r"""Integration test runner for qualification/structural_reconstruction_v1/."""
import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tests.test_geox2_structural_reconstruction import TestGeoX2StructuralReconstruction

if __name__ == "__main__":
    unittest.main()
