"""Read-only static output checks; production data gate is a separate required step."""
import argparse,gzip,json,re,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--path',default='apps/web/dist');a=p.parse_args();root=Path(a.path)
errors=[]
for file in root.rglob('*'):
    if not file.is_file():continue
    if file.suffix in ('.pdf','.py','.env','.zip') or any(part in ('.cache','node_modules','pipeline','.git') for part in file.relative_to(root).parts):errors.append(str(file)+': private artifact')
    if file.suffix in ('.html','.json','.js','.css'):
        text=file.read_text()
        if re.search(r'(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC )?PRIVATE KEY-----)',text):errors.append(str(file)+': secret pattern')
        if file.suffix=='.html' and re.search(r'<script[^>]+src=["\']https?://',text):errors.append(str(file)+': external script')
        if file.suffix=='.html' and re.search(r'<(?:iframe|object|embed)\b',text,re.I):errors.append(str(file)+': active embedded source')
external_js_gzip=sum(len(gzip.compress(f.read_bytes())) for f in root.rglob('*.js'))
inline_js_gzip=max((sum(len(gzip.compress(script.encode())) for script in re.findall(r'<script[^>]*>(.*?)</script>',f.read_text(),re.S)) for f in root.rglob('*.html')),default=0)
js_gzip=external_js_gzip+inline_js_gzip
if js_gzip>200*1024:errors.append('initial JS exceeds 200 KiB gzip budget')
indexes=list((root/'indexes').glob('*.json'));index_gzip=sum(len(gzip.compress(f.read_bytes())) for f in indexes)
if index_gzip>6*1024*1024:errors.append('indexes exceed 6 MiB gzip budget')
if not (root/'index.html').exists():errors.append('index.html missing')
print(json.dumps({'ok':not errors,'html_pages':len(list(root.rglob('*.html'))),'javascript_gzip_bytes':js_gzip,'index_gzip_bytes':index_gzip,'errors':errors},ensure_ascii=False))
sys.exit(bool(errors))
