from app.geometry import boxes_overlap, fits_within_bounds, get_unique_orientations
from app.models import BoxType, PackageInput, Placement


def test_unique_orientations_cube_vs_cuboid():
    cube = PackageInput(id=1, width=10, height=10, length=10, weight=5)
    cuboid = PackageInput(id=2, width=10, height=20, length=30, weight=5)
    assert len(get_unique_orientations(cube)) == 1
    assert len(get_unique_orientations(cuboid)) == 6


def test_fits_within_bounds_exact_and_overflow():
    box = BoxType("A", 150, 150, 150, 1000)
    assert fits_within_bounds((0, 0, 0), (150, 150, 150), box) is True
    assert fits_within_bounds((0, 0, 0), (150.1, 150, 150), box) is False
    assert fits_within_bounds((10, 0, 0), (145, 10, 10), box) is False


def test_boxes_overlap_touching_allowed_vs_intersection():
    p1 = Placement(package_id=1, x=0, y=0, z=0, width=10, height=10, length=10)
    touching = Placement(package_id=2, x=10, y=0, z=0, width=10, height=10, length=10)
    intersecting = Placement(package_id=3, x=9, y=9, z=9, width=10, height=10, length=10)

    assert boxes_overlap(p1, touching) is False
    assert boxes_overlap(p1, intersecting) is True