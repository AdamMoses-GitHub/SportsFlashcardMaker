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


def _fit_back_text_layout(
    team_name: str,
    width_px: int,
    height_px: int,
) -> tuple[ImageFont.ImageFont, list[str], int]:
    """Fit back text within safe margins: 8% top/bottom = 84% usable height.
    
    Uses conservative 92% safety factor on max_height to prevent overflow.
    """
    canvas = Image.new("RGB", (width_px, height_px), color="white")
    draw = ImageDraw.Draw(canvas)

    words = team_name.split()
    margin_horizontal = int(width_px * 0.08)
    margin_vertical = int(height_px * 0.08)
    max_width = width_px - (2 * margin_horizontal)  # 84% width
    max_height_base = height_px - (2 * margin_vertical)  # 84% height
    # Apply safety factor: use 92% of max_height to prevent overflow with varied font rendering
    max_height = int(max_height_base * 0.92)

    # Try font sizes with finer stepping for better fit precision
    for font_size in range(int(height_px * 0.40), 11, -1):
        font = _load_font(font_size)
        lines = _wrap_words(draw, words, font, max_width)
        if len(lines) > 4:
            continue

        # Reduce line spacing for longer text to ensure fit within margins
        spacing = max(6, font_size // 6)
        line_sizes = [_text_size(draw, line, font) for line in lines]
        widest_line = max((w for w, _ in line_sizes), default=0)
        total_height = sum(h for _, h in line_sizes) + spacing * (len(lines) - 1)

        if widest_line <= max_width and total_height <= max_height:
            return font, lines, spacing

    # Fallback: use smallest size but respect margins
    fallback_font = _load_font(12)
    return fallback_font, _wrap_words(draw, words, fallback_font, max_width), 6


def _fit_two_block_text_layout(
    first_text: str,
    second_text: str,
    width_px: int,
    height_px: int,
) -> tuple[ImageFont.ImageFont, list[str], list[str], int]:
    """Fit two text blocks (location/team) for optional split-color rendering.
    
    Uses conservative 92% safety factor on max_height to prevent overflow.
    """
    canvas = Image.new("RGB", (width_px, height_px), color="white")
    draw = ImageDraw.Draw(canvas)

    first_words = first_text.split()
    second_words = second_text.split()
    margin_horizontal = int(width_px * 0.08)
    margin_vertical = int(height_px * 0.08)
    max_width = width_px - (2 * margin_horizontal)  # 84% width
    max_height_base = height_px - (2 * margin_vertical)  # 84% height
    # Apply safety factor: use 92% of max_height to prevent overflow with varied font rendering
    max_height = int(max_height_base * 0.92)

    # Try font sizes with finer stepping for better fit precision
    for font_size in range(int(height_px * 0.28), 11, -1):
        font = _load_font(font_size)
        first_lines = _wrap_words(draw, first_words, font, max_width)
        second_lines = _wrap_words(draw, second_words, font, max_width)

        if len(first_lines) + len(second_lines) > 8:
            continue

        # Reduce line spacing for longer text to ensure fit within margins
        spacing = max(6, font_size // 6)
        block_gap = 0

        first_sizes = [_text_size(draw, line, font) for line in first_lines]
        second_sizes = [_text_size(draw, line, font) for line in second_lines]

        widest_line = max(
            [w for w, _ in first_sizes] + [w for w, _ in second_sizes],
            default=0,
        )
        first_height = sum(h for _, h in first_sizes) + spacing * max(0, len(first_lines) - 1)
        second_height = sum(h for _, h in second_sizes) + spacing * max(0, len(second_lines) - 1)
        total_height = first_height + second_height + (block_gap if first_lines and second_lines else 0)

        if widest_line <= max_width and total_height <= max_height:
            return font, first_lines, second_lines, spacing

    fallback_font = _load_font(12)
    return (
        fallback_font,
        _wrap_words(draw, first_words, fallback_font, max_width),
        _wrap_words(draw, second_words, fallback_font, max_width),
        6,
    )


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
) -> None:
    back_text = format_team_name(team, name_format)
    use_split = split_text_colors and name_format == "full"

    if use_split:
        location, team_name = split_team_name(team)
        location = location.strip() if location else ""
        team_name = team_name.strip() if team_name else ""

        if not location or not team_name or location.lower() == team_name.lower():
            use_split = False
        else:
            first_text, first_color = location, location_color
            second_text, second_color = team_name, team_color

    if use_split:
        font, first_lines, second_lines, spacing = _fit_two_block_text_layout(
            first_text,
            second_text,
            width_px,
            region_height_px,
        )

        first_sizes = [_text_size(draw, line, font) for line in first_lines]
        second_sizes = [_text_size(draw, line, font) for line in second_lines]

        first_height = sum(h for _, h in first_sizes) + spacing * max(0, len(first_lines) - 1)
        second_height = sum(h for _, h in second_sizes) + spacing * max(0, len(second_lines) - 1)
        total_height = first_height + second_height

        margin_top = int(region_height_px * 0.08)
        margin_bottom = int(region_height_px * 0.08)
        safe_height = region_height_px - margin_top - margin_bottom

        if total_height > safe_height:
            use_split = False
        else:
            y = top_offset_px + margin_top + max(0, (safe_height - total_height) // 2)

        if use_split:
            for line, (line_width, line_height) in zip(first_lines, first_sizes):
                x = (width_px - line_width) // 2
                draw.text((x, y), line, fill=first_color, font=font)
                y += line_height + spacing

            for line, (line_width, line_height) in zip(second_lines, second_sizes):
                x = (width_px - line_width) // 2
                draw.text((x, y), line, fill=second_color, font=font)
                y += line_height + spacing

    if not use_split:
        font, lines, spacing = _fit_back_text_layout(back_text, width_px, region_height_px)
        line_sizes = [_text_size(draw, line, font) for line in lines]
        total_height = sum(h for _, h in line_sizes) + spacing * (len(lines) - 1)

        margin_top = int(region_height_px * 0.08)
        margin_bottom = int(region_height_px * 0.08)
        safe_height = region_height_px - margin_top - margin_bottom
        y = top_offset_px + margin_top + max(0, (safe_height - total_height) // 2)

        for line, (line_width, line_height) in zip(lines, line_sizes):
            x = (width_px - line_width) // 2
            draw.text((x, y), line, fill=text_color, font=font)
            y += line_height + spacing


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
            elif corner == "top-right":
                x, y = card_w - w - margin, margin
            elif corner == "bottom-left":
                x, y = margin, card_h - h - margin
            else:  # bottom-right
                x, y = card_w - w - margin, card_h - h - margin

            # Reduce opacity for a subtle watermark effect
            r, g, b, a = resized.split()
            a = a.point(lambda i: int(i * 0.65))
            resized = Image.merge("RGBA", (r, g, b, a))
            card.paste(resized, (x, y), resized)
    except Exception:
        pass  # Never let a missing/corrupt league logo crash card generation


def _build_logo_card(source_logo: Path, width_px: int, height_px: int) -> Image.Image:    card = Image.new("RGB", (width_px, height_px), color="white")
    with Image.open(source_logo).convert("RGBA") as logo_rgba:
        max_logo_width = int(width_px * 0.8)
        max_logo_height = int(height_px * 0.8)
        resized_logo = ImageOps.contain(logo_rgba, (max_logo_width, max_logo_height))
        x = (width_px - resized_logo.width) // 2
        y = (height_px - resized_logo.height) // 2
        card.paste(resized_logo, (x, y), resized_logo)
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
    league_logo_path: Path | None = None,
    league_logo_corner: str = "none",
) -> Image.Image:
    card = Image.new("RGB", (width_px, height_px), color="white")
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
    )
    if league_logo_path and league_logo_corner != "none":
        _overlay_league_logo(card, league_logo_path, league_logo_corner)
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
    league_logo_path: Path | None = None,
    league_logo_corner: str = "none",
) -> Image.Image:
    card = Image.new("RGB", (width_px, height_px), color="white")
    draw = ImageDraw.Draw(card)

    top_margin = int(height_px * 0.06)
    logo_region_height = int(height_px * 0.58)
    footer_top = top_margin + logo_region_height + int(height_px * 0.04)
    footer_height = max(int(height_px * 0.24), height_px - footer_top - int(height_px * 0.06))

    with Image.open(source_logo).convert("RGBA") as logo_rgba:
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
    )

    if league_logo_path and league_logo_corner != "none":
        _overlay_league_logo(card, league_logo_path, league_logo_corner)
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
    league_logo_path: Path | None = None,
    league_logo_corner: str = "none",
    progress_callback: Callable[[str], None] | None = None,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if card_types is None:
        card_types = {"logo", "text"}

    width_px = inches[0] * dpi
    height_px = inches[1] * dpi

    created_cards: list[Path] = []

    ordered_teams = list(sorted_teams(teams))

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
        )

        created_for_team: list[str] = []

        if "logo" in card_types:
            logo_card = _build_logo_card(
                source_logo,
                width_px,
                height_px,
                league_logo_path=league_logo_path,
                league_logo_corner=league_logo_corner,
            )
            logo_destination = output_dir / f"{logo_name}.png"
            logo_card.save(logo_destination, dpi=(dpi, dpi))
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
                league_logo_path=league_logo_path,
                league_logo_corner=league_logo_corner,
            )
            text_destination = output_dir / f"{text_name}.png"
            text_card.save(text_destination, dpi=(dpi, dpi))
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
                league_logo_path=league_logo_path,
                league_logo_corner=league_logo_corner,
            )
            combined_destination = output_dir / f"{combo_name}.png"
            combined_card.save(combined_destination, dpi=(dpi, dpi))
            created_cards.append(combined_destination)
            created_for_team.append(combined_destination.name)

        if progress_callback and created_for_team:
            progress_callback(f"      Saved cards: {', '.join(created_for_team)}")

    return created_cards
