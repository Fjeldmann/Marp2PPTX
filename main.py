#!/usr/bin/env -S uv run --script

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

from pptx import Presentation

# Import from new modules
from src.marp_convert import (
    get_npx_path,
    marp_generate_in_parallel,
)
from src.preprocessing import (
    preprocess_markdown,
)
from src.postprocessing import (
    parse_marp_html,
    widen_text_shapes,
    normalize_font_names,
    remove_redundant_marp_white_rectangles,
    process_native_marp_images,
    process_styled_divs,
)

# Module logger
logger = logging.getLogger(__name__)


def process_pptx_html(
    html_path: Path,
    pptx_path: Path,
    output_path: Path,
    save_rendered_divs: bool = False,
    run_styled_divs: bool = True,
) -> None:
    """
    Processes a PPTX file using information from a Marp HTML file to fix backgrounds.

    If `save_rendered_divs` is True and `rendered_output_dir` is provided, styled div
    screenshots will be copied there (used when --debug + debug).

    Parameters:
        run_styled_divs: when False, skip the `process_styled_divs` pipeline. This
            allows the CLI to disable the experimental styled-div rendering step.
    """
    slides_data = parse_marp_html(html_path)
    logger.debug("Parsed Marp HTML -> slides_data length: %d", len(slides_data))
    logger.debug("Slides data content presence:")
    for _i, _sd in enumerate(slides_data):
        logger.debug(f"  slide[{_i}] content present: {bool(_sd.get('content'))}")

    # global CSS for styled-div rendering is computed inside `process_styled_divs`.
    # (moved there to reduce the number of arguments passed into the helper.)

    prs = Presentation(str(pptx_path))
    # Handle native Marp image/background sizing (extracted to helper)
    process_native_marp_images(
        prs=prs,
        slides_data=slides_data,
    )
    # Widen text boxes to avoid wrapping issues in some viewers (extracted to helper).
    widen_text_shapes(prs=prs, extra_width_cm=.7)


    # Handle styled HTML <div> elements that contain images. This was extracted to
    # the dedicated pipeline function `process_styled_divs` which fixes a known
    # Marp->PPTX conversion gap for custom HTML/CSS (rounded portraits, object-fit,
    # background-image on divs, inline border-radius, etc.).
    # This behavior is experimental and can be disabled via the CLI flag
    # `--experimental` (disabled by default).
    if run_styled_divs:
        process_styled_divs(
            prs=prs,
            slides_data=slides_data,
            html_path=html_path,
            save_rendered_divs=save_rendered_divs,
        )
    else:
        logger.info("Skipping experimental styled-div rendering (disabled)")

    # Normalize font names (fix known Marp->PPTX mismatches such as 'SegoeUI' -> 'Segoe UI')
    try:
        normalize_font_names(prs)
    except Exception:
        logger.debug("process_pptx_html: normalize_font_names failed", exc_info=True)

    try:
        removed_shapes = remove_redundant_marp_white_rectangles(prs)
        logger.info("Removed %d redundant white rectangle(s)", removed_shapes)
    except Exception:
        logger.debug("process_pptx_html: remove_redundant_marp_white_rectangles failed", exc_info=True)

    # Save the modified presentation
    prs.save(str(output_path))


def main() -> None:
    """
    Main function to run the CLI tool.
    """
    # configure module logging when running as a script (don't configure at import time)
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(
        description="Process a Marp Markdown file to create a polished PPTX.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create the 'convert' subcommand
    convert_parser = subparsers.add_parser(
        "convert",
        help="""Convert a Marp Markdown file to a polished PPTX.
This script automates the pipeline:
1. Preprocess Markdown to remove invisible characters.
2. Convert Markdown to HTML using Marp CLI (runs in parallel with step 3).
3. Convert Markdown to a raw PPTX using Marp CLI (runs in parallel with step 2).
4. Post-process the raw PPTX, using the HTML to fix background image layouts, creating the final PPTX.
5. Clean up intermediate files (preprocessed Markdown, HTML, raw PPTX) unless specified otherwise.
""",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    convert_parser.add_argument(
        "input_file",
        type=str,
        help='Path to the input Marp Markdown file (e.g., "sample.marp.md")',
    )
    convert_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help='Path for the final output PPTX file. Defaults to "<input_file>.pptx" (e.g., "sample.marp.md.pptx").',
    )
    convert_parser.add_argument(
        "--debug",
        action="store_true",
        help="Keep the intermediate HTML and raw PPTX files for debugging.",
    )
    convert_parser.add_argument(
        "--experimental",
        action="store_true",
        help="Enable experimental styled-div rendering (disabled by default).",
    )
    convert_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug logging."
    )
    
    args = parser.parse_args()
    
    # Check if a command was provided
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    input_md_file = Path(args.input_file)
    if not input_md_file.is_file():
        logger.error(f"Input file not found: {input_md_file}")
        sys.exit(1)

    # Define file paths based on user's requirements
    preprocessed_md_path = Path(f"{args.input_file}-m2p.preprocessed.marp.md")
    html_path = Path(f"{args.input_file}-m2p.html")
    raw_pptx_path = Path(f"{args.input_file}-m2p_raw.pptx")
    final_pptx_path = (
        Path(args.output) if args.output else Path(f"{args.input_file}-m2p.pptx")
    )

    # Include output files in cleanup list
    intermediate_files = [preprocessed_md_path, html_path, raw_pptx_path]

    try:
        # --- Step 1: Preprocess Markdown ---
        logger.info("Preprocessing Markdown to remove invisible characters...")
        preprocess_markdown(input_md_file, preprocessed_md_path)
        logger.debug(f"Preprocessed Markdown created: {preprocessed_md_path}")

        # run HTML + raw PPTX generation concurrently to improve throughput
        marp_generate_in_parallel(preprocessed_md_path, html_path, raw_pptx_path)

        # --- Step 3: Post-process the PPTX ---
        logger.info(f"Post-processing raw PPTX to create final file: {final_pptx_path}")

        process_pptx_html(
            Path(html_path),
            Path(raw_pptx_path),
            Path(final_pptx_path),
            save_rendered_divs=args.debug and logger.isEnabledFor(logging.DEBUG),
            run_styled_divs=args.experimental,
        )
        logger.info(f"Successfully created final PPTX: {final_pptx_path}")

    except FileNotFoundError:
        logger.error(
            f"Error: '{get_npx_path()}' command not found. Is Node.js and npm installed and in your PATH?"
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logger.error(f"Marp CLI failed to execute. The command was: {' '.join(e.cmd)}")
        # Stderr is not captured when streaming, so we can't print it here.
        # The error from the subprocess itself should be visible in the console.
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)

    finally:
        # --- Step 4: Cleanup ---
        if not args.debug:
            logger.info("Cleaning up intermediate files...")
            for f in intermediate_files:
                try:
                    if f.is_file():
                        os.remove(f)
                        logger.debug(f"Removed {f}")
                except OSError as e:
                    logger.warning(f"Could not remove intermediate file {f}: {e}")
            logger.info("Cleanup complete.")
        else:
            logger.info("Intermediate files kept as requested.")


if __name__ == "__main__":
    main()

