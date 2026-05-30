"""Create 6x4 flashcards with white backgrounds from logo images."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .teams import (
    Team,
    sorted_teams,
    team_filename_stem,
    split_team_name,
    format_team_name,
    format_filename,
)


def _load_font(font_size: int) -> ImageFont.ImageFont:
    """Load a bold sans-serif font when available, falling back safely."""
    font_candidates = (
        "DejaVuSans-Bold.ttf",
        "arialbd.ttf",
        "Arial Bold.ttf",
        "Arial.ttf",
    )
    for font_name in font_candidates:
        try:
            return ImageFont.truetype(font_name, font_size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def _wrap_words(
    draw: ImageDraw.ImageDraw,
    words: list[str],
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"
        candidate_width, _ = _text_size(draw, candidate, font)
        if candidate_width <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def _apply_logo_filter(logo_rgba: Image.Image, logo_filter: str) -> Image.Image:
    """Apply an optional visual filter to a logo RGBA image."""
    if logo_filter not in ("grayscale", "sepia"):
        return logo_rgba
    r, g, b, a = logo_rgba.split()
    gray = ImageOps.grayscale(Image.merge("RGB", (r, g, b)))
    if logo_filter == "grayscale":
        return Image.merge("RGBA", (gray, gray, gray, a))
    # sepia
    sepia_r = gray.point(lambda px: min(255, int(px * 1.07)))
    sepia_g = gray.point(lambda px: min(255, int(px * 0.74)))
    sepia_b = gray.point(lambda px: min(255, int(px * 0.43)))
    return Image.merge("RGBA", (sepia_r, sepia_g, sepia_b, a))


def _draw_text_with_effect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fill: str,
    font: ImageFont.ImageFont,
    effect: str = "none",
    effect_color: str = "#888888",
) -> None:
    """Draw text with an optional drop shadow or outline effect."""
    x, y = xy
    if effect == "shadow":
        _, h = _text_size(draw, text, font)
        offset = max(2, h // 15)
        draw.text((x + offset, y + offset), text, fill=effect_color, font=font)
    elif effect == "outline":
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), text, fill=effect_color, font=font)
    draw.text(xy, text, fill=fill, font=font)


def _make_layout_context(
    width_px: int,
    height_px: int,
    size_scale: float,
) -> tuple[ImageDraw.ImageDraw, int, int]:
    """Create a throw-away draw context and compute safe text margins.

    Returns (draw, max_width, max_height) where max_height already includes
    the 0.92 safety factor and size_scale.
    """
    canvas = Image.new("RGB", (width_px, height_px), color="white")
    draw = ImageDraw.Draw(canvas)
    margin_h = int(width_px * 0.08)
    margin_v = int(height_px * 0.08)
    max_width = width_px - 2 * margin_h
    max_height = int((height_px - 2 * margin_v) * 0.92 * size_scale)
    return draw, max_width, max_height


def _fit_back_text_layout(
    team_name: str,
    width_px: int,
    height_px: int,
    size_scale: float = 1.0,
) -> tuple[ImageFont.ImageFont, list[str], int]:
    """Fit back text within safe margins: 8% top/bottom = 84% usable height.
    
    Uses conservative 92% safety factor on max_height to prevent overflow.
    size_scale shrinks the allowed height budget so text renders smaller.
    """
    draw, max_width, max_height = _make_layout_context(width_px, height_px, size_scale)
    words = team_name.split()

    def _try_size(font_size: int) -> tuple[ImageFont.ImageFont, list[str], int] | None:
        font = _load_font(font_size)
        lines = _wrap_words(draw, words, font, max_width)
        if len(lines) > 4:
            return None
        spacing = max(6, font_size // 6)
        line_sizes = [_text_size(draw, line, font) for line in lines]
        widest = max((w for w, _ in line_sizes), default=0)
        total_h = sum(h for _, h in line_sizes) + spacing * (len(lines) - 1)
        if widest <= max_width and total_h <= max_height:
            return font, lines, spacing
        return None

    # Coarse pass (step 4) to find approximate fit, then fine pass (step 1).
    start = int(height_px * 0.40)
    coarse = 4
    fit_at: int | None = None
    for fs in range(start, 11, -coarse):
        if _try_size(fs) is not None:
            fit_at = fs
            break
    if fit_at is not None:
        for fs in range(min(start, fit_at + coarse - 1), fit_at - 1, -1):
            result = _try_size(fs)
            if result is not None:
                return result

    fallback_font = _load_font(12)
    return fallback_font, _wrap_words(draw, words, fallback_font, max_width), 6


def _fit_two_block_text_layout(
    first_text: str,
    second_text: str,
    width_px: int,
    height_px: int,
    size_scale: float = 1.0,
) -> tuple[ImageFont.ImageFont, list[str], list[str], int]:
    """Fit two text blocks (location/team) for optional split-color rendering.
    
    Uses conservative 92% safety factor on max_height to prevent overflow.
    size_scale shrinks the allowed height budget so text renders smaller.
    """
    draw, max_width, max_height = _make_layout_context(width_px, height_px, size_scale)
    first_words = first_text.split()
    second_words = second_text.split()

    def _try_size(font_size: int) -> tuple[ImageFont.ImageFont, list[str], list[str], int] | None:
        font = _load_font(font_size)
        first_lines = _wrap_words(draw, first_words, font, max_width)
        second_lines = _wrap_words(draw, second_words, font, max_width)
        if len(first_lines) + len(second_lines) > 8:
            return None
        spacing = max(6, font_size // 6)
        first_sizes = [_text_size(draw, line, font) for line in first_lines]
        second_sizes = [_text_size(draw, line, font) for line in second_lines]
        widest = max(
            [w for w, _ in first_sizes] + [w for w, _ in second_sizes],
            default=0,
        )
        first_h = sum(h for _, h in first_sizes) + spacing * max(0, len(first_lines) - 1)
        second_h = sum(h for _, h in second_sizes) + spacing * max(0, len(second_lines) - 1)
        total_h = first_h + second_h
        if widest <= max_width and total_h <= max_height:
            return font, first_lines, second_lines, spacing
        return None

    # Coarse pass (step 4) to find approximate fit, then fine pass (step 1).
    start = int(height_px * 0.28)
    coarse = 4
    fit_at: int | None = None
    for fs in range(start, 11, -coarse):
        if _try_size(fs) is not None:
            fit_at = fs
            break
    if fit_at is not None:
        for fs in range(min(start, fit_at + coarse - 1), fit_at - 1, -1):
            result = _try_size(fs)
            if result is not None:
                return result

    fallback_font = _load_font(12)
    return (
        fallback_font,
        _wrap_words(draw, first_words, fallback_font, max_width),
        _wrap_words(draw, second_words, fallback_font, max_width),
        6,
    )


def _get_conference_line(team: Team, abbreviate: bool) -> str | None:
    """Return the conference/division display string, or None if no data."""
    conf = team.conference_abbr if abbreviate else team.conference
    if not conf:
        return None
    if team.division:
        return f"{conf} · {team.division}"
    return conf


def _draw_team_text_region(
    draw: ImageDraw.ImageDraw,
    team: Team,
    width_px: int,
    region_height_px: int,
    top_offset_px: int,
    name_format: str,
    split_text_colors: bool,
    location_color: str,
    team_color: str,
    text_color: str = "black",
    text_effect: str = "none",
    text_effect_color: str = "#888888",
    size_scale: float = 1.0,
    show_conference: bool = False,
    abbreviate_conference: bool = False,
    name_order: str = "city_first",
) -> None:
    # Reserve space at the bottom for the conference/division line if needed.
    conf_line = _get_conference_line(team, abbreviate_conference) if show_conference else None
    conf_reserved = int(region_height_px * 0.20) if conf_line else 0
    eff_h = region_height_px - conf_reserved

    back_text = format_team_name(team, name_format, name_order)
    use_split = split_text_colors and name_format == "full"

    if use_split:
        location, team_name = split_team_name(team)
        location = location.strip() if location else ""
        team_name = team_name.strip() if team_name else ""

        if not location or not team_name or location.lower() == team_name.lower():
            use_split = False
        else:
            if name_order == "team_first":
                first_text, first_color = team_name, team_color
                second_text, second_color = location, location_color
            else:
                first_text, first_color = location, location_color
                second_text, second_color = team_name, team_color

    if use_split:
        font, first_lines, second_lines, spacing = _fit_two_block_text_layout(
            first_text,
            second_text,
            width_px,
            eff_h,
            size_scale=size_scale,
        )

        first_sizes = [_text_size(draw, line, font) for line in first_lines]
        second_sizes = [_text_size(draw, line, font) for line in second_lines]

        first_height = sum(h for _, h in first_sizes) + spacing * max(0, len(first_lines) - 1)
        second_height = sum(h for _, h in second_sizes) + spacing * max(0, len(second_lines) - 1)
        total_height = first_height + second_height

        margin_top = int(eff_h * 0.08)
        margin_bottom = int(eff_h * 0.08)
        safe_height = eff_h - margin_top - margin_bottom

        if total_height > safe_height:
            use_split = False
        else:
            y = top_offset_px + margin_top + max(0, (safe_height - total_height) // 2)

        if use_split:
            for line, (line_width, line_height) in zip(first_lines, first_sizes):
                x = (width_px - line_width) // 2
                _draw_text_with_effect(draw, (x, y), line, first_color, font, text_effect, text_effect_color)
                y += line_height + spacing

            for line, (line_width, line_height) in zip(second_lines, second_sizes):
                x = (width_px - line_width) // 2
                _draw_text_with_effect(draw, (x, y), line, second_color, font, text_effect, text_effect_color)
                y += line_height + spacing

    if not use_split:
        font, lines, spacing = _fit_back_text_layout(back_text, width_px, eff_h, size_scale=size_scale)
        line_sizes = [_text_size(draw, line, font) for line in lines]
        total_height = sum(h for _, h in line_sizes) + spacing * (len(lines) - 1)

        margin_top = int(eff_h * 0.08)
        margin_bottom = int(eff_h * 0.08)
        safe_height = eff_h - margin_top - margin_bottom
        y = top_offset_px + margin_top + max(0, (safe_height - total_height) // 2)

        for line, (line_width, line_height) in zip(lines, line_sizes):
            x = (width_px - line_width) // 2
            _draw_text_with_effect(draw, (x, y), line, text_color, font, text_effect, text_effect_color)
            y += line_height + spacing

    # Conference / division line at the bottom of the reserved area.
    if conf_line:
        conf_font, conf_lines, conf_spacing = _fit_back_text_layout(
            conf_line, width_px, conf_reserved, size_scale=1.0
        )
        conf_line_sizes = [_text_size(draw, l, conf_font) for l in conf_lines]
        conf_total_h = (
            sum(h for _, h in conf_line_sizes)
            + conf_spacing * max(0, len(conf_lines) - 1)
        )
        conf_top = top_offset_px + eff_h
        cy = conf_top + max(0, (conf_reserved - conf_total_h) // 2)
        for cl, (clw, clh) in zip(conf_lines, conf_line_sizes):
            cx = (width_px - clw) // 2
            draw.text((cx, cy), cl, fill=text_color, font=conf_font)
            cy += clh + conf_spacing


def _overlay_league_logo(
    card: Image.Image,
    league_logo_path: Path,
    corner: str,
    size_fraction: float = 0.15,
) -> None:
    """Composite a league/conference logo watermark into a corner of the card."""
    card_w, card_h = card.size
    overlay_size = int(min(card_w, card_h) * size_fraction)
    margin = int(min(card_w, card_h) * 0.03)

    try:
        with Image.open(league_logo_path).convert("RGBA") as logo_rgba:
            resized = ImageOps.contain(logo_rgba, (overlay_size, overlay_size))
            w, h = resized.size
            if corner == "top-left":
                x, y = margin, margin
            elif corner == "top-center":
                x, y = (card_w - w) // 2, margin
            elif corner == "top-right":
                x, y = card_w - w - margin, margin
            elif corner == "bottom-left":
                x, y = margin, card_h - h - margin
            elif corner == "bottom-center":
                x, y = (card_w - w) // 2, card_h - h - margin
            else:  # bottom-right
                x, y = card_w - w - margin, card_h - h - margin

            # Reduce opacity for a subtle watermark effect
            r, g, b, a = resized.split()
            a = a.point(lambda i: int(i * 0.65))
            resized = Image.merge("RGBA", (r, g, b, a))
            card.paste(resized, (x, y), resized)
    except Exception:
        pass  # Never let a missing/corrupt league logo crash card generation


def _draw_index_label(
    card: Image.Image,
    index: int,
    total: int,
    width_px: int,
    height_px: int,
    corner: str = "bottom-right",
) -> None:
    """Draw a subtle 'n/total' counter in the specified corner."""
    label = f"{index}/{total}"
    font_size = max(10, int(width_px * 0.016))
    font = _load_font(font_size)
    draw = ImageDraw.Draw(card)
    w, h = _text_size(draw, label, font)
    padding_x = int(width_px * 0.025)
    padding_y = int(height_px * 0.025)
    if corner == "top-left":
        x, y = padding_x, padding_y
    elif corner == "top-center":
        x, y = (width_px - w) // 2, padding_y
    elif corner == "top-right":
        x, y = width_px - w - padding_x, padding_y
    elif corner == "bottom-left":
        x, y = padding_x, height_px - h - padding_y
    elif corner == "bottom-center":
        x, y = (width_px - w) // 2, height_px - h - padding_y
    else:  # bottom-right
        x, y = width_px - w - padding_x, height_px - h - padding_y
    draw.text((x, y), label, fill="#aaaaaa", font=font)


def _build_logo_card(
    source_logo: Path,
    width_px: int,
    height_px: int,
    bg_color: str = "white",
    logo_filter: str = "none",
    league_logo_path: Path | None = None,
    league_logo_corner: str = "none",
    index_corner: str = "none",
    index: int = 0,
    total: int = 0,
) -> Image.Image:
    card = Image.new("RGB", (width_px, height_px), color=bg_color)
    with Image.open(source_logo).convert("RGBA") as logo_rgba:
        logo_rgba = _apply_logo_filter(logo_rgba, logo_filter)
        max_logo_width = int(width_px * 0.8)
        max_logo_height = int(height_px * 0.8)
        resized_logo = ImageOps.contain(logo_rgba, (max_logo_width, max_logo_height))
        x = (width_px - resized_logo.width) // 2
        y = (height_px - resized_logo.height) // 2
        card.paste(resized_logo, (x, y), resized_logo)
    if league_logo_path and league_logo_corner != "none":
        _overlay_league_logo(card, league_logo_path, league_logo_corner)
    if index_corner != "none" and total > 0:
        _draw_index_label(card, index, total, width_px, height_px, index_corner)
    return card


def _build_text_card(
    team: Team,
    width_px: int,
    height_px: int,
    name_format: str,
    split_text_colors: bool,
    location_color: str,
    team_color: str,
    text_color: str = "black",
    bg_color: str = "white",
    text_effect: str = "none",
    text_effect_color: str = "#888888",
    league_logo_path: Path | None = None,
    league_logo_corner: str = "none",
    text_size: str = "large",
    show_conference: bool = False,
    abbreviate_conference: bool = False,
    index_corner: str = "none",
    index: int = 0,
    total: int = 0,
    name_order: str = "city_first",
) -> Image.Image:
    _TEXT_SIZE_SCALES = {"large": 1.0, "medium": 0.65, "small": 0.45}
    size_scale = _TEXT_SIZE_SCALES.get(text_size, 1.0)
    card = Image.new("RGB", (width_px, height_px), color=bg_color)
    draw = ImageDraw.Draw(card)
    _draw_team_text_region(
        draw,
        team,
        width_px,
        height_px,
        0,
        name_format,
        split_text_colors,
        location_color,
        team_color,
        text_color,
        text_effect=text_effect,
        text_effect_color=text_effect_color,
        size_scale=size_scale,
        show_conference=show_conference,
        abbreviate_conference=abbreviate_conference,
        name_order=name_order,
    )
    if league_logo_path and league_logo_corner != "none":
        _overlay_league_logo(card, league_logo_path, league_logo_corner)
    if index_corner != "none" and total > 0:
        _draw_index_label(card, index, total, width_px, height_px, index_corner)
    return card


def _build_combined_card(
    team: Team,
    source_logo: Path,
    width_px: int,
    height_px: int,
    name_format: str,
    split_text_colors: bool,
    location_color: str,
    team_color: str,
    text_color: str = "black",
    bg_color: str = "white",
    text_effect: str = "none",
    text_effect_color: str = "#888888",
    logo_filter: str = "none",
    league_logo_path: Path | None = None,
    league_logo_corner: str = "none",
    show_conference: bool = False,
    abbreviate_conference: bool = False,
    index_corner: str = "none",
    index: int = 0,
    total: int = 0,
    name_order: str = "city_first",
) -> Image.Image:
    card = Image.new("RGB", (width_px, height_px), color=bg_color)
    draw = ImageDraw.Draw(card)

    top_margin = int(height_px * 0.06)
    logo_region_height = int(height_px * 0.58)
    footer_top = top_margin + logo_region_height + int(height_px * 0.04)
    footer_height = max(int(height_px * 0.24), height_px - footer_top - int(height_px * 0.06))

    with Image.open(source_logo).convert("RGBA") as logo_rgba:
        logo_rgba = _apply_logo_filter(logo_rgba, logo_filter)
        max_logo_width = int(width_px * 0.72)
        max_logo_height = int(logo_region_height * 0.92)
        resized_logo = ImageOps.contain(logo_rgba, (max_logo_width, max_logo_height))
        x = (width_px - resized_logo.width) // 2
        y = top_margin + max(0, (logo_region_height - resized_logo.height) // 2)
        card.paste(resized_logo, (x, y), resized_logo)

    divider_y = footer_top - int(height_px * 0.02)
    draw.line(
        [(int(width_px * 0.12), divider_y), (int(width_px * 0.88), divider_y)],
        fill="#cfcfcf",
        width=max(1, width_px // 600),
    )

    _draw_team_text_region(
        draw,
        team,
        width_px,
        footer_height,
        footer_top,
        name_format,
        split_text_colors,
        location_color,
        team_color,
        text_color,
        text_effect=text_effect,
        text_effect_color=text_effect_color,
        show_conference=show_conference,
        abbreviate_conference=abbreviate_conference,
        name_order=name_order,
    )

    if league_logo_path and league_logo_corner != "none":
        _overlay_league_logo(card, league_logo_path, league_logo_corner)
    if index_corner != "none" and total > 0:
        _draw_index_label(card, index, total, width_px, height_px, index_corner)
    return card


def build_flashcards(
    logos_dir: Path,
    output_dir: Path,
    teams: tuple[Team, ...],
    dpi: int = 300,
    inches: tuple[int, int] = (6, 4),
    filename_format: str = "prefix",
    name_format: str = "full",
    card_types: set[str] | None = None,
    split_text_colors: bool = False,
    location_color: str = "#1f4e79",
    team_color: str = "#b22222",
    text_color: str = "black",
    text_size: str = "large",
    show_conference: bool = False,
    abbreviate_conference: bool = False,
    index_corner: str = "none",
    league_logo_path: Path | None = None,
    league_logo_corner: str = "none",
    bg_color: str = "white",
    text_effect: str = "none",
    text_effect_color: str = "#888888",
    logo_filter: str = "none",
    progress_callback: Callable[[str], None] | None = None,
    name_order: str = "city_first",
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if card_types is None:
        card_types = {"logo", "text"}

    width_px = inches[0] * dpi
    height_px = inches[1] * dpi

    created_cards: list[Path] = []

    ordered_teams = list(sorted_teams(teams))
    total = len(ordered_teams)

    for index, team in enumerate(ordered_teams, start=1):
        if progress_callback:
            progress_callback(f"    Render {index}/{len(ordered_teams)}: {team.name}")
        # Logo is cached using original filename stem
        stem = team_filename_stem(team)
        source_logo = logos_dir / f"{stem}.png"
        if not source_logo.exists():
            raise FileNotFoundError(f"Logo not found: {source_logo}")

        legacy_single_side = output_dir / f"{stem}.png"
        if legacy_single_side.exists():
            legacy_single_side.unlink()

        logo_name, text_name, combo_name = format_filename(
            team,
            filename_format=filename_format,
            name_format=name_format,
            name_order=name_order,
        )

        created_for_team: list[str] = []

        if "logo" in card_types:
            logo_card = _build_logo_card(
                source_logo,
                width_px,
                height_px,
                bg_color=bg_color,
                logo_filter=logo_filter,
                league_logo_path=league_logo_path,
                league_logo_corner=league_logo_corner,
                index_corner=index_corner,
                index=index,
                total=total,
            )
            logo_destination = output_dir / f"{logo_name}.png"
            logo_card.save(logo_destination, dpi=(dpi, dpi), optimize=True)
            created_cards.append(logo_destination)
            created_for_team.append(logo_destination.name)

        if "text" in card_types:
            text_card = _build_text_card(
                team,
                width_px,
                height_px,
                name_format,
                split_text_colors,
                location_color,
                team_color,
                text_color,
                bg_color=bg_color,
                text_effect=text_effect,
                text_effect_color=text_effect_color,
                league_logo_path=league_logo_path,
                league_logo_corner=league_logo_corner,
                text_size=text_size,
                show_conference=show_conference,
                abbreviate_conference=abbreviate_conference,
                index_corner=index_corner,
                index=index,
                total=total,
                name_order=name_order,
            )
            text_destination = output_dir / f"{text_name}.png"
            text_card.save(text_destination, dpi=(dpi, dpi), optimize=True)
            created_cards.append(text_destination)
            created_for_team.append(text_destination.name)

        if "combo" in card_types:
            combined_card = _build_combined_card(
                team,
                source_logo,
                width_px,
                height_px,
                name_format,
                split_text_colors,
                location_color,
                team_color,
                text_color,
                bg_color=bg_color,
                text_effect=text_effect,
                text_effect_color=text_effect_color,
                logo_filter=logo_filter,
                league_logo_path=league_logo_path,
                league_logo_corner=league_logo_corner,
                show_conference=show_conference,
                abbreviate_conference=abbreviate_conference,
                index_corner=index_corner,
                index=index,
                total=total,
                name_order=name_order,
            )
            combined_destination = output_dir / f"{combo_name}.png"
            combined_card.save(combined_destination, dpi=(dpi, dpi), optimize=True)
            created_cards.append(combined_destination)
            created_for_team.append(combined_destination.name)

        if progress_callback and created_for_team:
            progress_callback(f"      Saved cards: {', '.join(created_for_team)}")

    return created_cards


def build_flashcard_pdf(
    output_dir: Path,
    teams: tuple[Team, ...],
    pdf_path: Path,
    card_types: set[str] | None = None,
    filename_format: str = "prefix",
    name_format: str = "full",
    dpi: int = 300,
    progress_callback: Callable[[str], None] | None = None,
) -> Path:
    """Assemble already-generated PNG cards into a single multi-page PDF.

    Pages are ordered: for each team (sorted), each selected card type in the
    order logo → text → combo.  With both 'logo' and 'text' selected this
    produces an interleaved front/back pattern suited to duplex printing.
    """
    if card_types is None:
        card_types = {"logo", "text"}

    ordered_teams = list(sorted_teams(teams))
    images: list[Image.Image] = []

    for team in ordered_teams:
        logo_name, text_name, combo_name = format_filename(
            team, filename_format=filename_format, name_format=name_format
        )
        for card_type, name in (("logo", logo_name), ("text", text_name), ("combo", combo_name)):
            if card_type not in card_types:
                continue
            png_path = output_dir / f"{name}.png"
            if not png_path.exists():
                continue
            images.append(Image.open(png_path).convert("RGB"))

    if not images:
        raise RuntimeError(
            f"No PNG cards found in '{output_dir}' to assemble into PDF. "
            "Generate PNG cards first."
        )

    if progress_callback:
        progress_callback(f"  Building PDF: {len(images)} page(s)...")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        images[0].save(
            pdf_path,
            save_all=True,
            append_images=images[1:],
            resolution=dpi,
        )
    finally:
        for img in images:
            img.close()

    return pdf_path
