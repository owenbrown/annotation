# Plan: Annotation Tool Proof of Concept

## Context

We're building a single-page annotation tool at `app/tool.html` that loads data from the FastAPI backend at `http://127.0.0.1:8000/`.

## Key Decision: Build From Scratch Using LSF Patterns (Not Embed LSF)

**Why not embed the actual LSF bundle:**
- No pre-built bundle exists in the repo. Building requires the full Nx monorepo toolchain (hundreds of npm deps, SCSS compilation, webpack, custom humansignal packages).
- LSF is 148K lines across 691 files. Even a "minimal" build pulls in MobX State Tree, Konva.js, Ant Design, and 30+ region types for modalities we don't need (audio, video, text, time series).
- Our end goal is zero third-party dependencies. Starting with a 148K-line framework and stripping it down is backwards — we'd remove more than we keep.
- LSF's XML config system is irrelevant — it defines the annotation UI layout declaratively. We don't need this abstraction. We're building one annotation UI for document images, not a generic framework for arbitrary modalities.

**What we ARE copying from LSF:**
- Event-driven architecture (editor emits events, parent controls data flow)
- Image canvas with shape overlays (SVG on top of image, not Konva)
- Per-region attributes in a sidebar
- Prediction/pre-annotation as separate data from human annotations
- Result array pattern (flat list of results with region IDs)

**What we're copying from other tools:**
- Raw SVG in HTML (annotate-lab) — no canvas library needed for 20-40 shapes
- Normalized coordinates 0-1 (annotate-lab) — resolution-independent
- Handler pattern for draw/edit/select modes (CVAT)
- Delta saves (CVAT) — only POST changes
- Key class color hashing (PPOCRLabel) — field-type visual distinction
- Cache separation of pre-annotation vs human data (PPOCRLabel)

## Architecture

```
app/tool.html          <- Single HTML file, opens in browser
  |
  |-- Fetches GET /       <- Loads annotations JSON from FastAPI
  |-- Posts   POST /      <- Saves annotations JSON to FastAPI
  |-- Loads   /kroger.jpg <- Image served by FastAPI
  |
  |-- Zero third-party JS/CSS dependencies
  |-- Modern HTML/CSS (container queries, :has(), CSS grid, custom properties)
  |-- ES modules in <script type="module"> blocks
```

## TODO

### Phase 1: Working Proof of Concept
Build `app/tool.html` — a single HTML file that:

1. [ ] Loads the kroger.jpg receipt image
2. [ ] Fetches annotations from `GET /`, filters out pre-annotations
3. [ ] Renders polygon overlays on the image using SVG
4. [ ] Shows a sidebar with annotation fields, values, handwriting checkbox
5. [ ] Lets the user click a polygon to select it and highlight it in the sidebar
6. [ ] Lets the user edit the text value and handwriting flag in the sidebar
7. [ ] Lets the user drag polygon vertices to adjust shapes
8. [ ] Lets the user draw NEW polygons (select field type, click to place vertices, close)
9. [ ] Lets the user delete annotations (button in sidebar)
10. [ ] Has a Save button that POSTs annotations to `POST /`
11. [ ] Basic zoom/pan on the image
12. [ ] Field types color-coded: vendor_name, total, total_tax, location

**Ask Owen to test after this phase.**

### Phase 2: Strip & Modernize (already clean if Phase 1 is built from scratch)
- Verify: zero `<script src="...">` to external CDNs
- Verify: zero `@import url(...)` to external CSS
- All JS is inline or in `<script type="module">` blocks
- All CSS uses modern features (custom properties, grid, container queries, :has())
- No React, no MUI, no Ant Design — vanilla JS with DOM APIs

### Phase 3: No XML Anywhere
- LSF uses XML to define annotation UIs declaratively. We don't use this pattern at all.
- Our annotation schema (field names, types, allowed values) will be plain JSON from the API.
- All data exchange is JSON. No XML, no protobuf, no COCO format.

## File Structure

```
app/
  tool.html           <- The annotation page (single file for now)
app.py                <- FastAPI backend (already exists)
kroger.jpg            <- Test image (already exists)
```

## FastAPI Changes Needed

The FastAPI app needs to:
1. Serve static files (tool.html, kroger.jpg) — add `StaticFiles` mount
2. Add CORS headers so tool.html can fetch from the API
3. Keep the existing GET / and POST / endpoints

## Data Flow

```
Browser loads: /static/tool.html
  |
  |--> GET /                    -> { annotations: [...] }
  |--> GET /static/kroger.jpg   -> image bytes
  |
  | User annotates...
  |
  |--> POST /                   -> { annotations: [...] }
       Response: { status: "ok" }
```

## Decisions Made

1. **Image serving**: Serve via FastAPI static files mount. Simple, no extra endpoint needed. Will serve tool.html the same way.

2. **Coordinates**: Use percentage coordinates (0-100) matching Label Studio's convention. Will update dummy data to place annotations over the actual Kroger logo area on the receipt.

3. **Polygon editing**: Vertex dragging is required. Will implement drag handles on polygon vertices.

4. **Pre-annotations**: Don't display for now. Filter them out on the client side.

5. **Per-field attributes**: Each annotation has `handwriting: bool`. The sidebar shows a checkbox for this. The system will eventually support different attribute sets per field type, but for now `handwriting` is on everything.

6. **Creating new annotations**: User can draw new polygons. Available field types: vendor_name, total, total_tax, location. User selects field type, clicks to place vertices, closes polygon.

7. **Deleting annotations**: Yes, delete button in sidebar.

8. **Vertex dragging**: Free sub-pixel positioning. No grid snapping.
