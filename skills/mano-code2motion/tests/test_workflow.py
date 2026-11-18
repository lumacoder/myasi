"""Workflow integrity; these tests do not score creativity or visual truth."""
import copy
import html
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
# Do not permanently prepend the skill's generic script names to host import paths.
def module(name,filename):
    old=sys.path[:];sys.path.insert(0,str(ROOT/'scripts'))
    try:
        spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/filename)
        out=importlib.util.module_from_spec(spec);spec.loader.exec_module(out);return out
    finally:sys.path[:]=old
capture=module('c2m_project_capture','render_project.py')
review=module('c2m_review_evidence','review_gate.py')

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        for name,data in {'brief.md':'intent','a.png':'pixels a','b.png':'pixels b',
                           'a.js':'original mechanism','b.js':'changed mechanism','technical.json':'checks'}.items():
            (self.root/name).write_text(data,encoding='utf8')
        self.record={'version':1,'project':'ink','brief':'brief.md','scope':'author still review',
          'reviews':[{'id':x,'variant':x,'time_s':2.8,'frame':x+'.png','sha256':'',
              'pixels_observed':'visible stalk and leaves','intent_delta':'material still graphic',
              'weakest_moment':'full silhouette'} for x in ('a','b')],
          'revisions':[{'from_review':'a','to_review':'b','hypothesis':'uniform width is the problem',
              'substantive_change':'pressure profile modifies the outline','source_before':'a.js',
              'source_after':'b.js','predicted_pixel_change':'tapered outline',
              'observed_result':'taper visible but still idealized'}],
          'comparisons':[{'a':'a','b':'b','same_conditions':['time_s','dimensions'],
              'declared_changes':['stroke geometry']}],
          'gates':{x:{'status':'not_reviewed','evidence':[],'reason':'not independently viewed'}
              for x in ('technical','readability','expression')},
          'limitations':['no normal-speed video review']}
    def tearDown(self):self.tmp.cleanup()
    def check_bad(self):
        with self.assertRaises(ValueError):review.validate(self.record,self.root)
    def test_valid_pending_does_not_mean_visual_pass(self):
        out=review.validate(self.record,self.root)
        self.assertFalse(out['visual_truth_verified']);self.assertEqual(len(out['blockers']),3)
    def test_require_pass_blocks_pending(self):
        with self.assertRaisesRegex(ValueError,'not delivery-approved'):
            review.validate(self.record,self.root,True)
    def test_missing_evidence_rejected(self):
        (self.root/'a.png').unlink();self.check_bad()
    def test_hash_mismatch_rejected(self):
        self.record['reviews'][0]['sha256']='bad';self.check_bad()
    def test_duplicate_review_id_rejected(self):
        self.record['reviews'][1]['id']='a';self.check_bad()
    def test_mismatched_comparison_time_rejected(self):
        self.record['reviews'][1]['time_s']=3.8;self.check_bad()
    def test_identical_source_is_not_revision(self):
        self.record['revisions'][0]['source_after']='a.js';self.check_bad()
    def test_missing_gate_rejected(self):
        del self.record['gates']['expression'];self.check_bad()
    def test_pass_without_evidence_rejected(self):
        self.record['gates']['technical']['status']='pass';self.check_bad()
    def test_placeholder_rejected(self):
        self.record['reviews'][0]['pixels_observed']='REPLACE with opinion';self.check_bad()
    def test_nonfinite_review_time_rejected(self):
        self.record['reviews'][0]['time_s']=float('nan');self.check_bad()
    def test_partial_is_not_delivery_pass(self):
        for v in self.record['gates'].values():v.update(status='partial',evidence=['a.png'])
        with self.assertRaises(ValueError):review.validate(self.record,self.root,True)
    def test_declared_pass_is_not_verified_truth(self):
        for v in self.record['gates'].values():v.update(status='pass',evidence=['a.png'])
        self.assertFalse(review.validate(self.record,self.root,True)['visual_truth_verified'])
    def test_frame_settings(self):self.assertEqual(capture.settings(6,24,1280,720),144)
    def test_bad_settings(self):
        for args in ((float('nan'),24,1280,720),(0,24,1280,720),(.01,24,1280,720),
                     (6,0,1280,720),(6,24,1279,720),(6,24,1280,0)):
            with self.subTest(args=args),self.assertRaises(ValueError):capture.settings(*args)
    def test_capture_protocol_checks_readiness_and_dimensions(self):
        result={'status':'ready','time_s':2.8,'width':1280,'height':720,'seek_order_checked':True}
        dom='<pre id="motion-capture" hidden="">'+html.escape(json.dumps(result))+'</pre>'
        self.assertEqual(capture.parse_protocol(dom,2.8,1280,720,True)['status'],'ready')
        for bad in (dom.replace('ready','pending'),dom.replace('1280','640'),
                    dom.replace('2.8','2.9'),dom.replace('true','false'),''):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                capture.parse_protocol(bad,2.8,1280,720,True)
    def test_protocol_accepts_serialized_float_tolerance(self):
        t=1/24;result={'status':'ready','time_s':float('%.12g'%t),'width':1280,'height':720}
        dom='<pre id="motion-capture">'+json.dumps(result)+'</pre>'
        capture.parse_protocol(dom,t,1280,720)
    def test_local_server_path_traversal_rejected(self):
        for path in ('/../outside','/%2e%2e/outside','/not-a-file','/'):
            with self.subTest(path=path),self.assertRaises(ValueError):capture.safe_file(self.root,path)
        self.assertEqual(capture.safe_file(self.root,'/brief.md?ignored=1'),(self.root/'brief.md').resolve())
    @unittest.skipUnless(shutil.which('node'),'Node optional; run qa.js separately when available')
    def test_original_case_adapter_qa(self):
        for script in ('qa.js','qa-c.js'):
            with self.subTest(script=script):
                result=subprocess.run([shutil.which('node'),str(ROOT/'examples/ink-bamboo'/script)],
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf8',timeout=30)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(json.loads(result.stdout)['status'],'PASS')

if __name__=='__main__':unittest.main()
