import threading
from dataclasses import dataclass
from app.models import PackedBox, PackageInput
from app.packer import pack_packages


@dataclass(frozen=True)
class ServiceResult:
    boxes_required: int
    skipped_duplicate_ids: list[int]
    unpackable_package_ids: list[int]
    packed_boxes: list[PackedBox]


class PackingService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._processed_ids: set[int] = set()

    def process_batch(self, packages: list[PackageInput]) -> ServiceResult:
        with self._lock:
            unique_packages: list[PackageInput] = []
            skipped_ids: list[int] = []
            seen_in_request: set[int] = set()

            for pkg in packages:
                if pkg.id in self._processed_ids or pkg.id in seen_in_request:
                    skipped_ids.append(pkg.id)
                else:
                    seen_in_request.add(pkg.id)
                    unique_packages.append(pkg)

            if not unique_packages:
                return ServiceResult(
                    boxes_required=0,
                    skipped_duplicate_ids=skipped_ids,
                    unpackable_package_ids=[],
                    packed_boxes=[],
                )

            outcome = pack_packages(unique_packages)

            # Only commit IDs that were successfully packed
            self._processed_ids.update(outcome.packed_ids)

            return ServiceResult(
                boxes_required=len(outcome.packed_boxes),
                skipped_duplicate_ids=skipped_ids,
                unpackable_package_ids=outcome.unpackable_ids,
                packed_boxes=outcome.packed_boxes,
            )