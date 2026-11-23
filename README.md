# 3D Box Packing Service

A FastAPI service that accepts a batch of rectangular packages and calculates how many shipping boxes are required. It considers package rotation, 3D placement, and the maximum weight capacity of each box.

The service uses a deterministic heuristic rather than an exhaustive search for a globally optimal packing arrangement.

## Features

- Packs multiple rectangular packages into each shipping box where possible.
- Supports all six axis-aligned orientations of a package.
- Checks box dimensions and maximum weight capacity.
- Prevents packages from overlapping while allowing touching faces and edges.
- Skips duplicate package IDs within a request and across previous requests handled by the same application process.
- Reports packages that cannot fit in any available box.
- Optionally returns the box assignments and 3D placement coordinates.
- Provides a health-check endpoint.
- Includes unit and API tests for geometry, packing, duplicate handling, and request validation.

## Project structure

```text
box-packing-service/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and validation error handler
│   ├── api.py           # HTTP endpoints
│   ├── schemas.py       # Pydantic request and response models
│   ├── models.py        # Domain dataclasses
│   ├── catalogue.py     # Shipping box catalogue
│   ├── geometry.py      # Rotations, boundary checks, and overlap detection
│   ├── packer.py        # 3D packing heuristic
│   └── service.py       # Request processing and duplicate tracking
├── tests/
│   ├── __init__.py
│   ├── test_geometry.py
│   ├── test_packer.py
│   ├── test_service.py
│   └── test_api.py
├── requirements.txt
├── README.md
├── Dockerfile           # Optional
```

## Requirements

- Python 3.10 or later
- pip

The dependencies are listed in `requirements.txt`:

- FastAPI
- Uvicorn
- Pydantic v2
- pytest
- HTTPX

## Setup and run

### 1. Create and activate a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Start the API

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The service is available at:

- API base URL: `http://127.0.0.1:8000`
- Interactive Swagger documentation: `http://127.0.0.1:8000/docs`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

The `--reload` option is intended for local development.

## API

### Health check

```http
GET /health
```

Example response:

```json
{
  "status": "healthy"
}
```

### Calculate required boxes

```http
POST /api/v1/packing/calculate
Content-Type: application/json
```

The request body is a JSON array. Each package must contain:

| Field    | Type    | Description        |
|----------|---------|--------------------|
| `id`     | Integer | Package identifier |
| `width`  | Number  | Package width      |
| `height` | Number  | Package height     |
| `length` | Number  | Package length     |
| `weight` | Number  | Package weight     |

All dimensions and weights must be greater than zero. Unknown fields are rejected.

#### Example request

```json
[
  {
    "id": 123,
    "width": 10,
    "height": 10,
    "length": 10,
    "weight": 5
  },
  {
    "id": 125,
    "width": 5,
    "height": 5,
    "length": 10,
    "weight": 10
  }
]
```

#### Example response — HTTP 200

```json
{
  "boxes_required": 1,
  "skipped_duplicate_ids": [],
  "unpackable_package_ids": []
}
```

The response reports the number of boxes used for the packages newly packed in that request.

### Include placement details

Add `?details=true` to include the selected box type, total box weight, and placement coordinates:

```http
POST /api/v1/packing/calculate?details=true
```

Example response:

```json
{
  "boxes_required": 1,
  "skipped_duplicate_ids": [],
  "unpackable_package_ids": [],
  "boxes": [
    {
      "box_type": "C",
      "total_weight": 15.0,
      "packages": [
        {
          "package_id": 123,
          "x": 0.0,
          "y": 0.0,
          "z": 0.0,
          "width": 10.0,
          "height": 10.0,
          "length": 10.0
        },
        {
          "package_id": 125,
          "x": 10.0,
          "y": 0.0,
          "z": 0.0,
          "width": 10.0,
          "height": 5.0,
          "length": 5.0
        }
      ]
    }
  ]
}
```

The coordinates describe the position of the package's lower corner inside its box. The dimensions in the response are the dimensions after rotation. The example illustrates the response shape; actual placement depends on the heuristic and its candidate-point ordering.

### Response fields

| Field                    | Description                                                                                              |
|--------------------------|----------------------------------------------------------------------------------------------------------|
| `boxes_required`         | Number of boxes opened for packages successfully packed in this request                                  |
| `skipped_duplicate_ids`  | IDs skipped because they already appeared in the current request or were processed by an earlier request |
| `unpackable_package_ids` | IDs that cannot fit in any catalogue box, considering rotation and weight                                |
| `boxes`                  | Present only when `details=true`; contains box types, total weights, and package placements              |

An empty array is valid and returns HTTP 200:

```json
{
  "boxes_required": 0,
  "skipped_duplicate_ids": [],
  "unpackable_package_ids": []
}
```

## Box catalogue

The service uses the following fixed box definitions:

| Box | Width | Height | Length | Maximum weight |
|-----|------:|-------:|-------:|---------------:|
| A   |   150 |    150 |    150 |          1,000 |
| B   |   100 |    200 |    100 |          1,000 |
| C   |   300 |    400 |    300 |          3,000 |

The dimensions and weights use the same units as the incoming package data.

Box C is larger than A and B on every dimension and has a higher weight capacity. The current packing implementation therefore opens the largest eligible box type for a package. This is a deliberate heuristic choice for the objective of reducing the number of boxes; it does not optimize shipping cost or unused box volume.

## Packing approach

Three-dimensional bin packing with weight constraints is an NP-hard problem. Finding the globally optimal arrangement can be computationally expensive. This service uses a deterministic **First-Fit Decreasing (FFD) ordering with Extreme-Point 3D placement**.

### 1. Identify packages that cannot fit

Before placing packages, the packer checks whether each package can fit by itself in at least one catalogue box.

- All six unique axis-aligned orientations are considered.
- The package must fit within the box dimensions.
- Its weight must not exceed that box's maximum weight.

Packages that fail this check are returned in `unpackable_package_ids`. Other valid packages in the same request are still packed.

### 2. Sort packable packages

Packable packages are sorted by:

1. Volume — descending
2. Weight — descending
3. Package ID — ascending

Larger and heavier packages are considered first. The ID tie-breaker makes the order deterministic when volume and weight are equal.

### 3. Try existing boxes using extreme points

Each open box starts with a candidate placement point at `(0, 0, 0)`.

When a package is placed at `(x, y, z)` with oriented dimensions `(w, h, l)`, the packer adds three candidate points:

- `(x + w, y, z)`
- `(x, y + h, z)`
- `(x, y, z + l)`

Candidate points are checked in `(y, z, x)` order, prioritizing lower positions. For each point, the packer tries the package's unique orientations and checks:

- The package remains within the box boundaries.
- It does not overlap any package already placed in that box.
- The box's total weight will remain within its limit.

The first valid placement is used. If no open box can accept the package, a new eligible box is opened and the package is placed in it.

### 4. Geometry and rotation

Packages are treated as axis-aligned rectangular cuboids. Rotation means permuting the width, height, and length across the three box axes. Duplicate orientations are removed; for example, a cube has only one unique orientation.

Overlap is checked using axis-aligned bounding boxes (AABB). Two packages overlap only when their interiors intersect on all three axes. Packages may touch at a face, edge, or corner.

## Behaviour and assumptions

- **Multiple packages per box:** Allowed, provided there is no geometric overlap and the combined weight does not exceed the box's maximum weight.
- **Rotation:** All six orthogonal orientations are permitted. There is no “this side up” restriction.
- **Exact fit:** A package may exactly match a box boundary.
- **Touching:** Touching faces, edges, or corners are allowed.
- **Gravity and support:** No gravity, stability, or load-bearing support simulation is performed. A package may overhang another package or be placed above an unsupported space, as long as it remains inside the outer box boundaries and does not intersect another package.
- **Duplicate IDs within a request:** The first occurrence is considered; subsequent occurrences are skipped and reported.
- **Duplicate IDs across requests:** IDs successfully packed by earlier requests are skipped in later requests handled by the same service process.
- **Unpackable packages:** These are reported separately. Their IDs are not registered as processed, so a caller can correct the package dimensions or weight and retry using the same ID.
- **Partial success:** A request may return HTTP 200 with valid packages packed and un-packable package IDs reported. `boxes_required` counts only boxes used for newly packed packages.
- **Validation:** Missing fields, unknown fields, non-integer IDs, and non-positive dimensions or weights cause HTTP 422. The request payload is rejected rather than silently accepting malformed package entries.

## Duplicate tracking and state limitations

Processed package IDs are stored in an in-memory Python `set`, protected by a `threading.Lock`. The lock keeps the check-and-update operation safe when multiple requests are handled concurrently by the same application process.

This is intentionally a lightweight implementation for the assignment. In-memory state has important limitations:

- IDs are forgotten when the application process restarts.
- Separate Uvicorn worker processes do not share the same set.
- Multiple application instances do not share the same set.

For a multi-worker or multi-instance production deployment, duplicate tracking should be moved to shared storage, such as Redis using an atomic operation (for example, `SETNX`) or a database with a unique constraint. The shared-state update should be atomic with the operation that records successful processing.

## Error handling

Invalid request data returns HTTP 422 with a consistent error envelope. For example:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Request payload failed validation.",
    "details": []
  }
}
```

The `details` array contains Pydantic validation information for the invalid fields. Unpackable packages are not treated as malformed input; they are reported in `unpackable_package_ids` in the HTTP 200 packing response.

## Running tests

Run the test suite from the project root:

```bash
pytest -v
```

The tests cover:

- Unique package orientations, including cubes and cuboids.
- Exact boundary fits and out-of-bounds placements.
- Overlap detection and permitted touching.
- Successful packing and rotation.
- Weight limits and packages that cannot fit.
- Packing invariants: no overlap, within bounds, and within weight capacity.
- Duplicate IDs within and across requests.
- Retry behaviour for IDs that were previously unpackable.
- Health endpoint, packing endpoint, optional details, empty input, and validation errors.

## Docker (optional)

If the repository includes the Dockerfile and `.dockerignore`, build and run the service with:

```bash
docker build -t box-packing-service:latest .
docker run -d --name box-packer -p 8000:8000 box-packing-service:latest
```

Verify the container health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

The provided container configuration uses one Uvicorn worker because duplicate-ID state is held in process memory. Increasing the worker count would create separate, inconsistent in-memory ID sets.

## Algorithm limitations and possible improvements

The heuristic is designed to be understandable, deterministic, and practical for the assignment. It does **not** guarantee the minimum possible number of boxes or the densest possible packing.

- Extreme-point placement considers generated candidate corners; it can miss feasible positions that are not adjacent to those points.
- Greedy ordering and first-fit placement can make an early choice that prevents a better later arrangement.
- The current largest-eligible-box policy does not minimize shipping cost or box volume.
- No gravity, support, fragility, or load-bearing constraints are modelled.

Possible future improvements include more advanced free-space methods such as Guillotine or MaxRects-style splitting, a search or optimization pass, cost-aware box selection, and shared persistent duplicate tracking.


## Design summary

The service separates the HTTP layer, request validation, domain models, geometry, packing algorithm, and request-level state management. This keeps the core packing logic independent of FastAPI while making the API contract and the heuristic straightforward to test.
