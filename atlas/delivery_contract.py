"""User-approved report requirements. No arbitrary universal report length."""
import re
from .io import AtlasError,atomic_json,read_json,confined


def set_contract(project,spec):
    if project.status()['state'] not in ('INTAKE','MANDATE','ENABLEMENT','META','READINESS','ORCHESTRATE'):
        raise AtlasError('Set the report contract before substantive research; amendments need user approval')
    if not isinstance(spec,dict) or spec.get('schema_version')!=1:
        raise AtlasError('Report contract requires schema_version 1')
    sections=spec.get('required_sections')
    if not isinstance(sections,list) or any(not isinstance(x,str) or not x.strip() for x in sections) or len(set(sections))!=len(sections):
        raise AtlasError('required_sections must be a unique list of headings')
    words=spec.get('minimum_words',0)
    if type(words) is not int or not 0<=words<=100000:raise AtlasError('minimum_words must be a realistic nonnegative integer')
    if spec.get('approval') not in ('user_approved','user_specified'):
        raise AtlasError('Record actual user agreement to report scope; do not fabricate approval')
    atomic_json(project.path/'report_contract.json',spec)
    return {'contract':'report_contract.json','required_sections':len(sections),'minimum_words':words,
            'note':'Agreement is operator recorded; this tool does not authenticate the user.'}


def audit_contract(project,text):
    path=project.path/'report_contract.json'
    if not path.exists():return {'defined':False,'ok':True,'limitations':'No explicit minimum length/outline agreed; report quality requires substantive assessment'}
    spec=read_json(path);required=spec['required_sections']
    headings=[re.sub(r'^#+\s*','',x.strip()).casefold() for x in text.splitlines() if x.lstrip().startswith('#')]
    missing=[s for s in required if s.casefold() not in headings]
    words=len(re.findall(r'\b[\w-]+\b',text))
    return {'defined':True,'ok':not missing and words>=spec['minimum_words'],
            'missing_sections':missing,'word_count':words,'minimum_words':spec['minimum_words'],
            'limitations':'Passing format/length requirements does not establish factual correctness or appropriate analytical depth.'}
