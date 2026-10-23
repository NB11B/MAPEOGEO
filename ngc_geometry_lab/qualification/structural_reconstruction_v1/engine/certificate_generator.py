r"""Certificate Generator for GEO-X2 Campaign.

Generates:
- 18 target reconstruction certificates in certificates/reconstruction/
- 12 primitive necessity certificates in certificates/necessity/
- Minimal basis minimization certificate in certificates/minimization/
- Countermodel comparison certificate in certificates/counterexamples/
"""
import os
import json

from qualification.structural_reconstruction_v1.engine.reconstruction_engine import ReconstructionEngine
from qualification.structural_reconstruction_v1.engine.primitive_ablation import PrimitiveAblationSuite
from qualification.structural_reconstruction_v1.engine.subset_minimizer import SubsetMinimizer
from qualification.structural_reconstruction_v1.engine.countermodel import CountermodelEvaluator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_all_certificates():
    recon_engine = ReconstructionEngine()
    ablation_suite = PrimitiveAblationSuite()
    minimizer = SubsetMinimizer()
    evaluator = CountermodelEvaluator()

    all_prims = set(ablation_suite.primitives.keys())

    # 1. Reconstruction certificates (18 targets)
    recon_certs = recon_engine.reconstruct_all(all_prims)
    recon_dir = os.path.join(BASE_DIR, "certificates", "reconstruction")
    for tid, cert in recon_certs.items():
        path = os.path.join(recon_dir, f"{tid}.json")
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(cert.to_dict(), fp, indent=2)

    # 2. Necessity certificates (12 primitives)
    nec_records = ablation_suite.run_all_ablations()
    nec_dir = os.path.join(BASE_DIR, "certificates", "necessity")
    for pid, rec in nec_records.items():
        path = os.path.join(nec_dir, f"{pid}.json")
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(rec.to_dict(), fp, indent=2)

    # 3. Minimization certificate
    min_res = minimizer.find_minimal_bases()
    min_dir = os.path.join(BASE_DIR, "certificates", "minimization")
    path_min = os.path.join(min_dir, "MINIMAL_BASIS_CERTIFICATE.json")
    with open(path_min, "w", encoding="utf-8") as fp:
        json.dump(min_res.to_dict(), fp, indent=2)

    # 4. Countermodel certificate
    counter_res = evaluator.evaluate()
    counter_dir = os.path.join(BASE_DIR, "certificates", "counterexamples")
    path_counter = os.path.join(counter_dir, "M0_M1_M2_COMPARISON.json")
    with open(path_counter, "w", encoding="utf-8") as fp:
        json.dump(counter_res.to_dict(), fp, indent=2)

    return {
        "reconstruction_certificates": len(recon_certs),
        "necessity_certificates": len(nec_records),
        "minimization_certificate": path_min,
        "countermodel_certificate": path_counter
    }


if __name__ == "__main__":
    res = generate_all_certificates()
    print("Generated all GEO-X2 certificates:", res)
