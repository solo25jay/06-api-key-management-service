import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('linkswift',Path(__file__).parents[1]/'app.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def test_url_validation():
 assert m.valid_url('https://example.com/path')
 assert m.valid_url('http://example.com')
 assert not m.valid_url('javascript:alert(1)')
 assert not m.valid_url('example.com')
def test_hash_is_not_plaintext():
 assert m.key_hash('lks_secret') != 'lks_secret'
 assert len(m.key_hash('lks_secret')) == 64
def test_health():
 r=m.app.test_client().get('/health')
 assert r.status_code == 200 and r.json['status'] == 'ok'
