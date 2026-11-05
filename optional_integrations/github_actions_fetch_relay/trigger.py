"""Manual GitHub API dispatch of owner-approved workflow; not invoked by ATLAS automatically.

GitHub's standard workflow_dispatch needs an enabled workflow on the default
branch. A 204 means accepted for processing, NOT that the research fetch worked.
"""
import argparse
import json
import os
import re
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit


def dispatch(owner,repo,urls,ref,token,authorized=False,domains=()):
    if not authorized or os.environ.get('ATLAS_RELAY_OWNER_AUTHORIZED')!='true':
        raise ValueError('Explicit relay owner and environment approval required')
    if not token or not token.strip():raise ValueError('Supply scoped GitHub API token through environment')
    if not re.fullmatch('[A-Za-z0-9_.-]{1,100}',owner) or not re.fullmatch('[A-Za-z0-9_.-]{1,100}',repo):
        raise ValueError('Invalid repository identifier')
    if not re.fullmatch('[A-Za-z0-9_./-]{1,120}',ref) or '..' in ref:raise ValueError('Invalid Git ref')
    if not isinstance(urls,list) or not 1<=len(urls)<=5:raise ValueError('Use 1..5 URLs')
    allowed=set(domains)
    for url in urls:
        parts=urlsplit(url)
        if parts.scheme!='https' or not parts.hostname or parts.hostname.lower() not in allowed or parts.username or parts.password:
            raise ValueError('Requested URL is not an explicitly approved public HTTPS host')
    data=json.dumps({'ref':ref,'inputs':{'urls_json':json.dumps(urls)}}).encode()
    endpoint=f'https://api.github.com/repos/{owner}/{repo}/actions/workflows/atlas-fetch.yml/dispatches'
    req=urllib.request.Request(endpoint,data=data,method='POST',headers={
        'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json',
        'X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json','User-Agent':'ATLAS-relay-dispatch/1.0'})
    with urllib.request.urlopen(req,timeout=12) as response:
        if response.status!=204:raise ValueError('Unexpected API dispatch status '+str(response.status))
    return {'accepted_for_dispatch':True,'workflow':'atlas-fetch.yml','ref':ref,
            'important':'This response does not establish that a workflow ran successfully. Inspect the actual run and encrypted artifact.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('owner');p.add_argument('repo');p.add_argument('--ref',default='main')
    p.add_argument('--urls-file',required=True,type=Path);p.add_argument('--allowlist',required=True,type=Path)
    p.add_argument('--owner-approved',action='store_true')
    args=p.parse_args()
    print(dispatch(args.owner,args.repo,json.loads(args.urls_file.read_text()),args.ref,
          os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN'),args.owner_approved,
          json.loads(args.allowlist.read_text())['domains']))
