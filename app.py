from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Annotation(BaseModel):
    polygon_vertices: list[tuple[float, float]]
    field_name: str
    value: str
    is_preannotation: bool
    handwriting: bool


class AnnotationsResponse(BaseModel):
    annotations: list[Annotation]


# Coordinates are percentages (0-100) of image width/height
DUMMY_ANNOTATIONS: list[Annotation] = [
    Annotation(
        polygon_vertices=[(25, 3), (25, 10), (75, 10), (75, 3)],
        field_name="vendor_name",
        value="kroger",
        is_preannotation=False,
        handwriting=False,
    ),
    Annotation(
        polygon_vertices=[(20, 3), (20, 10), (80, 10), (80, 3)],
        field_name="vendor_name",
        value="KROKER",
        is_preannotation=True,
        handwriting=False,
    ),
    Annotation(
        polygon_vertices=[(18, 11), (18, 14), (82, 14), (82, 11)],
        field_name="location",
        value="1690 POWDER SPRINGS ROAD",
        is_preannotation=False,
        handwriting=False,
    ),
]


@app.get("/api/annotations")
def get_annotations() -> AnnotationsResponse:
    return AnnotationsResponse(annotations=DUMMY_ANNOTATIONS)


@app.post("/api/annotations", status_code=200)
def post_annotations(body: AnnotationsResponse) -> dict:
    print(f"Received {len(body.annotations)} annotations")
    for a in body.annotations:
        print(f"  {a.field_name}: {a.value} (handwriting={a.handwriting})")
    return {"status": "ok", "count": len(body.annotations)}


# Serve static files (tool.html, kroger.jpg)
# Mount AFTER API routes so /api/* takes priority
app.mount("/", StaticFiles(directory=".", html=True), name="static")
