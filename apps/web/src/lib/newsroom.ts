import fs from 'node:fs';

export interface NewsSource {id:string;label:string;url:string}
export type NewsSectionKind='facts'|'reviews'|'response'|'decision'|'analysis'|'lessons'|'limits';
export interface NewsSection {heading:string;kind:NewsSectionKind;paragraphs:string[];sources:string[]}
export const findingLabels={'documented-error':'可核对错误','record-conflict':'记录冲突','unsupported-inference':'推断缺口','standard-dispute':'标准争议','not-established':'尚不能定错'} as const;
export const targetLabels={ac:'AC',reviewer:'审稿人',authors:'作者',process:'评审过程'} as const;
export interface NewsFinding {level:keyof typeof findingLabels;target:keyof typeof targetLabels;summary:string;rationale:string;source_ids:string[]}
export const auditLabels={claim:'争议原句',evidence:'原文证据',alternative:'合理解释',verdict:'技术判定',impact:'决定影响'} as const;
export interface NewsAudit {reviewed_at:string;claim:string;evidence:string;alternative:string;verdict:string;impact:string;scope:string;source_ids:string[]}
export const deskLabels={'serious-errors':'严重矛盾和错误','low-accepted':'低分录取','high-rejected':'高分被拒绝'} as const;
export const contributionLabels={method:'方法模块',data:'数据引入',process:'流程创新',theory:'理论贡献',empirical:'实证发现'} as const;
export const assessmentLabels={accurate:'该意见有依据','partly-accurate':'部分有依据','contradicted':'存在明确反证',unverifiable:'尚不能核实','value-judgment':'属于评价标准'} as const;
export interface ClaimCheck {claim:string;assessment:keyof typeof assessmentLabels;analysis:string;source_ids:string[]}
export interface ReviewerCheck extends ClaimCheck {note_id:string;label:string;score:number|null;included:boolean;author_reply:string}
export interface PaperBrief {gap:string;method:string;results:string;result_scope:string;source_ids:string[];contribution:{kind:keyof typeof contributionLabels;module:string;why:string;evidence:string;caveat:string}}
export interface ArticleChecks {reviewers:ReviewerCheck[];ac:ClaimCheck;authors:ClaimCheck & {data_verdict:string};takeaway:string}
export interface NewsArticle {
  slug:string;forum_id:string;title:string;headline:string;deck:string;topic:string;
  category:'low-accepted'|'high-rejected'|'accepted'|'rejected';decision:string;ratings:number[];mean:number;
  archive_date:string;read_minutes:number;sections:NewsSection[];sources:NewsSource[];
  review_state:'draft_private'|'commentary_public';score_note?:string;finding?:NewsFinding;
  publication?:{basis:'owner_requested_publication';human_reviewed:false;date:string};
  audit?:NewsAudit;
  desk?:keyof typeof deskLabels;desk_reason?:string;brief?:PaperBrief;checks?:ArticleChecks;
  format?:'reader-first';selection_status?:'current'|'historical';
  serious_basis?:{core_claim:string;consequence:string;source_ids:string[]};
}
export const sectionLabels:Record<NewsSectionKind,string>={facts:'公开事实',reviews:'评审意见',response:'作者主张',decision:'公开决定',analysis:'AI 分析',lessons:'AI 写作建议',limits:'分析限制'};
export const categoryLabels={'low-accepted':'低分录取','high-rejected':'高分拒稿',accepted:'录取',rejected:'拒绝'} as const;

function requireText(value:unknown,name:string):asserts value is string {
  if(typeof value!=='string'||!value.trim()) throw new Error(`Newsroom ${name} must be non-empty text`);
}
export function validateNewsroom(value:unknown,mode:'preview'|'public'='preview'):NewsArticle[]{
  if(!Array.isArray(value)) throw new Error('Newsroom must contain an article array');
  const slugs=new Set<string>();
  for(const item of value){
    if(!item||typeof item!=='object') throw new Error('Newsroom article must be an object');
    if(item.score_note!==undefined) requireText(item.score_note,'score note');
    for(const key of ['slug','forum_id','title','headline','deck','topic','decision','archive_date']) requireText(item[key],key);
    if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.slug)) throw new Error('Newsroom slug must be a safe route');
    if(slugs.has(item.slug)) throw new Error(`Newsroom duplicate slug: ${item.slug}`);
    slugs.add(item.slug);
    if(!Object.hasOwn(categoryLabels,item.category)) throw new Error('Newsroom category is invalid');
    if(item.format!==undefined&&item.format!=='reader-first')throw new Error('Newsroom article format is invalid');
    if(item.selection_status!==undefined&&!['current','historical'].includes(item.selection_status))throw new Error('Newsroom selection status is invalid');
    const expectedState=mode==='public'?'commentary_public':'draft_private';
    if(item.review_state!==expectedState) throw new Error(`Newsroom ${mode} requires ${expectedState} state`);
    if(mode==='public'&&(item.publication?.basis!=='owner_requested_publication'||item.publication?.human_reviewed!==false||!/^\d{4}-\d{2}-\d{2}$/.test(item.publication?.date||''))) throw new Error('Newsroom public commentary requires honest publication metadata');
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
    if(!Array.isArray(item.sections)||(!item.sections.length&&item.format!=='reader-first')) throw new Error('Newsroom sections are required');
    for(const section of item.sections){
      requireText(section.heading,'section heading');
      if(!Object.hasOwn(sectionLabels,section.kind)) throw new Error('Newsroom section kind is invalid');
      if(!Array.isArray(section.paragraphs)||!section.paragraphs.length) throw new Error('Newsroom section paragraphs are required');
      section.paragraphs.forEach((paragraph:unknown)=>requireText(paragraph,'paragraph'));
      if(!Array.isArray(section.sources)) throw new Error('Newsroom section sources must be an array');
      for(const id of section.sources) if(!sourceIds.has(id)) throw new Error(`Newsroom missing source: ${id}`);
    }
    if(mode==='public'){
      const finding=item.finding;
      if(!finding||!Object.hasOwn(findingLabels,finding.level)||!Object.hasOwn(targetLabels,finding.target)) throw new Error('Newsroom public finding classification is required');
      requireText(finding.summary,'finding summary');requireText(finding.rationale,'finding rationale');
      if(!Array.isArray(finding.source_ids)||!finding.source_ids.length||finding.source_ids.some((id:string)=>!sourceIds.has(id))) throw new Error('Newsroom finding source must exist');
      if(item.format!=='reader-first'&&(item.sections.length!==7||new Set(item.sections.map((s:NewsSection)=>s.kind)).size!==7)) throw new Error('Newsroom public sections must include all seven evidence and limitation roles');
      const audit=item.audit;
      if(!audit||!/^\d{4}-\d{2}-\d{2}$/.test(audit.reviewed_at)) throw new Error('Newsroom public audit and date are required');
      for(const key of [...Object.keys(auditLabels),'scope']) requireText(audit[key],`audit ${key}`);
      if(!Array.isArray(audit.source_ids)||!audit.source_ids.length||audit.source_ids.some((id:string)=>!sourceIds.has(id))) throw new Error('Newsroom audit source must exist');
      if(!Object.hasOwn(deskLabels,item.desk)) throw new Error('Newsroom editorial desk is required');
      requireText(item.desk_reason,'desk reason');
      if(item.desk==='serious-errors'&&!['documented-error','record-conflict'].includes(finding.level)) throw new Error('Newsroom serious desk requires a concrete finding');
      if(item.desk!=='serious-errors'&&item.desk!==item.category) throw new Error('Newsroom desk must agree with decision category');
      const cite=(ids:unknown,name:string)=>{if(!Array.isArray(ids)||!ids.length||ids.some((id:string)=>!sourceIds.has(id)))throw new Error(`Newsroom ${name} source must exist`);};
      if(item.desk==='serious-errors'){
        requireText(item.serious_basis?.core_claim,'serious basis core claim');
        requireText(item.serious_basis?.consequence,'serious basis consequence');
        cite(item.serious_basis.source_ids,'serious basis');
      }
      if(item.selection_status!=='historical'){
        if(item.ratings.length<3)throw new Error('Newsroom current threshold requires at least three reviews');
        if(item.desk==='low-accepted'&&(!/^Accept/.test(item.decision)||mean>4))throw new Error('Newsroom low accepted threshold requires mean <= 4');
        if(item.desk==='high-rejected'&&(item.decision!=='Reject'||mean<7))throw new Error('Newsroom high rejected threshold requires mean >= 7');
      }
      const brief=item.brief;
      for(const key of ['gap','method','results','result_scope']) requireText(brief?.[key],`brief ${key}`);
      cite(brief.source_ids,'brief');
      if(!Object.hasOwn(contributionLabels,brief.contribution?.kind))throw new Error('Newsroom one primary contribution is required');
      for(const key of ['module','why','evidence','caveat'])requireText(brief.contribution[key],`contribution ${key}`);
      const checks=item.checks;
      if(!Array.isArray(checks?.reviewers)||!checks.reviewers.length)throw new Error('Newsroom reviewer checks are required');
      const checkedScores=checks.reviewers.filter((r:ReviewerCheck)=>r.included).map((r:ReviewerCheck)=>r.score);
      if(JSON.stringify(checkedScores)!==JSON.stringify(item.ratings))throw new Error('Newsroom reviewer scores must match score display in order');
      const noteIds=new Set<string>();
      for(const reviewer of checks.reviewers){
        for(const key of ['note_id','label','author_reply'])requireText(reviewer[key],`reviewer ${key}`);
        if(noteIds.has(reviewer.note_id))throw new Error('Newsroom duplicate reviewer note');
        noteIds.add(reviewer.note_id);
        if(typeof reviewer.included!=='boolean')throw new Error('Newsroom reviewer inclusion must be explicit');
      }
      for(const check of [...checks.reviewers,checks.ac,checks.authors]){
        requireText(check?.claim,'check claim');requireText(check?.analysis,'check analysis');
        if(!Object.hasOwn(assessmentLabels,check.assessment))throw new Error('Newsroom check assessment is invalid');
        cite(check.source_ids,'check');
      }
      requireText(checks.authors.data_verdict,'author data verdict');requireText(checks.takeaway,'takeaway');
    }
  }
  return value as NewsArticle[];
}

// Private editorial input is opt-in. This guard must run before any filesystem access.
export function loadNewsroom(env:NodeJS.ProcessEnv=process.env):NewsArticle[]{
  if(env.NEWSROOM_PUBLIC==='1'){
    if(env.NEWSROOM_PREVIEW==='1') throw new Error('Choose one newsroom mode');
    if(!env.NEWSROOM_PUBLIC_FILE) throw new Error('Newsroom requires an explicit public source file');
    return validateNewsroom(JSON.parse(fs.readFileSync(env.NEWSROOM_PUBLIC_FILE,'utf8')),'public');
  }
  if(env.NEWSROOM_PREVIEW!=='1'||!env.NEWSROOM_FILE) return [];
  return validateNewsroom(JSON.parse(fs.readFileSync(env.NEWSROOM_FILE,'utf8')));
}
