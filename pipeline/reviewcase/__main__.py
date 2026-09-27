import argparse,json,sys
from pathlib import Path
from .capture import capture_corpus,dump
from .config import load_config
from .discover import discover_venue
from .fetch import RetryingClient
from .normalize import normalize_capture
from .rank import build_rankings
from .export import export_public
from .evidence import build_evidence_bundle
from .validate import validate_public
from .report import validate_report,approve_report

def read(path): return json.loads(Path(path).read_text())
def main():
    p=argparse.ArgumentParser(prog='python -m reviewcase'); sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('discover');q.add_argument('--venue',required=True);q.add_argument('--out',required=True)
    q=sub.add_parser('ingest');q.add_argument('--config',required=True);q.add_argument('--out',required=True);q.add_argument('--resume',action='store_true')
    q=sub.add_parser('normalize');q.add_argument('--capture',required=True);q.add_argument('--config',required=True);q.add_argument('--out',required=True)
    q=sub.add_parser('rank');q.add_argument('--input',required=True);q.add_argument('--out',required=True);q.add_argument('--min-reviews',type=int,default=3);q.add_argument('--candidate-n',type=int,default=50)
    q=sub.add_parser('bundle');q.add_argument('--forum',required=True);q.add_argument('--input',required=True);q.add_argument('--out',required=True)
    q=sub.add_parser('export');q.add_argument('--input',required=True);q.add_argument('--rankings',required=True);q.add_argument('--out',required=True);q.add_argument('--reports',default='content/reports');q.add_argument('--denylist',default='config/denylist.json')
    q=sub.add_parser('release');q.add_argument('--public',required=True);q.add_argument('--releases',required=True);q.add_argument('--release-id',required=True);q.add_argument('--metadata',required=True)
    q=sub.add_parser('redact');q.add_argument('--public',required=True);q.add_argument('--releases',required=True);q.add_argument('--denylist',required=True)
    q=sub.add_parser('validate-public');q.add_argument('--path',required=True);q.add_argument('--mode',choices=['fixture','production'],default='production')
    q=sub.add_parser('check-report');q.add_argument('--report',required=True);q.add_argument('--bundle',required=True)
    q=sub.add_parser('publish-report');q.add_argument('--report',required=True);q.add_argument('--bundle',required=True);q.add_argument('--approval-record',required=True);q.add_argument('--out',required=True)
    a=p.parse_args(); result=None
    if a.cmd=='discover':
        result=discover_venue(a.venue,RetryingClient()).__dict__;dump(Path(a.out)/'discovery.json',result)
    elif a.cmd=='ingest': result=capture_corpus(load_config(Path(a.config)),Path(a.out),a.resume)
    elif a.cmd=='normalize':
        c=read(Path(a.capture)/'capture.json');c['directory']=a.capture
        result=normalize_capture(c,load_config(Path(a.config)));dump(Path(a.out)/'corpus.json',result)
    elif a.cmd=='rank':
        result=build_rankings(read(Path(a.input)/'corpus.json'),a.min_reviews,a.candidate_n);dump(Path(a.out)/'rankings.json',result)
    elif a.cmd=='bundle':
        result=build_evidence_bundle(a.forum,read(Path(a.input)/'corpus.json'));dump(Path(a.out)/f"{result['bundle_id']}.json",result)
    elif a.cmd=='export': result=export_public(read(Path(a.input)/'corpus.json'),read(Path(a.rankings)/'rankings.json'),Path(a.out),reports_dir=Path(a.reports),denylist_path=Path(a.denylist))
    elif a.cmd=='release':
        from .release import release_snapshot
        result=release_snapshot(a.public,a.releases,a.release_id,read(a.metadata))
    elif a.cmd=='redact':
        from .release import redact_all
        denylist=read(a.denylist)
        redact_all(a.public,a.releases,set(denylist['forum_ids']));result={'redacted_count':len(denylist['forum_ids'])}
    elif a.cmd=='validate-public': result=validate_public(Path(a.path),a.mode)
    elif a.cmd=='check-report': result=validate_report(read(a.report),read(a.bundle))
    elif a.cmd=='publish-report':
        from .publish_guard import can_publish
        report=read(a.report);bundle=read(a.bundle);approval=read(a.approval_record)
        checked=validate_report(report,bundle)
        if not checked['ok']: result=checked
        else:
            approved=approve_report(report,approval.get('actor'),approval)
            result=can_publish(approved,bundle)
            if result['ok']:
                from .export import _denylist
                if approved['forum_id'] in _denylist(None): raise ValueError('forum_redacted')
                dump(Path(a.out)/approved['forum_id']/f"{approved['report_id']}.json",approved)
    print(json.dumps({'ok':result.get('ok'),'errors':result.get('errors',[])} if isinstance(result,dict) and 'ok' in result else {'status':'completed','capture_complete':result.get('capture_complete') if isinstance(result,dict) else None,'count':result.get('success_count') if isinstance(result,dict) else None},ensure_ascii=False))
    if isinstance(result,dict) and (result.get('ok') is False or result.get('capture_complete') is False): sys.exit(1)
if __name__=='__main__': main()
