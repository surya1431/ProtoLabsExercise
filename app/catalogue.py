from app.models import BoxType

BOX_CATALOGUE: tuple[BoxType, ...] = (
    BoxType(name="A", width=150.0, height=150.0, length=150.0, max_weight=1000.0),
    BoxType(name="B", width=100.0, height=200.0, length=100.0, max_weight=1000.0),
    BoxType(name="C", width=300.0, height=400.0, length=300.0, max_weight=3000.0),
)