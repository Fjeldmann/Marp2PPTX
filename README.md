### Marp PPTX Post-Processing: Status & Next Steps

#### 1. Marp HTML Structure (Key Concepts)

**Slides:**
- Each slide is represented by a `<svg data-marpit-svg ...>` element.
- Inside each SVG, there are one or more layers, each as a `<foreignObject>` with width/height attributes.
- Each `<foreignObject>` contains a `<section>` element, which holds the content for that layer.

**Headers:**
- If a slide has a header, a `<header>` element is placed under the `<section>` element.
- Split background images are never placed in the header.

**Marpit Advanced Backgrounds:**
- Advanced backgrounds (true and split) are always placed in a `<div data-marpit-advanced-background-container="true">`.
- This div can contain one or more `<figure>` elements, each with a background image.
- The direction (horizontal/vertical) is set by `data-marpit-advanced-background-direction`.
- Split backgrounds are indicated by attributes like `data-marpit-advanced-background-split` on the `<section>`.

#### 2. What We're Trying to Achieve

We want to post-process a Marp-exported PowerPoint (`.pptx`) so that all background images specified with Marp’s advanced image syntax are visually correct in the exported `.pptx`. This includes:

- **True backgrounds** (`![bg](...)`): Fill the slide, appear behind content, and match Marp’s CSS background-size/position logic (cover, contain, auto, etc.).
- **Multiple backgrounds** (`![bg](...)` x N, with `horizontal`/`vertical`): Stack images in the correct order and direction, matching Marp’s advanced backgrounds.
   - **Split backgrounds** (`![bg left]`, `![bg right]`, `![bg left:33%]`, etc.): Place the image as a foreground element in a defined region (not as a slide-wide background), shrinking the content area as Marp does. Only `left` and `right` split directions are supported (not `top` or `bottom`).
- **Cropping and placement**: All cropping, scaling, and placement (e.g., `right:35%`, `left:38% 70%`, `w:100% h:50%`) should visually match Marp’s HTML/PDF output.

Reference: [Marpit image syntax documentation](https://marpit.marp.app/image-syntax)

----

#### 3. What We've Done So Far

- **HTML Parsing:**
   - The script parses Marp HTML output, extracting slide backgrounds, split info, image URLs, and layout instructions, by walking the SVG/foreignObject/section/container/figure structure.
   - It builds a slide model for PPTX generation, replacing the old markdown/image logic.

- **True Backgrounds & Multiple Backgrounds:**
   - Images fill the slide or are stacked horizontally/vertically, matching Marp's stacking logic.

- **Advanced Background Scaling:**
   - Implemented full support for Marp's `background-size` property, parsed from the generated HTML.
   - **Supported keywords**: `cover` (fills the area, cropping if necessary), `contain` and `fit` (scales to fit within the area), `auto` (uses original image size), and percentage values (e.g., `50%`, which scales the image relative to the container).

- **Split Backgrounds:**
   - Split backgrounds (left, right, with percentage) are placed in the correct region and cropped to fill only the split space. Only `left` and `right` split directions are supported.
   - Multiple images in a split region are distributed equally within the split space (always horizontally), matching Marp's stacking logic.

- **Debugging and Logging:**
   - Extensive debug logging shows all image shapes, sizes, and the matching process for troubleshooting.

- **Robust Image Mapping**: Refactored the processing logic to map all images from the Marp HTML (including headers, content, and backgrounds) one-to-one with the picture shapes in the PPTX slide. This ensures that transformations are applied *only* to the correct background shapes, preventing unintended modifications to other images on the slide.

----

### 4. CLI & Pipeline Automation

The script has been refactored into a full command-line interface to automate the entire Marp to post-processed PPTX pipeline.

- **End-to-End Automation**: The script now orchestrates the three main steps of the conversion process:
    1.  **HTML Generation**: It calls `npx @marp-team/marp-cli` to convert the source Markdown file into an HTML file.
    2.  **Initial PPTX Generation**: It uses the same CLI tool to create a raw, editable PPTX file (`*_raw.pptx`).
    3.  **Post-Processing**: It runs the existing background image processing logic on the generated HTML and raw PPTX files.
- **File Management**:
    - **Smart Naming**: Automatically creates an intermediate `_raw.pptx` file and saves the final output as `<input_name>.pptx`.
    - **Automatic Cleanup**: Deletes the intermediate HTML and `_raw.pptx` files by default to keep the workspace clean.
    - **Keep Intermediates**: A `--debug` flag is available to prevent cleanup for debugging purposes.
- **Improved Usability**:
    - **CLI Arguments**: The script now uses `argparse` for robust handling of command-line arguments, including the input file, output file, and other options.
    - **Help Documentation**: A `--help` command provides clear instructions on how to use the script and its available options.
    - **Enhanced Typing**: Static typing has been improved throughout the codebase for better maintainability and reliability.

----

### 5. Testing

The new CLI simplifies testing significantly. To process a Marp Markdown file, run the script with the input file path.

Set the name of the Marp markdown file:
```powershell
$MARP_MARKDOWN_FILE = "sample.marp.md"
```

Run the end-to-end processing pipeline with a single command:
```powershell
uv run marp_pptx_postprocess.py ./${MARP_MARKDOWN_FILE}
```

The script will handle the intermediate steps and produce a final, post-processed PPTX file named `sample.marp.pptx`.

To inspect the final output:
```powershell
explorer "${MARP_MARKDOWN_FILE}.pptx"
```

To run the pipeline and keep the intermediate files for debugging:
```powershell
uv run marp_pptx_postprocess.py ./${MARP_MARKDOWN_FILE} --debug
```

This will leave the following files for inspection:
- `${MARP_MARKDOWN_FILE}.html`
- `${MARP_MARKDOWN_FILE}_raw.pptx`
- `${MARP_MARKDOWN_FILE}.pptx` (final output)

----

### 6. Next Steps (Advanced Placement)

#### Recent Progress
- Implemented a fix to widen all text boxes by 4cm (1133 pixels) to prevent unwanted text wrapping in headings when viewed in LibreOffice.
- This adjustment ensures that headings display correctly without wrapping issues.

The next major step is to handle explicit `width` and `height` parameters for background images, which are specified in the markdown but not always available in the final HTML `background-size` property.

- **Parameters to Support:**
    - **Explicit `width` and `height`**: Keywords like `width: 300px` or `h: 50%`.
    - **Shorthand `w` and `h`**: e.g., `w:300px`.
    - **Positional arguments**: e.g. `![bg 50%]` or `![bg 300px 200px]`. The script will need to parse the original markdown to get these.

- **Goal:** Correctly position and scale images that use these markdown-specific parameters.

- **Content Area Shrinking:**
    - For split backgrounds, shrink the content area as Marp does, so content is not covered by split backgrounds.



----

**Ready for next session: Implement advanced width/height placement logic.**