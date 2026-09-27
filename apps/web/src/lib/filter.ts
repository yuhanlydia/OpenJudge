import type {CaseIndex,CaseFilter} from './types.ts';
export function filterCases(cases:CaseIndex[],filter:CaseFilter):CaseIndex[]{
 const q=(filter.q||'').normalize('NFKC').toLocaleLowerCase().trim();
 return cases.filter(p=>{
  const s=p.score_summary, mean=s?.mean===null||s?.mean===undefined?NaN:Number(s.mean);
  return (!q||[p.title,...(p.keywords||[])].join(' ').normalize('NFKC').toLocaleLowerCase().includes(q))&&
   (filter.minMean===undefined||(Number.isFinite(mean)&&mean>=filter.minMean))&&
   (filter.maxMean===undefined||(Number.isFinite(mean)&&mean<=filter.maxMean))&&
   (s?.valid_review_count??0)>=(filter.minReviews??0)&&
   (!filter.reportState||filter.reportState==='all'||(p.report_state||'not_generated')===filter.reportState);
 });
}
export function paginate<T>(items:T[],requested=1,pageSize=25){const pages=Math.max(1,Math.ceil(items.length/pageSize));const page=Math.max(1,Math.min(pages,Math.floor(Number.isFinite(requested)?requested:1)));return {items:items.slice((page-1)*pageSize,page*pageSize),page,pages,total:items.length};}
export function readFilter(params:URLSearchParams):CaseFilter{
 const number=(k:string)=>{const v=params.get(k);if(v===null||v.trim()==='')return undefined;const n=Number(v);return Number.isFinite(n)&&n>=0?n:undefined;};
 return {q:params.get('q')||'',minMean:number('minMean'),maxMean:number('maxMean'),minReviews:number('minReviews')??3,reportState:params.get('reportState')||'all',page:Math.max(1,Math.floor(number('page')??1))};
}
