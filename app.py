import os, re, secrets, hashlib, base64
from urllib.parse import urlparse
from datetime import datetime, timezone
from flask import Flask, request, redirect, render_template, session, flash, jsonify
from supabase import create_client
from cryptography.fernet import Fernet, InvalidToken

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-only-change-before-deploy')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
BASE_URL = os.environ.get('BASE_URL', '').rstrip('/')
supabase = None
if os.environ.get('SUPABASE_URL') and os.environ.get('SUPABASE_SERVICE_ROLE_KEY'):
    supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])

def db():
    if supabase is None: raise RuntimeError('Configure Supabase environment variables.')
    return supabase

def key_hash(key): return hashlib.sha256(key.encode()).hexdigest()
def key_cipher():
    # Derive a stable encryption key from the server-only Flask secret.
    secret = os.environ.get('FLASK_SECRET_KEY', 'dev-only-change-before-deploy').encode()
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret).digest()))
def valid_url(url):
    try:
        p = urlparse(url.strip())
        return p.scheme in ('http', 'https') and bool(p.netloc) and len(url) <= 2048
    except Exception: return False

def key_expired(row, now=None):
    value = row.get('expires_at')
    if not value: return False
    try:
        expires = datetime.fromisoformat(value.replace('Z', '+00:00')) if isinstance(value, str) else value
        if expires.tzinfo is None: expires = expires.replace(tzinfo=timezone.utc)
        return expires <= (now or datetime.now(timezone.utc))
    except (TypeError, ValueError):
        # Fail closed if an expiry value is malformed.
        return True

def active_key(raw):
    if not raw: return None
    rows = db().table('api_keys').select('*').eq('key_hash', key_hash(raw)).eq('revoked', False).execute().data
    if not rows or key_expired(rows[0]): return None
    return rows[0]

def create_link(url, key):
    for attempt in range(5):
        code = secrets.token_urlsafe(6).replace('-', '').replace('_', '')[:7]
        try:
            rows = db().table('short_urls').insert({'code':code,'original_url':url,'api_key_id':key['id']}).execute().data
            if rows: return rows[0]
        except Exception:
            if attempt == 4: raise
    raise RuntimeError('Unable to allocate short code')

@app.get('/')
def home(): return render_template('index.html', short_url=None)

@app.post('/request-key')
def request_key():
    name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); reason=request.form.get('reason','').strip()
    if not name or '@' not in email:
        flash('Enter your name and a valid email address.', 'error'); return redirect('/')
    try:
        # Issue the key immediately. Admin can monitor, set an expiry, or revoke it later.
        raw='lks_'+secrets.token_urlsafe(32)
        encrypted=key_cipher().encrypt(raw.encode()).decode()
        req=db().table('api_key_requests').insert({'name':name[:100],'email':email[:254],'reason':reason[:500],'status':'issued','key_encrypted':encrypted,'key_delivered':False}).execute().data
        if not req: raise RuntimeError('Request record was not saved')
        key_rows=db().table('api_keys').insert({'label':name[:100],'owner_email':email[:254],'key_hash':key_hash(raw),'key_prefix':raw[:12],'revoked':False}).execute().data
        if not key_rows: raise RuntimeError('API key was not saved')
        db().table('api_key_requests').update({'api_key_id':key_rows[0]['id']}).eq('id',req[0]['id']).execute()
        session['request_id']=req[0]['id']
        flash('Your API key has been generated and is ready to use.', 'success')
    except Exception:
        app.logger.exception('Key issuance failed'); flash('Could not issue your API key. Try again later.', 'error')
    return redirect('/')

@app.get('/request-status')
def request_status():
    request_id=session.get('request_id')
    if not request_id: return jsonify({'status':'none'})
    try:
        rows=db().table('api_key_requests').select('*').eq('id',request_id).limit(1).execute().data or []
        if not rows: return jsonify({'status':'none'})
        req=rows[0]
        if req.get('status') == 'issued' and req.get('key_encrypted'):
            try:
                raw=key_cipher().decrypt(req['key_encrypted'].encode()).decode()
                # Keep the encrypted copy until the user acknowledges they have seen it.
                return jsonify({'status':'issued','api_key':raw})
            except (InvalidToken, ValueError):
                app.logger.exception('Could not decrypt issued API key')
                return jsonify({'status':'issued','api_key':None,'message':'Your key was issued but could not be displayed. Contact the administrator.'}), 500
        return jsonify({'status':req.get('status','pending')})
    except Exception:
        app.logger.exception('Request status lookup failed'); return jsonify({'error':'Unable to check request status'}), 500

@app.post('/request-key/acknowledge')
def acknowledge_key():
    request_id=session.get('request_id')
    if not request_id: return jsonify({'ok':False}), 400
    try:
        db().table('api_key_requests').update({'key_encrypted':None,'key_delivered':True}).eq('id',request_id).execute()
        session.pop('request_id',None)
        return jsonify({'ok':True})
    except Exception:
        app.logger.exception('Could not acknowledge key delivery'); return jsonify({'ok':False}), 500

@app.post('/shorten')
def shorten_form():
    raw=request.form.get('api_key','').strip(); url=request.form.get('url','').strip()
    if not valid_url(url): flash('Enter a complete http:// or https:// URL.', 'error'); return redirect('/')
    try:
        key=active_key(raw)
        if not key: flash('API key is invalid, revoked, or expired.', 'error'); return redirect('/')
        row=create_link(url,key); short=(BASE_URL or request.url_root.rstrip('/'))+'/'+row['code']
        return render_template('index.html', short_url=short)
    except Exception:
        app.logger.exception('Shortening failed'); flash('Could not create link. Check server configuration.', 'error'); return redirect('/')

@app.post('/api/shorten')
def api_shorten():
    key=active_key(request.headers.get('X-API-Key','').strip()); payload=request.get_json(silent=True) or {}; url=str(payload.get('url','')).strip()
    if not key: return jsonify({'error':'Invalid, revoked, or expired API key'}), 401
    if not valid_url(url): return jsonify({'error':'Provide a valid http or https URL'}), 400
    try:
        row=create_link(url,key)
        return jsonify({'short_url':(BASE_URL or request.url_root.rstrip('/'))+'/'+row['code'],'code':row['code'],'original_url':url}), 201
    except Exception:
        app.logger.exception('API error'); return jsonify({'error':'Unable to create short URL'}), 500

@app.get('/<code>')
def follow(code):
    if not re.fullmatch(r'[A-Za-z0-9]{4,12}',code): return render_template('not_found.html'),404
    try:
        rows=db().table('short_urls').select('id,original_url,clicks').eq('code',code).limit(1).execute().data
        if not rows: return render_template('not_found.html'),404
        db().table('short_urls').update({'clicks':int(rows[0].get('clicks') or 0)+1}).eq('id',rows[0]['id']).execute()
        return redirect(rows[0]['original_url'], code=302)
    except Exception:
        app.logger.exception('Redirect failed'); return render_template('not_found.html'),500

@app.get('/admin')
def admin():
    if not session.get('admin'): return render_template('admin_login.html')
    try:
        reqs=db().table('api_key_requests').select('*').order('created_at',desc=True).execute().data or []
        keys=db().table('api_keys').select('*').order('created_at',desc=True).execute().data or []
        for key in keys:
            key['expired'] = key_expired(key)
            key['expires_on'] = key.get('expires_at', '')[:10] if key.get('expires_at') else ''
            key['display_status'] = 'revoked' if key.get('revoked') else ('expired' if key['expired'] else 'active')
        urls=db().table('short_urls').select('*').order('created_at',desc=True).limit(100).execute().data or []
        total_clicks=sum(int(u.get('clicks') or 0) for u in urls)
        return render_template('admin.html',requests_data=reqs,keys_data=keys,urls_data=urls,total_clicks=total_clicks)
    except Exception:
        app.logger.exception('Admin load failed'); return render_template('admin_login.html',error='Supabase connection failed.'),503

@app.post('/admin/login')
def login():
    if not ADMIN_PASSWORD: return render_template('admin_login.html',error='Set ADMIN_PASSWORD in environment.'),503
    if secrets.compare_digest(request.form.get('password',''),ADMIN_PASSWORD): session['admin']=True; return redirect('/admin')
    return render_template('admin_login.html',error='Incorrect password.'),401

@app.post('/admin/logout')
def logout(): session.clear(); return redirect('/admin')
def admin_only(): return bool(session.get('admin'))

@app.post('/admin/keys/<int:kid>/expiry')
def set_expiry(kid):
    if not admin_only(): return redirect('/admin')
    value='' if request.form.get('clear_expiry') else request.form.get('expires_on','').strip()
    try:
        if value:
            # Date-only expiry remains valid through the selected day (UTC).
            selected=datetime.strptime(value, '%Y-%m-%d').replace(hour=23,minute=59,second=59,microsecond=999999,tzinfo=timezone.utc)
            expiry=selected.isoformat()
        else:
            expiry=None
        result=db().table('api_keys').update({'expires_at':expiry}).eq('id',kid).execute()
        if not result.data:
            flash('API key not found.','error')
        else:
            flash('Expiry date updated.' if expiry else 'Expiry date removed. Key has no scheduled expiry.','success')
    except ValueError:
        flash('Choose a valid expiry date.','error')
    except Exception:
        app.logger.exception('Could not update key expiry'); flash('Could not update expiry date.','error')
    return redirect('/admin')

@app.post('/admin/keys/<int:kid>/revoke')
def revoke(kid):
    if not admin_only(): return redirect('/admin')
    try:
        db().table('api_keys').update({'revoked':True,'revoked_at':datetime.now(timezone.utc).isoformat()}).eq('id',kid).execute(); flash('Key revoked. It cannot create new links.','success')
    except Exception: flash('Could not revoke key.','error')
    return redirect('/admin')

@app.get('/health')
def health(): return jsonify({'status':'ok'})
if __name__ == '__main__': app.run(port=int(os.environ.get('PORT','5000')),debug=os.environ.get('FLASK_DEBUG')=='1')
