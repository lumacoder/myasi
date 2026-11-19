"""Include numeric regression and director/workflow evidence tests in repository discovery."""
from pathlib import Path
import runpy

TESTS = Path(__file__).resolve().parents[1] / 'skills/mano-code2motion/tests'
MotionTests = runpy.run_path(str(TESTS / 'test_motion.py'))['MotionTests']
WorkflowTests = runpy.run_path(str(TESTS / 'test_workflow.py'))['WorkflowTests']

# Local production contract/media regressions; not creative-quality benchmarks.
_production = runpy.run_path(str(TESTS / "test_production.py"))
ProductionContractTests = _production["ContractTests"]
ProductionMediaTests = _production["MediaTests"]
