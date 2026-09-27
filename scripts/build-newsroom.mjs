import {execFileSync} from 'node:child_process';import path from 'node:path';import fs from 'node:fs';
const root=path.resolve(import.meta.dirname,'..');
const out=process.env.OUT_DIR?path.resolve(root,process.env.OUT_DIR):path.join(root,'dist');
execFileSync(process.execPath,[path.join(root,'scripts/validate-newsroom.mjs')],{cwd:root,stdio:'inherit'});
execFileSync('pnpm',['--dir','apps/web','build'],{cwd:root,stdio:'inherit',env:{...process.env,NEWSROOM_PREVIEW:'0',NEWSROOM_PUBLIC:'1',NEWSROOM_PUBLIC_FILE:path.join(root,'data/newsroom/articles.json'),OUT_DIR:out,BASE_PATH:'/',SITE_URL:process.env.SITE_URL||'https://openjudge.longyunbo218.chatgpt.site'}});
// This edition publishes case commentary, not the separate unvalidated conference index.
for(const dir of ['iclr-2026','indexes','versions'])fs.rmSync(path.join(out,dir),{recursive:true,force:true});
execFileSync('python3',[path.join(root,'scripts/check-dist.py'),'--path',out],{cwd:root,stdio:'inherit'});
