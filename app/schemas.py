from pydantic import BaseModel, ConfigDict, Field, StrictInt


class PackageRequestItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: StrictInt = Field(..., description="Unique integer identifier for the package")
    width: float = Field(..., gt=0, description="Package width (> 0)")
    height: float = Field(..., gt=0, description="Package height (> 0)")
    length: float = Field(..., gt=0, description="Package length (> 0)")
    weight: float = Field(..., gt=0, description="Package weight (> 0)")


class PlacementDetail(BaseModel):
    package_id: int
    x: float
    y: float
    z: float
    width: float
    height: float
    length: float


class BoxDetail(BaseModel):
    box_type: str
    total_weight: float
    packages: list[PlacementDetail]


class PackingResponse(BaseModel):
    boxes_required: int
    skipped_duplicate_ids: list[int]
    unpackable_package_ids: list[int]
    boxes: list[BoxDetail] | None = None