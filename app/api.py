from fastapi import APIRouter, Depends, Query
from app.models import PackageInput
from app.schemas import BoxDetail, PackageRequestItem, PackingResponse, PlacementDetail
from app.service import PackingService

router = APIRouter()
_default_service = PackingService()


def get_packing_service() -> PackingService:
    return _default_service


@router.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.post(
    "/api/v1/packing/calculate",
    response_model=PackingResponse,
    response_model_exclude_none=True,
    tags=["Packing"],
)
def calculate_packing(
    packages: list[PackageRequestItem],
    details: bool = Query(default=False, description="Include 3D placement coordinates"),
    service: PackingService = Depends(get_packing_service),
) -> PackingResponse:
    domain_packages = [
        PackageInput(
            id=item.id,
            width=item.width,
            height=item.height,
            length=item.length,
            weight=item.weight,
        )
        for item in packages
    ]
    result = service.process_batch(domain_packages)

    box_details = None
    if details:
        box_details = [
            BoxDetail(
                box_type=box.box_type.name,
                total_weight=box.total_weight,
                packages=[
                    PlacementDetail(
                        package_id=p.package_id,
                        x=p.x,
                        y=p.y,
                        z=p.z,
                        width=p.width,
                        height=p.height,
                        length=p.length,
                    )
                    for p in box.placements
                ],
            )
            for box in result.packed_boxes
        ]

    return PackingResponse(
        boxes_required=result.boxes_required,
        skipped_duplicate_ids=result.skipped_duplicate_ids,
        unpackable_package_ids=result.unpackable_package_ids,
        boxes=box_details,
    )