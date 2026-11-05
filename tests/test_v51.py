"""ATLAS 5.1 incident-regression tests. All external access is mocked; not a live research benchmark."""
import base64
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from atlas.project import Project
from atlas.demo import prepare_research,complete
from atlas.io import AtlasError,atomic_json,now,read_json
from atlas.operability import next_actions,scaffold,batch_intake
from atlas.capture import capture_source,capture_claim,capture_search
from atlas.evidence import validate_evidence
from atlas.verification import report_audit
from atlas.reporting import render_markdown,limited_report,export_report
from atlas.network_doctor import doctor_network
from atlas.privacy import git_inspect
from atlas.delivery_contract import set_contract,audit_contract
from atlas.budget import Budget
from atlas.__main__ import main

REPO=Path(__file__).resolve().parents[1]

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

class Workspace(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        shutil.copytree(REPO/'methods',self.root/'methods')
    def tearDown(self):self.temp.cleanup()
    def project(self):return Project.create(self.root,'case','Assess a bounded business question','general')

class OperatorTests(Workspace):
    def test_modes(self):
        p=Project.create(self.root,'case','Question','general',research_mode='lite')
        self.assertEqual(p.status()['research_mode'],'lite')
        self.assertLess(len(batch_intake(p,'lite')['items']),len(batch_intake(p,'rigorous')['items']))
    def test_next_lists_all_unanswered_core(self):
        p=self.project();result=next_actions(p)
        self.assertEqual(result['current_stage'],'INTAKE')
        self.assertEqual(result['next_stage'],'MANDATE')
        self.assertGreater(len(result['issues']),5)
        self.assertFalse(result['can_advance'])
    def test_scaffold_draft_not_overwritten(self):
        p=self.project()
        p.mandate({q['key']:'Explicit assumption' for q in batch_intake(p)['items'] if q['essential']},True)
        p.advance('MANDATE')
        result=scaffold(p,'ENABLEMENT');self.assertTrue(result['files'])
        original=(p.path/'enablement.json').read_bytes()
        self.assertEqual(scaffold(p,'ENABLEMENT')['files'][0]['status'],'preserved')
        self.assertEqual(original,(p.path/'enablement.json').read_bytes())
    def test_stage_error_identifies_next(self):
        p=self.project()
        with self.assertRaisesRegex(AtlasError,'current=INTAKE.*next_allowed=MANDATE'):p.advance('RESEARCH')
    def test_cli_mandate_auto_advances(self):
        p=self.project()
        for q in batch_intake(p)['items']:
            if q['essential']:p.answer(q['key'],'User answer provided for test')
        with contextlib.redirect_stdout(io.StringIO()):
            code=main(['--root',str(self.root),'mandate','case','--acknowledged'])
        self.assertEqual(code,0)
        self.assertEqual(p.status()['state'],'MANDATE')
    def test_cli_next_and_dry_run(self):
        self.project()
        for args in (['next','case'],['advance','case','MANDATE','--dry-run']):
            output=io.StringIO()
            with contextlib.redirect_stdout(output):code=main(['--root',str(self.root),*args])
            self.assertEqual(code,0);self.assertIn('next_stage',output.getvalue())
    def test_expires_do_not_block_offline_task_finish(self):
        p=prepare_research(self.root)
        p.task('collect','running')
        # Expires after the running task started; this is only offline bookkeeping.
        state=p.status(); receipt=state['access']['tests']['local']
        row=read_json(p.path/receipt['artifact']);row['expires_at']='2020-01-01'
        # Changing recorded receipt hash should fail integrity, not expiry test.
        atomic_json(p.path/receipt['artifact'],row)
        with self.assertRaises(AtlasError):p.task('collect','done','branches/missing.json')
    def test_access_reapproval_keeps_unchanged_receipts(self):
        p=prepare_research(self.root)
        previous=p.status()['access']['tests']
        decisions=p.status()['access']['decisions']
        p.approve_access(decisions,'Reconfirmed same approved policy')
        self.assertEqual(previous,p.status()['access']['tests'])
    def test_optional_block_does_not_revoke_existing_access(self):
        p=prepare_research(self.root)
        p.block_access('https://www.example.org','read','Temporary 504','One optional source missing','local',severity='optional')
        self.assertFalse(p.status()['hold'])
        self.assertIn('local',p.status()['access']['tests'])
    def test_optional_block_cli_is_recorded_successfully(self):
        p=prepare_research(self.root)
        sink=io.StringIO()
        with contextlib.redirect_stdout(sink):
            rc=main(['--root',str(self.root),'access-block',p.slug,'--resource','https://www.example.org',
                '--operation','read','--reason','Timeout','--quality-impact','Optional limitation','--severity','optional'])
        self.assertEqual(rc,0)
        self.assertTrue(json.loads(sink.getvalue())['ok'])
    def test_budget_status_without_limit(self):
        f=self.root/'budget.sqlite3'
        self.assertEqual(Budget(f,'1.00').status()['remaining_usd'],'1.00')
        self.assertEqual(Budget(f,None).status()['remaining_usd'],'1.00')
    def test_cli_budget_status_without_limit(self):
        b=Budget(self.root/'.atlas/budget.sqlite3','3.00')
        sink=io.StringIO()
        with contextlib.redirect_stdout(sink):rc=main(['--root',str(self.root),'budget','status'])
        self.assertEqual(rc,0)
        self.assertEqual(json.loads(sink.getvalue())['remaining_usd'],'3.00')

class EvidenceTests(Workspace):
    def test_capture_snippet_and_preserve_query(self):
        p=prepare_research(self.root)
        result=capture_source(p,'https://www.census.gov/data','Census example','Snippet from search only','market demand',provisional=True)
        self.assertTrue((p.path/result['snapshot']).is_file())
        self.assertEqual(len(read_json(p.path/'search_log.json')['queries']),1)
        check=validate_evidence(p.artifact('evidence.json'),p.path)
        self.assertIn('provisional_source',{w['code'] for w in check['warnings']})
    def test_claim_on_snippet_is_not_independently_verified(self):
        p=prepare_research(self.root)
        source=capture_source(p,'https://www.census.gov/data','Census','Snippet text','query',provisional=True)
        claim=capture_claim(p,'Snippet text',['S0001'],scope='US, time unspecified',material=True)
        validation=validate_evidence(p.artifact('evidence.json'),p.path)
        self.assertIn('unreviewed_claim',{e['code'] for e in validation['errors']})
    def test_capture_search_zero_results(self):
        p=prepare_research(self.root)
        row=capture_search(p,'obscure question','search provider','No results',status='partial')
        self.assertEqual(row['retrieved_ids'],[])
    def test_strict_report_fails_zero_claims(self):
        p=self.project()
        result=report_audit('# Summary\nAn unsupported finding.',p.artifact('evidence.json'),strict=True)
        self.assertFalse(result['ok']);self.assertEqual(result['errors'][0]['code'],'no_claims')
    def test_limited_report_banners(self):
        p=prepare_research(self.root)
        src=p.path/'outputs/draft.md';src.write_text('# Draft\nUnverified claims are not conclusions.')
        receipt=limited_report(p,src,'Key primary sources unavailable')
        self.assertEqual(receipt['status'],'LIMITED_NOT_VERIFIED')
        self.assertIn('LIMITED / UNVERIFIED', (p.path/'outputs/limited-report.md').read_text())
        self.assertEqual(p.status()['state'],'RESEARCH')
    def test_render_claim_to_footnote(self):
        p=prepare_research(self.root)
        capture_source(p,'https://www.census.gov/data','Census','Observed text','query',provisional=True)
        capture_claim(p,'Observed text',['S0001'],scope='Test scope',material=False)
        result=render_markdown('Claim [[claim:C0001]]',p.artifact('evidence.json'))
        self.assertIn('[1]',result);self.assertIn('## References',result)
    def test_pdf_export_optional(self):
        try:import reportlab
        except ImportError:self.skipTest('Optional PDF dependency unavailable')
        p=prepare_research(self.root)
        path=p.path/'outputs/draft.md';path.write_text('# Test Report\nThis is not verified.')
        receipt=export_report(p,'outputs/draft.md','outputs/draft.pdf','pdf',limited=True,limitations='Unverified')
        self.assertEqual(receipt['format'],'pdf')
        self.assertTrue((p.path/'outputs/draft.pdf').read_bytes().startswith(b'%PDF'))
    def test_report_contract(self):
        p=self.project()
        set_contract(p,{'schema_version':1,'required_sections':['Overview','Risks'], 'minimum_words':15,'approval':'user_specified'})
        self.assertFalse(audit_contract(p,'# Overview\nA few words only.')['ok'])
        self.assertTrue(audit_contract(p,'# Overview\n# Risks\n'+('Substantive wording is required here. '*5))['ok'])
    def test_source_url_not_credentials(self):
        p=prepare_research(self.root)
        with self.assertRaises(AtlasError):capture_source(p,'https://a:b@www.census.gov','Title','Body','query')
    def test_exploratory_search_cap(self):
        p=prepare_research(self.root)
        p.prepare_search('local','Inspect additional independent source',probe=False,plan_id='EXPLORATORY')
        with self.assertRaises(AtlasError):p.prepare_search('unknown','Another','EXPLORATORY')

class SafetyTests(Workspace):
    def test_network_requires_authorization(self):
        self.assertFalse(doctor_network(['github.com'])['ok'])
    def test_network_mock(self):
        with patch('atlas.network_doctor.inspect_host',return_value={'ok':False,'host':'example.org','error':'DNS denied'}):
            result=doctor_network(['example.org'],authorized=True)
        self.assertFalse(result['ok'])
        self.assertIn('firewall',result['remediation'])
    def test_git_tracked_projects_detected(self):
        subprocess.run(['git','init','-q',str(self.root)],check=True,stdout=subprocess.DEVNULL)
        (self.root/'projects').mkdir();(self.root/'projects/report.md').write_text('sensitive')
        (self.root/'projects/.gitkeep').write_text('')
        subprocess.run(['git','-C',str(self.root),'add','projects/report.md','projects/.gitkeep'],check=True)
        result=git_inspect(self.root)
        self.assertIn('projects/report.md',result['sensitive_tracked'])
        self.assertNotIn('projects/.gitkeep',result['sensitive_tracked'])
        self.assertFalse(result['safe_to_commit'])
    def test_installer_zip_traversal_rejected(self):
        mod=load_module(REPO/'scripts/install_from_zip.py','atlas_installer_test')
        p=self.root/'bad.zip'
        with zipfile.ZipFile(p,'w') as z:z.writestr('ATLAS/../../attack.txt','oops')
        with self.assertRaises(ValueError):mod.install(p,self.root/'target')
    def test_installer_no_overwrite(self):
        mod=load_module(REPO/'scripts/install_from_zip.py','atlas_installer_test2')
        p=self.root/'pack.zip'
        with zipfile.ZipFile(p,'w') as z:z.writestr('ATLAS/AGENTS.md','instructions')
        dest=self.root/'other';dest.mkdir();(dest/'AGENTS.md').write_text('existing')
        with self.assertRaises(FileExistsError):mod.install(p,dest)
        self.assertEqual((dest/'AGENTS.md').read_text(),'existing')
    def test_relay_disabled_and_encryption_round_trip(self):
        mod=load_module(REPO/'optional_integrations/github_actions_fetch_relay/relay.py','atlas_relay_test')
        try:import cryptography
        except ImportError:self.skipTest('Optional cryptography unavailable')
        private=self.root/'keys/private';public=self.root/'keys/public'
        mod.keygen(private,public)
        ciphertext=mod.encrypt(b'public facts',public.read_text())
        self.assertEqual(mod.decrypt(ciphertext,private.read_text()),b'public facts')
        with patch.dict(os.environ,{},clear=True):
            # By default the relay cannot run, regardless of URLs.
            with self.assertRaisesRegex(ValueError,'disabled'): 
                from unittest.mock import patch as _patch
                with _patch('sys.argv',['relay.py','run','--allowlist',str(REPO/'optional_integrations/github_actions_fetch_relay/allowlist.json'),
                        '--public-key',str(public),'--output',str(self.root/'result.json')]):mod.main()
    def test_relay_private_address_rejected(self):
        mod=load_module(REPO/'optional_integrations/github_actions_fetch_relay/relay.py','atlas_relay_test2')
        with patch('socket.getaddrinfo',return_value=[(0,0,0,'',('127.0.0.1',443))]):
            with self.assertRaisesRegex(ValueError,'Nonpublic'):mod.validate_url('https://www.census.gov/data',{'www.census.gov'})
    def test_relay_dispatch_requires_owner_approval(self):
        mod=load_module(REPO/'optional_integrations/github_actions_fetch_relay/trigger.py','atlas_relay_trigger')
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'approval'):
                mod.dispatch('owner','repo',['https://www.census.gov/data'],'main','secret',False,{'www.census.gov'})
    def test_relay_dispatch_mock_submission_not_success(self):
        mod=load_module(REPO/'optional_integrations/github_actions_fetch_relay/trigger.py','atlas_relay_trigger2')
        class Response:
            status=204
            def __enter__(self):return self
            def __exit__(self,*args):pass
        with patch.dict(os.environ,{'ATLAS_RELAY_OWNER_AUTHORIZED':'true'}):
            with patch('urllib.request.urlopen',return_value=Response()) as request:
                result=mod.dispatch('owner','repo',['https://www.census.gov/data'],'main','secret',True,{'www.census.gov'})
        self.assertTrue(result['accepted_for_dispatch'])
        self.assertIn('not establish',result['important'])

if __name__=='__main__':unittest.main()
