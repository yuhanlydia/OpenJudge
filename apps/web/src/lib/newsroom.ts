import fs from 'node:fs';

export interface NewsSource {id:string;label:string;url:string}
export type NewsSectionKind='facts'|'reviews'|'response'|'decision'|'analysis'|'lessons'|'limits';
export interface NewsSection {heading:string;kind:NewsSectionKind;paragraphs:string[];sources:string[]}
export interface NewsArticle {
  slug:string;forum_id:string;title:string;headline:string;deck:string;topic:string;
  category:'low-accepted'|'high-rejected';decision:string;ratings:number[];mean:number;
  archive_date:string;read_minutes:number;sections:NewsSection[];sources:NewsSource[];
  review_state:'draft_private';score_note?:string;
}
export const sectionLabels:Record<NewsSectionKind,string>={facts:'公开事实',reviews:'评审意见',response:'作者主张',decision:'公开决定',analysis:'AI 分析',lessons:'AI 写作建议',limits:'分析限制'};
export const categoryLabels={'low-accepted':'低分录取','high-rejected':'高分拒稿'} as const;

function requireText(value:unknown,name:string):asserts value is string {
  if(typeof value!=='string'||!value.trim()) throw new Error(`Newsroom ${name} must be non-empty text`);
}
export function validateNewsroom(value:unknown):NewsArticle[]{
  if(!Array.isArray(value)) throw new Error('Newsroom must contain an article array');
  const slugs=new Set<string>();
  for(const item of value){
    if(!item||typeof item!=='object') throw new Error('Newsroom article must be an object');
    if(item.score_note!==undefined) requireText(item.score_note,'score note');
    for(const key of ['slug','forum_id','title','headline','deck','topic','decision','archive_date']) requireText(item[key],key);
    if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.slug)) throw new Error('Newsroom slug must be a safe route');
    if(slugs.has(item.slug)) throw new Error(`Newsroom duplicate slug: ${item.slug}`);
    slugs.add(item.slug);
    if(!['low-accepted','high-rejected'].includes(item.category)) throw new Error('Newsroom category is invalid');
    if(item.review_state!=='draft_private') throw new Error('Newsroom preview requires draft_private state');
    if(!/^\d{4}-\d{2}-\d{2}$/.test(item.archive_date)||!Number.isInteger(item.read_minutes)||item.read_minutes<1) throw new Error('Newsroom date or reading duration is invalid');
    if(!Array.isArray(item.ratings)||!item.ratings.length||item.ratings.some((n:unknown)=>typeof n!=='number'||!Number.isFinite(n)||![0,2,4,6,8,10].includes(n))) throw new Error('Newsroom ratings must be one of 0, 2, 4, 6, 8, 10');
    const mean=item.ratings.reduce((sum:number,n:number)=>sum+n,0)/item.ratings.length;
    if(typeof item.mean!=='number'||!Number.isFinite(item.mean)||Math.abs(item.mean-mean)>1e-9) throw new Error('Newsroom mean does not agree with reviewer scores');
    if(!Array.isArray(item.sources)||!item.sources.length) throw new Error('Newsroom source list is required');
    const sourceIds=new Set<string>();
    for(const source of item.sources){
      requireText(source.id,'source id');requireText(source.label,'source label');requireText(source.url,'source URL');
      if(sourceIds.has(source.id)) throw new Error(`Newsroom duplicate source: ${source.id}`);
      sourceIds.add(source.id);
      let url:URL;try{url=new URL(source.url);}catch{throw new Error('Newsroom source URL must use HTTPS');}
      if(url.protocol!=='https:'||url.username||url.password) throw new Error('Newsroom source URL must use HTTPS without credentials');
    }
    if(!Array.isArray(item.sections)||!item.sections.length) throw new Error('Newsroom sections are required');
    for(const section of item.sections){
      requireText(section.heading,'section heading');
      if(!Object.hasOwn(sectionLabels,section.kind)) throw new Error('Newsroom section kind is invalid');
      if(!Array.isArray(section.paragraphs)||!section.paragraphs.length) throw new Error('Newsroom section paragraphs are required');
      section.paragraphs.forEach((paragraph:unknown)=>requireText(paragraph,'paragraph'));
      if(!Array.isArray(section.sources)) throw new Error('Newsroom section sources must be an array');
      for(const id of section.sources) if(!sourceIds.has(id)) throw new Error(`Newsroom missing source: ${id}`);
    }
  }
  return value as NewsArticle[];
}

// Private editorial input is opt-in. This guard must run before any filesystem access.
export function loadNewsroom(env:NodeJS.ProcessEnv=process.env):NewsArticle[]{
  if(env.NEWSROOM_PREVIEW!=='1'||!env.NEWSROOM_FILE) return [];
  return validateNewsroom(JSON.parse(fs.readFileSync(env.NEWSROOM_FILE,'utf8')));
}
