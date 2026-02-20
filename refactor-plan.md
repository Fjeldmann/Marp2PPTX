# Revised Refactor Plan for marp_pptx_postprocess.py (Single File)

## Goals
- Improve readability and maintainability with minimal changes.
- Add basic type hints and structured comments.
- Extract helper functions for clarity.
- Keep the core structure intact to avoid breaking existing logic.
- Implement minimal tests on critical functions (e.g., parse and render).

## Step-by-step plan (minimal, single-file)

### ✅ 1. Add type hints and docstrings (done)
- `parse_marp_html` and `process_pptx_html` are annotated and documented.
- `render_div_as_image` was given a module-level docstring and type hints.

### ✅ 2. Extract small helper (targeted)
- Instead of large module splits, `render_div_as_image` was lifted to module level
  (now testable) and smaller helper logic is scoped to where it's used.

### ✅ 3. Remove global variables (`SLIDE_WIDTH`, `SLIDE_HEIGHT`) (done)
- Replaced with local `slide_width` / `slide_height` variables inside
  `process_pptx_html` to remove hidden module state.

### ✅ 4. Basic error handling and logging (done)
- Uses `logging` throughout; critical sections already wrapped with try/except
  where appropriate.

### ✅ 5. Minimal tests (done)
- Added `tests/test_marp_postprocess.py` covering:
  - `parse_marp_html` parsing of background/content
  - `render_div_as_image` image download + render (requests is monkeypatched)

### ✅ 6. Keep the script as a single file (kept)
- No new modules were introduced — all improvements kept inside
  `marp_pptx_postprocess.py` for minimal disruption.

### 7. Follow-ups (small, non-blocking)
- [x] Remove duplicate/nested `render_div_as_image` (done).
- [ ] Add a dev dependency entry for `pytest` and optionally `ruff`/`mypy`.
- [ ] Run `ruff`/`black` and a single `ty check` — low-risk formatting/types pass.

---

# Quick status
- Completed: small, high-impact refactor (no module split).
- Added: module-level `render_div_as_image` + minimal pytest coverage.
- Next: tidy duplicate nested helper (optional) and add CI/dev deps if you want.

Would you like me to (pick one):
- [x] remove the nested `render_div_as_image` now (done),
- [x] add `pytest` to dev dependencies and a simple GitHub Actions job,
- [ ] run formatting/type checks and fix any remaining issues?

---

# Summary
- Focus on small, incremental improvements.
- Keep the script simple and functional.
- Add minimal, targeted tests.
- Avoid overengineering at this stage.

Would you like me to generate specific code snippets for any of these steps now?