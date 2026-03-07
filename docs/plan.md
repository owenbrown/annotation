# Plan: Annotation Tool Proof of Concept

## Context

We're building a single-page annotation tool at `app/tool.html` that loads data from the FastAPI backend at `http://127.0.0.1:8000/`.

## Key Decision: Build From Scratch Using LSF Patterns (Not Embed LSF)

**Why not embed the actual LSF bundle:**
- No pre-built bundle exists in the repo. Building requires the full Nx monorepo toolchain (hundreds of npm deps, SCSS compilation, webpack, custom humansignal packages).
- LSF is 148K lines across 691 files. Even a "minimal" build pulls in MobX State Tree, Konva.js, Ant Design, and 30+ region types for modalities we don't need (audio, video, text, time series).
- Our end goal is zero third-party dependencies. Starting with a 148K-line framework and stripping it down is backwards — we'd remove more than we keep.
- LSF's XML config system is something we explicitly want to replace with JavaScript.

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

1. [x] Loads the kroger.jpg receipt image
2. [x] Fetches annotations from `GET /`
3. [x] Renders polygon overlays on the image using SVG
4. [x] Distinguishes pre-annotations (dashed outline) from current annotations (solid outline)
5. [x] Shows a sidebar with the annotation fields and values
6. [x] Lets the user click a polygon to select it and see/edit its attributes
7. [x] Lets the user edit the text value in the sidebar
8. [x] Has a Save button that POSTs updated annotations to `POST /`
9. [x] Basic zoom/pan on the image

**Ask Owen to test after this phase.**

### Phase 2: Strip & Modernize (already clean if Phase 1 is built from scratch)
- Verify: zero `<script src="...">` to external CDNs
- Verify: zero `@import url(...)` to external CSS
- All JS is inline or in `<script type="module">` blocks
- All CSS uses modern features (custom properties, grid, container queries, :has())
- No React, no MUI, no Ant Design — vanilla JS with DOM APIs

### Phase 3: Replace XML With JavaScript
- Already done if Phase 1 uses JS objects for config
- Annotation schema defined as a JS object, not XML
- Field definitions (name, type, allowed values) are plain JS

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

## Questions for Owen

1. **Image serving**: Should the FastAPI app serve kroger.jpg as a static file (e.g., `/static/kroger.jpg`), or should it be a dedicated endpoint like `GET /image`? I'll default to static file serving.

2. **Coordinates**: The dummy annotation coordinates are very small (e.g., `[1.0, 2.0]`). Are these pixel coordinates, or normalized 0-1 coordinates, or percentage coordinates? For a receipt image that's likely 1000+ pixels tall, coordinates like `(1, 2)` to `(8, 5)` would be tiny pixel boxes in the top-left corner. Should I treat them as percentages (0-100 scale) for the proof of concept, or would you prefer I update the dummy data to match the actual Kroger logo position on the receipt?

3. **Polygon editing**: For the POC, should clicking a polygon let you edit only the text value, or also drag the polygon vertices? I'll start with text editing only and add vertex dragging as a follow-up.

4. **Multiple annotations on the same field**: The dummy data has two annotations for `vendor_name` — one current (`kroger`) and one pre-annotation (`KROKER`). Should the sidebar show both side-by-side (current vs pre-annotation), or show the current value with a "show pre-annotation" toggle?
