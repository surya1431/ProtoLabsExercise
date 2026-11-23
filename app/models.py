from dataclasses import dataclass, field


@dataclass(frozen=True)
class PackageInput:
    id: int
    width: float
    height: float
    length: float
    weight: float

    @property
    def volume(self) -> float:
        return self.width * self.height * self.length


@dataclass(frozen=True)
class BoxType:
    name: str
    width: float
    height: float
    length: float
    max_weight: float

    @property
    def volume(self) -> float:
        return self.width * self.height * self.length


@dataclass(frozen=True)
class Placement:
    package_id: int
    x: float
    y: float
    z: float
    width: float
    height: float
    length: float


@dataclass
class PackedBox:
    box_type: BoxType
    placements: list[Placement] = field(default_factory=list)
    total_weight: float = 0.0
    candidate_points: set[tuple[float, float, float]] = field(
        default_factory=lambda: {(0.0, 0.0, 0.0)}
    )

    def add_placement(self, placement: Placement, weight: float) -> None:
        self.placements.append(placement)
        self.total_weight += weight
        # Remove the used corner and add 3 new extreme points
        self.candidate_points.discard((placement.x, placement.y, placement.z))
        self.candidate_points.add((placement.x + placement.width, placement.y, placement.z))
        self.candidate_points.add((placement.x, placement.y + placement.height, placement.z))
        self.candidate_points.add((placement.x, placement.y, placement.z + placement.length))