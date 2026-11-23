from app.models import PackageInput
from app.service import PackingService


def test_duplicate_tracking_and_unpackable_retry():
    service = PackingService()

    # Batch 1: ID 1 packed, ID 1 duplicate skipped, ID 2 unpackable (not registered)
    res1 = service.process_batch([
        PackageInput(id=1, width=10, height=10, length=10, weight=5),
        PackageInput(id=1, width=10, height=10, length=10, weight=5),
        PackageInput(id=2, width=999, height=10, length=10, weight=5),
    ])
    assert res1.boxes_required == 1
    assert res1.skipped_duplicate_ids == [1]
    assert res1.unpackable_package_ids == [2]

    # Batch 2: ID 1 is still skipped (cross-request), corrected ID 2 succeeds
    res2 = service.process_batch([
        PackageInput(id=1, width=10, height=10, length=10, weight=5),
        PackageInput(id=2, width=10, height=10, length=10, weight=5),
    ])
    assert res2.boxes_required == 1
    assert res2.skipped_duplicate_ids == [1]
    assert res2.unpackable_package_ids == []