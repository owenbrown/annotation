from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Annotation(BaseModel):
    polygon_vertices: list[tuple[float, float]]
    field_name: str
    value: str
    is_preannotation: bool


class AnnotationsResponse(BaseModel):
    annotations: list[Annotation]


DUMMY_ANNOTATIONS: list[Annotation] = [
    Annotation(
        polygon_vertices=[(1, 2), (1, 5), (8, 5), (8, 2)],
        field_name="vendor_name",
        value="kroger",
        is_preannotation=False,
    ),
    Annotation(
        polygon_vertices=[(2, 2), (2, 5), (8, 5), (8, 2)],
        field_name="vendor_name",
        value="KROKER",
        is_preannotation=True,
    ),
]


@app.get("/")
def get_annotations() -> AnnotationsResponse:
    return AnnotationsResponse(annotations=DUMMY_ANNOTATIONS)


@app.post("/", status_code=200)
def post_annotations(body: AnnotationsResponse) -> dict:
    return {"status": "ok", "count": len(body.annotations)}
