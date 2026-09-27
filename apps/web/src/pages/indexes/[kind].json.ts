import type {APIRoute} from 'astro';
import {loadPublicSnapshot,ranked} from '../../lib/data';
export function getStaticPaths(){const s=loadPublicSnapshot();return [{params:{kind:'low-score-accepted'},props:{items:ranked(s,'low_score_accepted')}},{params:{kind:'high-score-rejected'},props:{items:ranked(s,'high_score_rejected')}}];}
export const GET:APIRoute=({props})=>new Response(JSON.stringify(props.items),{headers:{'Content-Type':'application/json'}});
