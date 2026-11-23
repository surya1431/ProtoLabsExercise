from dataclasses import dataclass
from app.catalogue import BOX_CATALOGUE
from app.geometry import boxes_overlap, fits_within_bounds, get_unique_orientations
from app.models import BoxType, PackedBox, PackageInput, Placement


@dataclass(frozen=True)
class PackingOutcome:
    packed_boxes: list[PackedBox]
    packed_ids: list[int]
    unpackable_ids: list[int]


def can_fit_in_empty_box(pkg: PackageInput, box_type: BoxType) -> bool:
    """Check if a single package fits in an empty box of `box_type` under any rotation."""
    if pkg.weight > box_type.max_weight:
        return False
    return any(
        fits_within_bounds((0.0, 0.0, 0.0), dims, box_type)
        for dims in get_unique_orientations(pkg)
    )


def select_largest_box_for(pkg: PackageInput) -> BoxType | None:
    """Return the largest-volume box type capable of holding `pkg` alone."""
    sorted_catalogue = sorted(BOX_CATALOGUE, key=lambda b: b.volume, reverse=True)
    for box_type in sorted_catalogue:
        if can_fit_in_empty_box(pkg, box_type):
            return box_type
    return None


def try_place_in_open_box(pkg: PackageInput, box: PackedBox) -> Placement | None:
    """Attempt to place `pkg` at an extreme point inside an already-open `box`."""
    if box.total_weight + pkg.weight > box.box_type.max_weight:
        return None

    # Sort points by (y, z, x) to fill bottom layers first
    ordered_points = sorted(box.candidate_points, key=lambda pt: (pt[1], pt[2], pt[0]))
    orientations = get_unique_orientations(pkg)

    for point in ordered_points:
        for w, h, l in orientations:
            if not fits_within_bounds(point, (w, h, l), box.box_type):
                continue
            candidate = Placement(
                package_id=pkg.id,
                x=point[0],
                y=point[1],
                z=point[2],
                width=w,
                height=h,
                length=l,
            )
            if all(not boxes_overlap(candidate, existing) for existing in box.placements):
                return candidate
    return None


def pack_packages(packages: list[PackageInput]) -> PackingOutcome:
    """Pack valid packages using FFD + Extreme Points; separate unpackable items."""
    packable: list[tuple[PackageInput, BoxType]] = []
    unpackable_ids: list[int] = []

    for pkg in packages:
        largest_box = select_largest_box_for(pkg)
        if largest_box is None:
            unpackable_ids.append(pkg.id)
        else:
            packable.append((pkg, largest_box))

    # Deterministic FFD sorting: volume desc, weight desc, id asc
    packable.sort(key=lambda item: (-item[0].volume, -item[0].weight, item[0].id))

    open_boxes: list[PackedBox] = []
    packed_ids: list[int] = []

    for pkg, fallback_box_type in packable:
        placed = False
        for box in open_boxes:
            placement = try_place_in_open_box(pkg, box)
            if placement is not None:
                box.add_placement(placement, pkg.weight)
                packed_ids.append(pkg.id)
                placed = True
                break

        if not placed:
            new_box = PackedBox(box_type=fallback_box_type)
            placement = try_place_in_open_box(pkg, new_box)
            assert placement is not None  # Guaranteed by select_largest_box_for
            new_box.add_placement(placement, pkg.weight)
            open_boxes.append(new_box)
            packed_ids.append(pkg.id)

    return PackingOutcome(
        packed_boxes=open_boxes,
        packed_ids=packed_ids,
        unpackable_ids=unpackable_ids,
    )