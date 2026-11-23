from itertools import permutations
from app.models import BoxType, PackageInput, Placement


def get_unique_orientations(pkg: PackageInput) -> list[tuple[float, float, float]]:
    """Return all unique axis-aligned (width, height, length) rotations."""
    dims = (pkg.width, pkg.height, pkg.length)
    return sorted(set(permutations(dims)), reverse=True)


def fits_within_bounds(
    point: tuple[float, float, float],
    dims: tuple[float, float, float],
    box: BoxType,
) -> bool:
    """Check if a package at `point` with `dims` stays inside `box`."""
    x, y, z = point
    w, h, l = dims
    return (
        x >= 0.0
        and y >= 0.0
        and z >= 0.0
        and (x + w) <= box.width
        and (y + h) <= box.height
        and (z + l) <= box.length
    )


def boxes_overlap(a: Placement, b: Placement) -> bool:
    """Return True if two placements share interior volume (touching faces allowed)."""
    return (
        a.x < (b.x + b.width)
        and b.x < (a.x + a.width)
        and a.y < (b.y + b.height)
        and b.y < (a.y + a.height)
        and a.z < (b.z + b.length)
        and b.z < (a.z + a.length)
    )