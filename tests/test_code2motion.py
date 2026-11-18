"""Include the skill's portable numerical/schema tests in repository discovery."""
from pathlib import Path
import runpy

MotionTests = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                               'skills/mano-code2motion/tests/test_motion.py'))['MotionTests']
