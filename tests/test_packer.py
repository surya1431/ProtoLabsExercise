from app.geometry import boxes_overlap, fits_within_bounds
from app.models import PackageInput
from app.packer import pack_packages


def test_example_payload_fits_in_one_box():
    pkgs = [
        PackageInput(id=123, width=10, height=10, length=10, weight=5),
        PackageInput(id=125, width=5, height=5, length=10, weight=10),
    ]
    outcome = pack_packages(pkgs)
    assert len(outcome.packed_boxes) == 1
    assert outcome.packed_ids == [123, 125]
    assert outcome.unpackable_ids == []


def test_rotation_required_to_fit_box_c():
    # Box C is 300x400x300; package is 400x300x300
    pkgs = [PackageInput(id=1, width=400, height=300, length=300, weight=100)]
    outcome = pack_packages(pkgs)
    assert len(outcome.packed_boxes) == 1


def test_weight_limit_splits_into_multiple_boxes():
    # Six 600g packages = 3600g > Box C max_weight (3000g) -> requires 2 boxes
    pkgs = [
        PackageInput(id=i, width=10, height=10, length=10, weight=600)
        for i in range(1, 7)
    ]
    outcome = pack_packages(pkgs)
    assert len(outcome.packed_boxes) == 2


def test_unpackable_items_separated_while_rest_packed():
    pkgs = [
        PackageInput(id=1, width=10, height=10, length=10, weight=10),
        PackageInput(id=998, width=500, height=10, length=10, weight=10),  # too wide
        PackageInput(id=999, width=10, height=10, length=10, weight=5000),  # too heavy
    ]
    outcome = pack_packages(pkgs)
    assert len(outcome.packed_boxes) == 1
    assert outcome.packed_ids == [1]
    assert outcome.unpackable_ids == [998, 999]


def test_geometric_invariants_no_overlap_and_in_bounds():
    pkgs = [
        PackageInput(id=i, width=100, height=100, length=100, weight=100)
        for i in range(1, 20)
    ]
    outcome = pack_packages(pkgs)
    for box in outcome.packed_boxes:
        assert box.total_weight <= box.box_type.max_weight
        for i, p1 in enumerate(box.placements):
            assert fits_within_bounds(
                (p1.x, p1.y, p1.z), (p1.width, p1.height, p1.length), box.box_type
            )
            for p2 in box.placements[i + 1 :]:
                assert not boxes_overlap(p1, p2)