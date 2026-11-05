"""Researcher-facing ergonomic commands. Scaffolds are drafts, never accepted research evidence."""
from pathlib import Path
from .io import AtlasError, atomic_json, read_json, now
from .project import Project, STATES, ARTIFACTS
from .intake import questions
from .enablement import feature_inventory


def next_actions(project):
    state=project.status(); stage=state['state']; index=STATES.index(stage)
    following=STATES[index+1] if index+1<len(STATES) else None
    required=list(ARTIFACTS.get(following,[])) if following else []
    missing=[name for name in required if not (project.path/name).is_file()]
    problems=[]
    if state.get('hold'):
        problems.append({'field':'hold','message':f"{state['hold'].get('kind')}: {state['hold'].get('reason')}",'severity':'blocking'})
    if following=='MANDATE':
        questionset=questions(project.root,state['domain'],state['answers'],state['extra_questions'])
        for row in questionset:
            if row['essential'] and not row['answered']:
                problems.append({'field':'intake.'+row['key'],'message':'Unanswered essential question (or declare assumption)','severity':'blocking'})
    if following=='VERIFY':
        for task in state.get('tasks',[]):
            if task['status']!='done' and (task.get('critical',True) or task['status'] not in ('blocked','skipped') or not task.get('decision_impact')):
                problems.append({'field':'tasks.'+task['id'],'message':f"Task {task['id']} is {task['status']}; complete or record a justified noncritical gap",'severity':'blocking'})
        for key in ('coverage.json','search_log.json'):
            if not (project.path/key).is_file(): missing.append(key)
    if following=='SYNTHESIS':
        evidence=project.artifact('evidence.json')
        if not evidence.get('claims'):
            problems.append({'field':'evidence.claims','message':'No claims recorded; fully verified research cannot complete','severity':'blocking'})
    for name in missing:
        problems.append({'field':name,'message':'Required draft artifact missing; run atlas scaffold <slug> --stage '+following,'severity':'blocking'})
    # Attempt the actual gate read-only and expose any remaining contract error;
    # never mutate, seal or mark the stage advanced.
    if following and not missing and not state.get('hold'):
        try:
            with project.connection() as con:
                project._gate(following,project._state(con),con)
        except (AtlasError,OSError,KeyError,TypeError,ValueError) as exc:
            message=str(exc)
            if not any(row['message']==message for row in problems):
                problems.append({'field':following,'message':message,'severity':'blocking'})
    return {'current_stage':stage,'next_stage':following,'can_advance':not problems and bool(following),
            'issues':problems,'required_artifacts':required,
            'command':('atlas advance '+project.slug+' '+following) if following else None,
            'note':'Dry-run diagnostics; a successful check does not create artifacts or establish research truth.'}


def scaffold(project,stage=None):
    state=project.status(); index=STATES.index(state['state'])
    stage=stage or (STATES[index+1] if index+1<len(STATES) else 'COMPLETE')
    if stage not in STATES: raise AtlasError('Unknown scaffold stage: '+stage)
    if STATES.index(stage)>index+1: raise AtlasError('Scaffold only the current or immediate next stage')
    defaults={
        'ENABLEMENT':{'enablement.json':feature_inventory(state['question'])},
        'META':{'access_plan.json':{'schema_version':1,'question':state['question'],'coverage':['REPLACE_WITH_REAL_COVERAGE'],
                 'selection_reason':'DRAFT: choose minimum verified research capabilities','needs':[]}},
        'READINESS':{'dossier.json':{'methods_compared':[],'selection_reason':'DRAFT','risks':'DRAFT','limitations':'DRAFT','expertise':'DRAFT',
                                    'tool_comparison':'DRAFT','method_sources':[],'pilot':'DRAFT'},
                     'protocol.json':{'schema_version':2,'methods':[],'coverage':[],'search_plan':[],'evaluation_criteria':[],
                     'meta_iterations':1,'inclusion':'DRAFT','exclusion':'DRAFT','verification':'DRAFT','stopping_rule':'DRAFT',
                     'amendment_policy':'DRAFT'}},
        'ORCHESTRATE':{'readiness.json':{'decision':'DRAFT','checks':{},'capabilities':[],'limitations':'DRAFT'}},
        'RESEARCH':{'plan.json':{'architecture_reason':'DRAFT','model_policy':'DRAFT','tasks':[]}},
        'VERIFY':{'coverage.json':{'items':[],'stopping_decision':'DRAFT'},'search_log.json':{'queries':[]}},
        'SYNTHESIS':{'review.json':{'decision':'DRAFT','reviewer':'DRAFT','limitations':'No real review yet','reviewed_claim_ids':[]}},
        'DELIVER':{'synthesis.json':{'conclusion':'DRAFT','tradeoffs':'DRAFT','uncertainty':'DRAFT',
                                   'failure_conditions':'DRAFT','strongest_counterargument':'DRAFT','claim_ids':[]}},
        'MEMORY':{'deliverables.json':{'files':[],'contract_review':'DRAFT'}},
        'EVALUATE':{'lessons.json':{'proposed_methods':[],'limitations':'DRAFT'}},
        'COMPLETE':{'evaluation.json':{'research_quality_proven':False,'limitations':'DRAFT'}}}
    output=[]
    for name,value in defaults.get(stage,{}).items():
        path=project.path/name
        if path.exists(): output.append({'artifact':name,'status':'preserved'}); continue
        atomic_json(path,value); output.append({'artifact':name,'status':'created_draft'})
    return {'stage':stage,'files':output,'warning':'Templates are incomplete drafts. Do not claim validation until backed by actual evidence.'}


def batch_intake(project,mode='rigorous'):
    if mode not in ('lite','standard','rigorous'): raise AtlasError('Mode must be lite, standard, or rigorous')
    s=project.status(); q=questions(project.root,s['domain'],s['answers'],s['extra_questions'])
    if mode=='lite':
        selected={'objective','decision','success','scope','geography','horizon','constraints','budget','permissions','deliverables'}
        q=[row for row in q if row['key'] in selected]
    elif mode=='standard':
        q=[row for row in q if row['batch']=='core' or row['essential']]
    outstanding=[row for row in q if not row['answered']]
    return {'mode':mode,'question':s['question'],'items':outstanding,'rounds_preferred':1 if mode=='lite' else 2,
            'essential_remaining':sum(bool(x['essential']) for x in outstanding),
            'instruction':'Group items as one coherent interview; fill optional answers with stated assumptions. Ask further questions only for material uncertainty; explicitly confirm deliverables.'}
