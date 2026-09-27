import fs from 'node:fs';
import path from 'node:path';
import type {PublicSnapshot,CaseIndex} from './types';
export const root=path.resolve(process.cwd(),'../..');
export const releaseRoot=path.resolve(process.env.REVIEWCASE_RELEASES_DIR||path.join(root,'data/releases'));
export const dataRoot=path.resolve(process.env.REVIEWCASE_DATA_DIR||path.join(root,'data/public'));
export function readJSON(file:string,fallback?:any){try{return JSON.parse(fs.readFileSync(file,'utf8'));}catch(e){if(fallback!==undefined)return fallback;throw e;}}
export function loadPublicSnapshot(directory=dataRoot):PublicSnapshot{
 const index=readJSON(path.join(directory,'index/iclr2026.json'));
 return {papers:Array.isArray(index)?index:index.papers||[],rankings:readJSON(path.join(directory,'rankings.json')),coverage:readJSON(path.join(directory,'coverage.json')),manifest:readJSON(path.join(directory,'manifest.json'))};
}
export function loadPaper(id:string,directory=dataRoot){return readJSON(path.join(directory,'papers',id+'.json'));}
export function ranked(snapshot:PublicSnapshot,key:'low_score_accepted'|'high_score_rejected'){const byId=new Map(snapshot.papers.map(p=>[p.forum_id,p]));return (snapshot.rankings[key]||[]).map(id=>byId.get(id)).filter(Boolean) as CaseIndex[];}
export function releases(){const index=readJSON(path.join(releaseRoot,'index.json'),{releases:[]});return (Array.isArray(index)?index:index.releases||[]).filter((r:any)=>r.release_id).map((r:any)=>({...r,...readJSON(path.join(releaseRoot,r.release_id,'release-manifest.json'),{})}));}
export function reportLabel(state:string='not_generated'){return ({not_generated:'尚未分析',approved:'已审核',published:'已发布',stale:'待复核'} as Record<string,string>)[state]||'尚未发布';}
export function fmt(value:unknown,digits=2){return value===null||value===undefined?'—':Number(value).toFixed(digits);}
export function date(value:any){if(!value)return '未记录';const d=new Date(value);return Number.isNaN(d.getTime())?'未记录':d.toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',hour12:false});}
