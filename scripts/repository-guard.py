"""Catch accidentally tracked private material before commit/PR. Cannot undo prior exposure."""
import json,re,subprocess,sys
from pathlib import Path
PRIVATE={'private_drafts','.cache','.env','credentials','node_modules','__pycache__'}
def inspect_files(root,files):
    errors=[]
    for rel in files:
        path=Path(rel)
        if any(part in PRIVATE or part.startswith('.env') for part in path.parts):errors.append(f'{rel}: private path');continue
        p=Path(root)/path
        if not p.is_file():continue
        if p.suffix.lower() in ('.pdf','.pem','.key'):errors.append(f'{rel}: raw document or key requires separate private storage');continue
        if p.suffix.lower() not in ('.json','.yaml','.yml','.md','.txt','.js','.ts','.astro','.py','.mjs'):continue
        text=p.read_text(errors='replace')
        if re.search(r'(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC )?PRIVATE KEY-----)',text):errors.append(f'{rel}: potential secret')
        if p.suffix=='.json':
            try:data=json.loads(text)
            except ValueError:errors.append(f'{rel}: invalid JSON');continue
            if isinstance(data,dict):
                if data.get('is_fixture') is True and not any(k in path.parts for k in ('tests','fixtures')):errors.append(f'{rel}: fixture outside tests')
                if data.get('report_id') and data.get('editorial_state') not in ('approved','published') and data.get('is_fixture') is not True:errors.append(f'{rel}: private report draft')
                if any(key in data for key in ('authorids','api_key','access_token','private_draft','identity_mapping')):errors.append(f'{rel}: disallowed private field')
    return errors
if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    files=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
    errors=inspect_files(root,[f for f in files if f]);print(json.dumps({'ok':not errors,'errors':errors}));sys.exit(bool(errors))
