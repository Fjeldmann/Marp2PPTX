from PIL import Image, ImageDraw
from bs4 import Tag
from pydantic import HttpUrl, ValidationError


import os
import re
import tempfile
import logging
import requests
import io
from pathlib import Path
from typing import List, Optional


# CSS helper utilities -------------------------------------------------------
logger = logging.getLogger(__name__)

def _css_block_for_class(css: Optional[str], class_name: str) -> Optional[str]:
    """Return the CSS declaration block body for a selector that contains the given class.

    This is intentionally forgiving: it will match simple selectors and selector
    lists that include the class (e.g. ".a, .b { ... }" or "div .classname { ... }").
    """
    if not css:
        return None
    for m in re.finditer(r"([^{]+)\{([^}]+)\}", css):
        selectors = m.group(1)
        body = m.group(2)
        # match any selector in the selector list that contains the class (bounded)
        sel_list = [s.strip() for s in selectors.split(",")]
        for s in sel_list:
            if re.search(rf"(^|[^0-9A-Za-z_-])\.{re.escape(class_name)}($|[^0-9A-Za-z_-])", s):
                return body
    return None


def _extract_css_property(block: Optional[str], prop: str) -> Optional[str]:
    """Return the first occurrence of a CSS property value from a declaration block.

    Example: _extract_css_property('width:100px; height:20px;', 'width') -> '100px'
    """
    if not block:
        return None
    m = re.search(rf"{re.escape(prop)}\s*:\s*([^;]+)", block, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def _download_image(url: str, timeout: int = 10) -> Image.Image:
    """Download image bytes and return a Pillow Image (RGB).

    Raises the underlying exception on failure so callers can decide how to
    handle it.
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    except requests.RequestException:
        logger.debug("_download_image: request failed for %s", url)
        raise
    except Exception:
        logger.debug("_download_image: failed to open image for %s", url)
        raise


def main(
    div_tag: Tag,
    css: Optional[str] = None,
    save_copy_to: Optional[Path] = None,
    slide_index: Optional[int] = None,
    div_index: Optional[int] = None,
) -> Optional[str]:
    """Render a Marp HTML <div> (with an <img> or background-image) to a PNG file.

    This is a module-level helper so unit tests can call it directly. It mirrors the
    implementation used during PPTX post-processing. Returns the PNG path or None on
    failure.
    - Accept `background-image` on the container `div` when no `<img>` is present.
    - Parse inline CSS *and* the `css` blob passed in for `border-radius`,
      `object-fit`, `object-position`, `transform: scale(...)`, and explicit
      `width`/`height` (px).
    - Implement basic `object-fit` semantics for `cover` / `contain` / `none`.

    """
    logger.debug(
        f"Rendering div (slide={slide_index} div={div_index}) class={div_tag.get('class')} [Pillow mode]"
    )

    # Normalise attributes we inspect
    _div_classes_attr = div_tag.get("class")
    div_classes: List[str] = list(_div_classes_attr) if _div_classes_attr else []
    div_style = str(div_tag.get("style") or "")
    img_tag = div_tag.find("img")
    img_style = str(img_tag.get("style") or "") if img_tag else ""

    # --- Determine source image URL (img[src] or div background-image / css class rule)
    src_str = ""
    if img_tag and img_tag.has_attr("src"):
        src_str = str(img_tag.get("src") or "")
    else:
        # Look for inline background-image on the div
        inline_bg = re.search(
            r"background-image:\s*url\((?:['\"]?)(.+?)(?:['\"]?)\)\s*(?=;|$)",
            div_style,
            re.IGNORECASE,
        )
        if inline_bg:
            src_str = inline_bg.group(1)
        else:
            # Try to find a background-image rule in the provided CSS for any class
            if css:
                for class_name in div_classes:
                    body = _css_block_for_class(css, class_name)
                    if not body:
                        continue
                    bg_val = _extract_css_property(body, "background-image")
                    if not bg_val:
                        continue
                    m = re.search(r"url\((?:['\"]?)(.+?)(?:['\"]?)\)", bg_val)
                    if m:
                        src_str = m.group(1)
                        break

    if not src_str:
        logger.warning("  No image source found in <img> or background-image on div")
        return None

    # Validate/resolve source: accept remote HTTP(S) URLs or existing local paths
    is_remote = False
    try:
        HttpUrl(src_str)
        is_remote = True
    except ValidationError:
        # allow plain filesystem paths that exist
        p = Path(src_str)
        if not p.is_file():
            logger.warning(f"  Invalid or unsupported image src: {src_str}")
            return None
        src_str = str(p)

    # Load image (HTTP download for remote URLs, open file for local paths)
    try:
        if is_remote:
            logger.debug(f"  Downloading image: {src_str}")
            img = _download_image(src_str, timeout=10)
        else:
            logger.debug(f"  Loading local image file: {src_str}")
            img = Image.open(src_str).convert("RGB")
        logger.debug(f"  Loaded image: {img.size[0]}x{img.size[1]} px")
    except Exception as e:
        logger.error(f"  Failed to load image '{src_str}': {e}")
        return None

    # --- Compute rendering target size (allow inline/class width/height in px)
    target_w = target_h = 400

    # inline width/height on div (px)
    wh_inline = re.search(r"width:\s*(\d+)px", div_style)
    if wh_inline:
        try:
            target_w = int(wh_inline.group(1))
        except Exception:
            logger.debug("Failed to parse inline width on div style", exc_info=True)
    hh_inline = re.search(r"height:\s*(\d+)px", div_style)
    if hh_inline:
        try:
            target_h = int(hh_inline.group(1))
        except Exception:
            logger.debug("Failed to parse inline height on div style", exc_info=True)

    # class-based width/height in provided global CSS
    if css:
        for class_name in div_classes:
            body = _css_block_for_class(css, class_name)
            if not body:
                continue
            w_val = _extract_css_property(body, "width")
            h_val = _extract_css_property(body, "height")
            try:
                if w_val and w_val.strip().endswith("px"):
                    m = re.match(r"(\d+)", w_val.strip())
                    if m:
                        target_w = int(m.group(1))
                if h_val and h_val.strip().endswith("px"):
                    m2 = re.match(r"(\d+)", h_val.strip())
                    if m2:
                        target_h = int(m2.group(1))
            except Exception:
                logger.debug("Failed to parse width/height from CSS block", exc_info=True)
            break

    # --- Border radius (supports percent and px for the first value)
    border_radius_pct: Optional[float] = None
    border_radius_px: Optional[int] = None
    # inline first
    if div_style:
        br_m = re.search(r"border-radius:\s*([^;]+);?", div_style, re.IGNORECASE)
        if br_m:
            val = br_m.group(1).strip()
            if val.endswith("%"):
                try:
                    border_radius_pct = float(val.rstrip("%"))
                except Exception:
                    pass
            elif val.endswith("px"):
                try:
                    border_radius_px = int(float(val.rstrip("px")))
                except Exception:
                    pass
    # class-based from global css
    if css and border_radius_pct is None and border_radius_px is None:
        for class_name in div_classes:
            body = _css_block_for_class(css, class_name)
            if not body:
                continue
            val = _extract_css_property(body, "border-radius")
            if not val:
                continue
            val = val.strip()
            if val.endswith("%"):
                try:
                    border_radius_pct = float(val.rstrip("%"))
                except Exception:
                    logger.debug("Failed to parse percent border-radius", exc_info=True)
            elif val.endswith("px"):
                try:
                    border_radius_px = int(float(val.rstrip("px")))
                except Exception:
                    logger.debug("Failed to parse px border-radius", exc_info=True)
            break

    # --- transform: scale(...) (look in inline img style first, then css)
    scale_factor = 1.0
    scale_search_space = img_style + "\n" + div_style + "\n" + (css or "")
    scale_match = re.search(r"transform:\s*scale\(([0-9.]+)\)", scale_search_space)
    if scale_match:
        try:
            scale_factor = float(scale_match.group(1))
        except Exception:
            scale_factor = 1.0

    # --- object-fit / object-position parsing (support px and %)
    object_fit = "cover"
    of_m = re.search(r"object-fit:\s*(\w+)", scale_search_space)
    if of_m:
        object_fit = of_m.group(1).lower()

    # default: center (50%/50%)
    obj_pos_x_px: Optional[int] = None
    obj_pos_y_px: Optional[int] = None
    obj_pos_x_pct: Optional[float] = None
    obj_pos_y_pct: Optional[float] = None

    # try percent first
    op_pct = re.search(r"object-position:\s*(-?[0-9.]+)%\s+(-?[0-9.]+)%", scale_search_space)
    if op_pct:
        try:
            obj_pos_x_pct = float(op_pct.group(1))
            obj_pos_y_pct = float(op_pct.group(2))
        except Exception:
            obj_pos_x_pct = obj_pos_y_pct = None
    else:
        op_px = re.search(r"object-position:\s*(-?\d+)px\s+(-?\d+)px", scale_search_space)
        if op_px:
            try:
                obj_pos_x_px = int(op_px.group(1))
                obj_pos_y_px = int(op_px.group(2))
            except Exception:
                obj_pos_x_px = obj_pos_y_px = None

    # --- Apply scale to source image early so object-position px values are meaningful
    if scale_factor != 1.0:
        try:
            new_w = max(1, int(img.width * scale_factor))
            new_h = max(1, int(img.height * scale_factor))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            logger.debug(f"  Scaled source to {new_w}x{new_h} (scale={scale_factor})")
        except Exception:
            logger.debug("render_div_as_image: source scaling failed", exc_info=True)

    # --- Compute inner target area (use 100% for object-fit behaviour)
    target_w_inner = target_w
    target_h_inner = target_h

    # --- Apply object-fit behaviour
    if object_fit == "cover":
        # scale so the image covers the target area, then crop according to object-position
        scale = max(target_w_inner / img.width, target_h_inner / img.height)
        sw = max(1, int(img.width * scale))
        sh = max(1, int(img.height * scale))
        img_resized = img.resize((sw, sh), Image.Resampling.LANCZOS)
        # compute offset from object-position
        if obj_pos_x_pct is not None:
            ox = int((sw - target_w_inner) * (obj_pos_x_pct / 100.0))
        elif obj_pos_x_px is not None:
            ox = obj_pos_x_px
        else:
            ox = (sw - target_w_inner) // 2
        if obj_pos_y_pct is not None:
            oy = int((sh - target_h_inner) * (obj_pos_y_pct / 100.0))
        elif obj_pos_y_px is not None:
            oy = obj_pos_y_px
        else:
            oy = (sh - target_h_inner) // 2
        left = max(0, min(sw - target_w_inner, ox))
        top = max(0, min(sh - target_h_inner, oy))
        img_cropped = img_resized.crop((left, top, left + target_w_inner, top + target_h_inner))
    elif object_fit == "contain":
        scale = min(target_w_inner / img.width, target_h_inner / img.height)
        sw = max(1, int(img.width * scale))
        sh = max(1, int(img.height * scale))
        img_resized = img.resize((sw, sh), Image.Resampling.LANCZOS)
        # paste centered (or positioned) onto transparent canvas
        canvas = Image.new("RGBA", (target_w_inner, target_h_inner), (0, 0, 0, 0))
        if obj_pos_x_pct is not None:
            ox = int((target_w_inner - sw) * (obj_pos_x_pct / 100.0))
        else:
            ox = (target_w_inner - sw) // 2
        if obj_pos_y_pct is not None:
            oy = int((target_h_inner - sh) * (obj_pos_y_pct / 100.0))
        else:
            oy = (target_h_inner - sh) // 2
        canvas.paste(img_resized.convert("RGBA"), (ox, oy))
        img_cropped = canvas.convert("RGBA")
    else:
        # 'none' or unknown: center-crop the source (or use px offsets if provided)
        left = ((img.width - target_w_inner) // 2) + (obj_pos_x_px or 0)
        top = ((img.height - target_h_inner) // 2) + (obj_pos_y_px or 0)
        left = max(0, min(img.width - target_w_inner, left))
        top = max(0, min(img.height - target_h_inner, top))
        img_cropped = img.crop((left, top, left + target_w_inner, top + target_h_inner)).convert("RGBA")

    # Ensure final size
    if img_cropped.size != (target_w, target_h):
        try:
            img_cropped = img_cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
        except Exception:
            logger.debug("render_div_as_image: final resize failed", exc_info=True)

    # --- Apply border-radius mask
    mask = Image.new("L", (target_w, target_h), 0)
    draw = ImageDraw.Draw(mask)

    if border_radius_pct is not None:
        # percent based mask
        if border_radius_pct >= 50:
            draw.ellipse([0, 0, target_w, target_h], fill=255)
        elif border_radius_pct > 0:
            radius_px = int(min(target_w, target_h) * border_radius_pct / 100)
            draw.rounded_rectangle([0, 0, target_w, target_h], radius=radius_px, fill=255)
        else:
            draw.rectangle([0, 0, target_w, target_h], fill=255)
    elif border_radius_px is not None:
        if border_radius_px * 2 >= min(target_w, target_h):
            draw.ellipse([0, 0, target_w, target_h], fill=255)
        elif border_radius_px > 0:
            draw.rounded_rectangle([0, 0, target_w, target_h], radius=border_radius_px, fill=255)
        else:
            draw.rectangle([0, 0, target_w, target_h], fill=255)
    else:
        draw.rectangle([0, 0, target_w, target_h], fill=255)

    # Composite mask into alpha channel
    if img_cropped.mode != "RGBA":
        img_rgba = img_cropped.convert("RGBA")
    else:
        img_rgba = img_cropped
    img_rgba.putalpha(mask)

    png_path = os.path.join(
        tempfile.gettempdir(),
        f"div_render_pillow_{os.getpid()}_{slide_index or 0}_{div_index or 0}.png",
    )
    img_rgba.save(png_path, "PNG")

    if save_copy_to:
        dest_dir = Path(save_copy_to)
        dest_dir.mkdir(parents=True, exist_ok=True)
        copy_path = dest_dir / f"slide-{slide_index}-div-{div_index}.png"
        img_rgba.save(str(copy_path), "PNG")

    return png_path