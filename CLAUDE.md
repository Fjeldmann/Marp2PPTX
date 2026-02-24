# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install for development
uv sync --dev
uv pip install -e .

# Run the tool
marp2pptx convert example.marp.md --open-pptx
marp2pptx convert example.marp.md --debug      # keeps intermediate files
marp2pptx convert example.marp.md --experimental  # enables styled-div rendering

# Lint
uv run ruff check .
uv run ruff format .

# Type check
uv run ty check

# Run tests
pytest

# Build and publish
uv build
uv publish --token $PYPI_TOKEN
```

## Architecture

The conversion pipeline has four stages, orchestrated in `marp2pptx/__main__.py`:

1. **Preprocessing** (`preprocessing.py`): Strips invisible Unicode characters (U+200B etc.) from the Markdown source that would cause Marp to produce split text boxes. Writes a temporary `*.preprocessed.marp.md` file.

2. **Marp CLI generation** (`marp_convert.py`): Calls `npx @marp-team/marp-cli@latest` twice in parallel via `ThreadPoolExecutor` — once for HTML output (used as a reference for post-processing) and once for the raw editable PPTX (via `--pptx-editable`, which requires LibreOffice).

3. **Post-processing** (`postprocessing.py`): The largest module. Opens the raw PPTX with `python-pptx` and applies a sequence of fixes using the HTML as a reference:
   - `parse_marp_html` — parses slide data (background images, styled divs) from the Marp HTML using BeautifulSoup.
   - `process_native_marp_images` — corrects background image sizing/positioning using Marp's `![bg ...]` syntax data extracted from the HTML.
   - `widen_text_shapes` — adds extra width to text boxes to prevent wrapping mismatches across viewers.
   - `merge_multiline_textboxes` — reunifies text boxes that LibreOffice split from a single wrapped sentence.
   - `improve_bullet_points` — fixes bullet point rendering using HTML as reference.
   - `process_styled_divs` (experimental, opt-in via `--experimental`) — renders custom HTML `<div>` elements with CSS (rounded portraits, object-fit, background-image) as PNG images and replaces corresponding PPTX shapes.
   - `normalize_font_names` — maps mismatched font names (e.g. `SegoeUI` → `Segoe UI`).
   - `remove_redundant_marp_white_rectangles` — removes the three full-slide white rectangles Marp/LibreOffice injects behind every slide.

4. **Cleanup**: Intermediate files (preprocessed MD, HTML, raw PPTX) are deleted unless `--debug` is passed.

**`render_div_as_image.py`** is the rendering engine for styled divs. It uses Pillow to composite images with `object-fit`/`object-position`/`border-radius`/`transform: scale(...)` CSS semantics, outputting a PNG to a temp file.

## Key dependencies

| Package | Role |
|---|---|
| `python-pptx` | Read/write PPTX files |
| `beautifulsoup4` | Parse Marp-generated HTML |
| `Pillow` | Render styled divs as PNG images |
| `pydantic` | Validate image URLs in `render_div_as_image` |
| `requests` | Download remote images for div rendering |
| `npx` / Marp CLI | External — must be in PATH |
| LibreOffice | External — required by Marp CLI for `--pptx-editable` |

## Intermediate file naming

For an input `example.marp.md`, the pipeline creates:
- `example.marp.md-m2p.preprocessed.marp.md` — cleaned Markdown
- `example.marp.md-m2p.html` — Marp HTML reference
- `example.marp.md-m2p_raw.pptx` — raw PPTX from LibreOffice
- `example.marp.md-m2p.pptx` — final output (always kept)

## Notes

- The `--experimental` flag is required to enable `process_styled_divs`; it is off by default because it can fail silently on unsupported CSS patterns.
- On Windows, `npx.cmd` is used explicitly instead of `npx` for PATH resolution.
- The `resources/` directory contains sample `.marp.md` files for manual testing.
- `pytest` tests live in `tests/`; the test module is currently mostly empty — new features should be tested there.
