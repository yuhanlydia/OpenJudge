export interface ScoreSummary { scores: (number|string)[]; mean: number|string|null; median?: number|string|null; min?:number|string|null; max?:number|string|null; std_population?:number|string|null; valid_review_count: number; missing_rating_count?:number; scale_id?: string; score_stage?:string }
export interface CaseIndex {forum_id:string; title:string; keywords?:string[]; decision:string; source_url:string; score_summary:ScoreSummary; report_state?:string; issues?:string[]; track?:string|null; [key:string]:any}
export interface CaseFilter {q?:string; minMean?:number; maxMean?:number; minReviews?:number; reportState?:string; page?:number}
export interface PublicSnapshot {papers:CaseIndex[]; rankings:{low_score_accepted:string[];high_score_rejected:string[];[key:string]:any};coverage:Record<string,any>;manifest:Record<string,any>}
export type SanitizedMarkup=string;
