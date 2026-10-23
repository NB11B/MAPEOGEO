from mapeogeo.psmsl_work_plan_v1 import derive_plan

def test_commuting_scale_family_is_parallelizable():
    ops=(((2,0),(0,2)),((3,0),(0,3)))
    p=derive_plan(ops)
    assert p.reorder_safe and p.parallelizable and p.irreversible_steps==()

def test_projection_is_marked_irreversible():
    p=derive_plan((((1,0,0),(0,1,0)),))
    assert p.irreversible_steps==(0,)
