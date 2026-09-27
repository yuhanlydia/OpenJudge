import json, time, random, urllib.parse, urllib.request, urllib.error
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

HOST='https://api2.openreview.net'
class FetchError(RuntimeError): pass
class RetryingClient:
    def __init__(self, transport=None, delay=1, sleep=time.sleep):
        self.transport=transport or self._transport; self.delay=delay; self.sleep=sleep; self.last=0
    def _transport(self,path):
        url=HOST+path
        request=urllib.request.Request(url,headers={'User-Agent':'ReviewCase/0.1 public research read-only'})
        class SafeRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,req,fp,code,msg,headers,newurl):
                parsed=urllib.parse.urlparse(newurl)
                if parsed.scheme!='https' or parsed.hostname!='api2.openreview.net': raise FetchError('redirect_host_forbidden')
                return super().redirect_request(req,fp,code,msg,headers,newurl)
        opener=urllib.request.build_opener(SafeRedirect)
        with opener.open(request,timeout=30) as response:
            if urllib.parse.urlparse(response.geturl()).hostname != 'api2.openreview.net': raise FetchError('redirect_host_forbidden')
            return json.load(response)
    def request(self,path):
        if not path.startswith('/') or '://' in path: raise FetchError('invalid_path')
        for attempt in range(5):
            remaining=self.delay-(time.monotonic()-self.last)
            if remaining>0: self.sleep(remaining)
            self.last=time.monotonic()
            try: return self.transport(path)
            except urllib.error.HTTPError as e:
                if e.code in (401,403): raise FetchError(f'permission_{e.code}') from e
                if e.code not in (429,500,502,503,504) or attempt==4: raise FetchError(f'http_{e.code}') from e
                retry=e.headers.get('Retry-After')
                try: wait=float(retry)
                except (ValueError,TypeError):
                    try: wait=max(0,(parsedate_to_datetime(retry)-datetime.now(timezone.utc)).total_seconds())
                    except (ValueError,TypeError): wait=min(60,2**attempt+random.random())
                self.sleep(min(60,wait))
            except (TimeoutError,urllib.error.URLError) as e:
                if attempt==4: raise FetchError('network_failure') from e
                self.sleep(min(60,2**attempt+random.random()))
    def get_group(self,id): return self.request('/groups?'+urllib.parse.urlencode({'id':id}))['groups'][0]
    def get_invitation(self,id): return self.request('/invitations?'+urllib.parse.urlencode({'id':id}))['invitations'][0]
    def get_notes(self,**params): return self.request('/notes?'+urllib.parse.urlencode(params))

def fetch_forum(forum_id,client):
    if not forum_id or '/' in forum_id: raise ValueError('invalid forum id')
    offset=0; notes=[]; seen=set()
    while True:
        response=client.get_notes(forum=forum_id,limit=1000,offset=offset,details='replies')
        page=response['notes']
        for note in page:
            if note['id'] not in seen: notes.append(note); seen.add(note['id'])
            queue=list(note.get('details',{}).get('replies',[]))
            while queue:
                child=queue.pop(0)
                if child['id'] not in seen: notes.append(child); seen.add(child['id'])
                queue.extend(child.get('details',{}).get('replies',[]))
        if len(page)<1000:
            if response.get('count') is not None and offset+len(page)!=response['count']: raise FetchError('forum_page_count_mismatch')
            break
        offset+=len(page)
    return notes
