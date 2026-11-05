"""Durable, operator-observed evidence capture. No unsupported source is certified by capture alone."""
import re
from pathlib import Path
from urllib.parse import urlsplit
from .io import AtlasError, now, atomic_json, atomic_text, read_json, file_hash, confined
from .project import Project


def capture_source(project,url,title,body,query,tool='manual',provisional=False,source_id=None,plan_id=None):
    state=project.status()
    if state['state'] not in ('RESEARCH','VERIFY'):
        raise AtlasError('Source capture requires RESEARCH or VERIFY stage; do not treat intake/meta probes as substantive research')
    if state.get('hold') and state['hold'].get('kind') in ('aborted',): raise AtlasError('Project aborted')
    if not all(isinstance(v,str) and v.strip() for v in (url,title,body,query,tool)):
        raise AtlasError('source-add needs a URL, title, actual text/snippet, query and retrieval tool')
    if len(body.encode('utf-8'))>9_000_000: raise AtlasError('Source text exceeds 9 MB')
    u=urlsplit(url)
    if u.scheme not in ('https','http') or not u.hostname or u.username or u.password:
        raise AtlasError('Sources need a public HTTP(S) URL without credentials')
    evidence=project.artifact('evidence.json')
    existing={r['id'] for r in evidence['sources']}
    if source_id is None:
        source_id=next(f'S{i:04d}' for i in range(1,100000) if f'S{i:04d}' not in existing)
    if not re.fullmatch('[A-Za-z0-9_-]{1,80}',source_id) or source_id in existing:
        raise AtlasError('Source ID unsafe or already in use')
    path='sources/'+source_id+'.txt'
    if (project.path/path).exists(): raise AtlasError('Source snapshot file already exists')
    atomic_text(project.path/path,body)
    row={'id':source_id,'source_type':'search_result' if provisional else 'web_snapshot',
         'url':url,'title':title,'origin_group':u.hostname.lower(),
         'accessed_at':now(),'snapshot':path,'sha256':file_hash(project.path/path),
         'provenance_note':'Operator-imported '+('search snippet, unverified full page' if provisional else 'source text; acquisition/identity not independently authenticated'),
         'provisional':bool(provisional),'retrieval_tool':tool}
    evidence['sources'].append(row);atomic_json(project.path/'evidence.json',evidence)
    logpath=project.path/'search_log.json'
    log=read_json(logpath) if logpath.exists() else {'queries':[]}
    if not isinstance(log,dict) or not isinstance(log.get('queries'),list): raise AtlasError('Malformed existing search log')
    qid=f'Q{len(log["queries"])+1:05d}'
    entry={'id':qid,'plan_id':plan_id or 'EXPLORATORY','query':query,'tool':tool,'at':now(),
           'status':'partial' if provisional else 'complete',
           'outcome':'Provisional snippet; full source unverified' if provisional else 'Operator-observed content (not independently authenticated)',
           'retrieved_ids':[source_id],'included_ids':[source_id],'exclusions':[]}
    log['queries'].append(entry);atomic_json(logpath,log)
    return {'source_id':source_id,'search_id':qid,'snapshot':path,'status':'provisional_not_verified' if provisional else 'captured_not_independently_verified',
            'next':'Add claim records with atlas claim-add; independent review still required for material claims'}


def capture_claim(project,text,source_ids,kind='factual',scope='',author='researcher',material=True,reported_statistic=False,numeric_value=None,units=None):
    state=project.status()
    if state['state'] not in ('RESEARCH','VERIFY'): raise AtlasError('Claim capture requires RESEARCH or VERIFY')
    evidence=project.artifact('evidence.json')
    known={s['id'] for s in evidence['sources']}
    if not source_ids or not set(source_ids)<=known: raise AtlasError('Claim requires known source IDs; add sources first')
    if kind not in ('factual','numeric','inference'): raise AtlasError('Invalid claim kind')
    if not text.strip() or not scope.strip() or not author.strip(): raise AtlasError('Claim text, scope and author required')
    if material and all(s.get('source_type')=='search_result' for s in evidence['sources'] if s['id'] in source_ids):
        # Keep claim but it cannot be audited as fully verified until full evidence exists.
        caveat='Only provisional snippets are linked; seek original documents before certification.'
    else:caveat='Evidence interpretation and independence have not yet been verified.'
    ids={c['id'] for c in evidence['claims']}
    cid=next(f'C{i:04d}' for i in range(1,100000) if f'C{i:04d}' not in ids)
    claim={'id':cid,'text':text,'kind':kind,'material':bool(material),'source_ids':source_ids,
           'author':author,'scope':scope,'uncertainty':{'level':'unknown','basis':'Not independently assessed', 'limitations':[caveat]}}
    if kind=='numeric':
        if numeric_value is None or not units: raise AtlasError('Numeric claim requires numeric value and units')
        claim.update(numeric_value=numeric_value,units=units,reported_statistic=bool(reported_statistic))
    evidence['claims'].append(claim); atomic_json(project.path/'evidence.json',evidence)
    return {'claim_id':cid,'status':'recorded_pending_review','source_ids':source_ids,'warning':caveat}


def capture_search(project,query,tool,outcome,plan_id='EXPLORATORY',status='partial',source_ids=None):
    if project.status()['state']!='RESEARCH':raise AtlasError('Search logging requires RESEARCH stage')
    if not query.strip() or not tool.strip() or not outcome.strip():raise AtlasError('Query, tool and outcome required')
    path=project.path/'search_log.json';data=read_json(path) if path.is_file() else {'queries':[]}
    ids={s['id'] for s in project.artifact('evidence.json')['sources']}
    sources=source_ids or []
    if not set(sources)<=ids:raise AtlasError('Search log source IDs must exist in evidence register')
    row={'id':f'Q{len(data["queries"])+1:05d}','query':query,'tool':tool,'outcome':outcome,'plan_id':plan_id,'at':now(),
         'status':status,'retrieved_ids':sources,'included_ids':sources,'exclusions':[]}
    data['queries'].append(row);atomic_json(path,data)
    return row
