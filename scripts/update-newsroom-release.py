"""Refresh only the release manifest from already integrated editorial records."""
import collections
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'data/newsroom'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
articles=json.loads((ROOT/'articles.json').read_text())
release=json.loads((ROOT/'release.json').read_text())
old={row['forum_id']:row for row in release['cases']}
cases=[]
for article in articles:
    forum=article['forum_id'];path=ROOT/'evidence'/f'{forum}.json'
    data=json.loads(path.read_text())
    cases.append({'forum_id':forum,'sha256':digest(path),'notes':len(data['notes']),
      'excluded_rating_note_ids':old.get(forum,{}).get('excluded_rating_note_ids',[])})
release.update(edition='ICLR2026-strict-full-corpus-v4',articles_sha256=digest(ROOT/'articles.json'),
  coverage_sha256=digest(ROOT/'coverage.json'),cases=cases,public_note_count=sum(c['notes'] for c in cases))
release['authorization']['scope']='Owner requested 100+ strict cases across three exclusive desks, detailed reviewer/AC/author checks and public Site updates; continued 2026-09-28.'
release['review_audit']['case_count']=len(articles)
release['review_audit']['additional_manuscript_access']=[{'forum_id':a['forum_id'],
 'urls':[s['url'] for s in a['sources'] if any(x in s['url'] for x in ('arxiv.org','proceedings.','attachment/','openaccess.thecvf.com'))],
 'scope':a['brief']['result_scope']} for a in articles]
current=[a for a in articles if a.get('selection_status')!='historical']
release['selection_policy']={'low_accepted_max_mean':4,'high_rejected_min_mean':7,'min_valid_reviews':3,
 'serious_requires_material_consequence':True,'target_not_quota':100,
 'current_case_count':len(current),'historical_case_count':len(articles)-len(current)}
release['reader_structure'].update(desks=dict(collections.Counter(a['desk'] for a in current)),
 official_review_notes=sum(len(a['checks']['reviewers']) for a in articles),
 included_ratings=sum(len(a['ratings']) for a in articles),source_snapshot_changed=False)
(ROOT/'release.json').write_text(json.dumps(release,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'articles':len(articles),'current':len(current),'public_notes':release['public_note_count']}))
