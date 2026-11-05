#!/usr/bin/env python3
"""Illustrative incident recovery simulation; no external sources or AI workers."""
import json
from pathlib import Path
import shutil
import tempfile
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from atlas.demo import prepare_research
from atlas.capture import capture_source,capture_claim,capture_search
from atlas.operability import next_actions
from atlas.reporting import limited_report

ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as t:
    root=Path(t)
    shutil.copytree(ROOT/'methods',root/'methods')
    project=prepare_research(root,'simulation')
    source=capture_source(project,'https://www.census.gov/','Illustrative public source',
                          'Synthetic snippet only; NOT retrieved from the Census website.',
                          'Example question',tool='synthetic',provisional=True)
    claim=capture_claim(project,'A synthetic snippet is available.',[source['source_id']],
                        scope='This offline simulation only',material=True)
    capture_search(project,'Unsuccessful optional query','synthetic','Network unavailable; no source found')
    project.block_access('https://www.census.gov','read','Synthetic timeout','Missing optional document',severity='optional')
    report=project.path/'outputs/draft.md'
    report.write_text('# Synthetic demonstration\n\nThis is not a real research finding. [[claim:'+claim['claim_id']+']]\n',encoding='utf-8')
    limited=limited_report(project,report,'Only a fabricated snippet was supplied; no independent verification')
    outcome={'state':project.status()['state'],'held':project.status()['hold'],
             'captured_sources':len(project.artifact('evidence.json')['sources']),
             'captured_claims':len(project.artifact('evidence.json')['claims']),
             'search_log_entries':len(json.loads((project.path/'search_log.json').read_text())['queries']),
             'limited_report':limited['status'],'next_step':next_actions(project)['next_stage'],
             'warning':'A test of local control paths, not real research or network access.'}
    assert outcome['state']=='RESEARCH' and outcome['held'] is None
    assert outcome['captured_sources']==1 and outcome['captured_claims']==1
    assert outcome['search_log_entries']==2 and outcome['limited_report']=='LIMITED_NOT_VERIFIED'
    print(json.dumps(outcome,indent=2))
