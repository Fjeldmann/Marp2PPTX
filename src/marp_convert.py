"""Marp conversion functions for parsing HTML and generating PPTX via Marp CLI."""

import logging
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


# On Windows, shutil.which('npx') should find npx.cmd.

# We explicitly use '.cmd' to be certain, which is more robust.
def get_npx_path() -> Optional[Path]:
    npx_executable = "npx.cmd" if sys.platform == "win32" else "npx"
    npx_path = shutil.which(npx_executable)
    if not npx_path:
        logger.error(
            f"Error: '{npx_executable}' command not found. Is Node.js and npm installed and in your PATH?"
        )
        sys.exit(1)
    return Path(npx_path)


def marpcli_generate_html(input_md_file: Path, output_html_file: Path) -> None:
    # --- Step 1: Run Marp CLI for HTML ---
    logger.info(f"Generating intermediate HTML file: {output_html_file}")
    marp_html_command = [
        str(get_npx_path()),
        "@marp-team/marp-cli@latest",
        str(input_md_file),
        "--allow-local-files",
        "--html",
        "-o",
        str(output_html_file),
    ]
    if output_html_file.is_file():
        output_html_file.unlink()
        logger.debug(f"Deleted existing file at {output_html_file} to ensure fresh generation.")
    
    logger.debug("Executing: %s", " ".join(map(str, marp_html_command)))
    subprocess.run(marp_html_command, check=True)
    if not output_html_file.is_file():
        logger.error(f"Expected HTML file was not created: {output_html_file}")
        sys.exit(1)
    logger.info("Successfully created HTML.")


# --- Step 2: Run Marp CLI for raw PPTX ---
def marpcli_generate_raw_pptx(input_md_file: Path, output_pptx_file: Path) -> None:
    logger.info(f"Generating intermediate raw PPTX file: {output_pptx_file}")
    marp_pptx_command = [
        str(get_npx_path()),
        "@marp-team/marp-cli@latest",
        str(input_md_file),
        "--pptx-editable",
        "--allow-local-files",
        "-o",
        str(output_pptx_file),
    ]
    if output_pptx_file.is_file():
        output_pptx_file.unlink()
        logger.debug(f"Deleted existing file at {output_pptx_file} to ensure fresh generation.")
    logger.debug("Executing: %s", " ".join(map(str, marp_pptx_command)))
    subprocess.run(marp_pptx_command, check=True)
    # ensure the raw PPTX was created else throw an error and exit
    if not output_pptx_file.is_file():
        logger.error(f"Expected raw PPTX file was not created: {output_pptx_file}")
        sys.exit(1)
    logger.info("Successfully created raw PPTX.")


def marp_generate_in_parallel(input_md_file: Path, html_path: Path, raw_pptx_path: Path) -> None:
    """Run Marp HTML and raw PPTX generation concurrently (improves performance).

    Both generator functions are started immediately and we wait for both to finish.
    Raises RuntimeError on first failure.
    """
    logger.info("Launching Marp CLI (HTML + PPTX) in parallel...")
    errors = []
    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_map = {
            ex.submit(marpcli_generate_html, input_md_file, html_path): "html",
            ex.submit(marpcli_generate_raw_pptx, input_md_file, raw_pptx_path): "pptx",
        }
        for fut in as_completed(fut_map):
            name = fut_map[fut]
            try:
                fut.result()
                logger.info("Marp %s generation completed", name)
            except Exception as exc:
                logger.error("Marp %s generation failed: %s", name, exc)
                errors.append((name, exc))
    if errors:
        # re-raise the first error for the caller to handle
        raise RuntimeError(f"Marp generation failed: {errors[0][0]}: {errors[0][1]}")
