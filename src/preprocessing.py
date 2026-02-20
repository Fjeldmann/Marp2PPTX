"""Preprocessing functions for Marp Markdown files before conversion."""

import logging
import re
from pathlib import Path

# Module logger
logger = logging.getLogger(__name__)


def remove_invisible_characters(content: str) -> str:
    """
    Remove invisible Unicode characters from Markdown content.

    **Issue Solved:**
    When converting Marp Markdown to PPTX, invisible characters (particularly U+200B
    zero-width space) can cause text to be unexpectedly split into multiple textboxes
    in the output presentation.

    Example Problem:
        Input: "**01** Økonomi​ og estimat​er for forbrug"
        (contains U+200B after "Økonomi" and "estimat")

        Without preprocessing:
        - Renders as 3 separate textboxes instead of 1:
          1. "01 Økonomi "
          2. " og estimat "
          3. "er for forbrug"

        With preprocessing:
        - Renders as 1 textbox: "**01** Økonomi og estimater for forbrug"

    This function removes common invisible Unicode characters that can cause rendering
    issues, including:
    - U+200B ZERO WIDTH SPACE
    - U+200C ZERO WIDTH NON-JOINER
    - U+200D ZERO WIDTH JOINER
    - U+FEFF ZERO WIDTH NO-BREAK SPACE
    - U+200E LEFT-TO-RIGHT MARK
    - U+200F RIGHT-TO-LEFT MARK

    Args:
        content: The Markdown content as a string.

    Returns:
        The content with invisible characters removed.
    """
    # Pattern to match common invisible Unicode characters
    invisible_chars_pattern = r'[\u200B\u200C\u200D\uFEFF\u200E\u200F]'

    cleaned_content = re.sub(invisible_chars_pattern, '', content)

    return cleaned_content


def preprocess_markdown(input_path: Path, output_path: Path) -> None:
    """
    Preprocess a Markdown file by removing invisible characters.

    Args:
        input_path: Path to the input Markdown file.
        output_path: Path to the output preprocessed Markdown file.

    Returns:
        None

    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read the input file
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read input file {input_path}: {e}")
        raise

    # Apply preprocessing
    cleaned_content = remove_invisible_characters(content)

    # Write the preprocessed content
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
    except Exception as e:
        logger.error(f"Failed to write preprocessed file {output_path}: {e}")
        raise

    logger.debug(f"Preprocessed Markdown file: {input_path} -> {output_path}")
