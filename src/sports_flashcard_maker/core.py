"""Pure business logic for flashcard generation - zero CLI dependencies."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from .download_logos import download_logos
from .flashcards import build_flashcards, build_flashcard_pdf
from .teams import Team, format_output_filenames, get_flashcard_set


def _write_set_readme(
    readme_path: Path,
    display_name: str,
    set_code: str,
    output_dir: Path,
    teams: tuple[Team, ...],
    dpi: int,
    card_ratio: str,
    filename_format: str,
    name_format: str,
    card_types: set[str],
    split_text_colors: bool,
    location_color: str,
    team_color: str,
    text_color: str,
    text_size: str,
    show_conference: bool,
    abbreviate_conference: bool,
    index_corner: str,
    league_logo_corner: str,
    bg_color: str,
    text_effect: str,
    text_effect_color: str,
    logo_filter: str,
    pdf_output: bool,
    warnings: list[str],
) -> None:
    team_lines: list[str] = []
    file_lines: list[str] = []

    for team in teams:
        output_names = format_output_filenames(
            team,
            filename_format=filename_format,
            name_format=name_format,
            card_types=card_types,
        )
        team_lines.append(f"- {team.name}")
        for output_name in output_names:
            team_lines.append(f"  - {output_name}.png")
            file_lines.append(f"- {output_name}.png")

    warning_lines = [f"- {warning}" for warning in warnings] if warnings else ["- None"]

    readme_content = "\n".join(
        [
            f"# {display_name} Flashcards",
            "",
            "## Summary",
            f"- Set code: `{set_code}`",
            f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- Output folder: `{output_dir.resolve()}`",
            f"- Team count: {len(teams)}",
            f"- Card count: {len(file_lines)}",
            "",
            "## Generation Settings",
            f"- DPI: {dpi}",
            f"- Card ratio: {card_ratio}",
            f"- Filename format: {filename_format}",
            f"- Card types: {', '.join(sorted(card_types))}",
            f"- Name format: {name_format}",
            f"- Split text colors: {'on' if split_text_colors else 'off'}",
            f"- Location color: {location_color}",
            f"- Team color: {team_color}",
            f"- Text color: {text_color}",
            f"- Text size: {text_size}",
            f"- Show conference/division: {'yes' if show_conference else 'no'}",
            f"- Abbreviate conference names: {'yes' if abbreviate_conference else 'no'}",
            f"- Card index corner: {index_corner}",
            f"- League logo overlay: {league_logo_corner}",
            f"- Background color: {bg_color}",
            f"- Text effect: {text_effect}"
            + (f" (color: {text_effect_color})" if text_effect != "none" else ""),
            f"- Logo filter: {logo_filter}",
            f"- PDF output: {'yes' if pdf_output else 'no'}",
            "",
            "## Teams And Created Files",
            *team_lines,
            "",
            "## All Files Created",
            *file_lines,
            "",
            "## Warnings",
            *warning_lines,
            "",
            "## Notes",
            "- Output files per team depend on the selected card output mode.",
            "- File names reflect the selected naming options used during generation.",
        ]
    )

    readme_path.write_text(readme_content + "\n", encoding="utf-8")


def generate_flashcards(
    set_code: str,
    output_dir: Path | str | None = None,
    logos_dir: Path | str | None = None,
    dpi: int = 300,
    card_ratio: str = "3x2",
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
    league_logo_corner: str = "none",
    bg_color: str = "white",
    text_effect: str = "none",
    text_effect_color: str = "#888888",
    logo_filter: str = "none",
    pdf_output: bool = False,
    force_refresh: bool = False,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, object]:
    """
    Generate flashcards for a given set.

    Args:
        set_code: Code of the flashcard set (e.g., "mlb", "nfl", "acc")
        output_dir: Where to save generated flashcards. Defaults to output/{set_folder}/
        logos_dir: Where to download/cache logos. Defaults to data/logos_raw/
        dpi: DPI for saved PNG files. Defaults to 300.
        card_ratio: Flashcard aspect ratio: "1x1", "3x2", or "2x3". Defaults to "3x2".
        filename_format: "prefix" (logo_XXX.png) or "suffix" (XXX_logo.png). Defaults to "prefix".
        name_format: "full" (city+team), "city_only", or "team_only". Defaults to "full".
        card_types: Set of card types to generate: "logo", "text", "combo". Defaults to {"logo", "text"}.
        split_text_colors: When true, render location/team in different colors on back text for full-name mode.
        location_color: Color for location part when split colors are enabled.
        team_color: Color for team part when split colors are enabled.
    
    Returns:
        Dict with:
        - status: "success" or "error"
        - set_code: The requested set code
        - display_name: Human-readable set name
        - team_count: Number of teams processed
        - file_count: Number of PNG files created (team_count * 2 for front+back)
        - output_dir: Full path where files were saved
        - warnings: List of non-fatal warning messages
        - error: Error message (only if status is "error")
    """

    def _ratio_to_inches(ratio: str) -> tuple[int, int]:
        ratio_map: dict[str, tuple[int, int]] = {
            "1x1": (4, 4),
            "3x2": (6, 4),
            "2x3": (4, 6),
            "5x4": (5, 4),
            "4x5": (4, 5),
            "7x5": (7, 5),
            "5x7": (5, 7),
            "8x10": (8, 10),
            "10x8": (10, 8),
        }
        if ratio not in ratio_map:
            raise ValueError(
                "Invalid card_ratio. Choose one of: 1x1, 3x2, 2x3, 5x4, 4x5, 7x5, 5x7, 8x10, 10x8"
            )
        return ratio_map[ratio]

    try:
        # Resolve paths
        logos_dir = Path(logos_dir) if logos_dir else Path("data/logos_raw")
        
        # Load team set configuration
        team_set = get_flashcard_set(set_code)
        output_dir = Path(output_dir) if output_dir else Path("output") / team_set.output_folder
        if progress_callback:
            progress_callback(f"  Preparing set: {team_set.display_name}")
            progress_callback(f"  Output folder: {output_dir}")
        
        # Download logos
        if progress_callback:
            progress_callback("  Resolving teams and downloading logos...")
        downloaded_files, resolved_teams, download_warnings, league_logo_path = download_logos(
            team_set,
            logos_dir,
            progress_callback=progress_callback,
            force_refresh=force_refresh,
        )
        if not resolved_teams:
            raise RuntimeError(f"No teams found for set {team_set.code}.")
        if progress_callback:
            progress_callback(
                f"  Logos ready: {len(downloaded_files)}/{len(resolved_teams)} downloaded or cached"
            )

        card_inches = _ratio_to_inches(card_ratio)
        
        # Generate flashcards
        if progress_callback:
            progress_callback("  Rendering flashcards...")
        created_cards = build_flashcards(
            logos_dir,
            output_dir,
            resolved_teams,
            dpi=dpi,
            inches=card_inches,
            filename_format=filename_format,
            name_format=name_format,
            card_types=card_types,
            split_text_colors=split_text_colors,
            location_color=location_color,
            team_color=team_color,
            text_color=text_color,
            text_size=text_size,
            show_conference=show_conference,
            abbreviate_conference=abbreviate_conference,
            index_corner=index_corner,
            league_logo_path=league_logo_path,
            league_logo_corner=league_logo_corner,
            bg_color=bg_color,
            text_effect=text_effect,
            text_effect_color=text_effect_color,
            logo_filter=logo_filter,
            progress_callback=progress_callback,
        )
        if progress_callback:
            progress_callback(
                f"  Finished set: {team_set.display_name} ({len(resolved_teams)} teams, {len(created_cards)} cards)"
            )

        pdf_path_result: str | None = None
        if pdf_output and created_cards:
            pdf_file = output_dir / f"{set_code}_flashcards.pdf"
            if progress_callback:
                progress_callback(f"  Generating PDF: {pdf_file.name}...")
            build_flashcard_pdf(
                output_dir=output_dir,
                teams=resolved_teams,
                pdf_path=pdf_file,
                card_types=card_types,
                filename_format=filename_format,
                name_format=name_format,
                dpi=dpi,
                progress_callback=progress_callback,
            )
            pdf_path_result = str(pdf_file.resolve())
            if progress_callback:
                progress_callback(f"  PDF saved: {pdf_file.name}")

        duplicate_structured_name_teams = [
            team.name
            for team in resolved_teams
            if team.location_name
            and team.mascot_name
            and team.location_name.strip().lower() == team.mascot_name.strip().lower()
        ]

        warnings: list[str] = list(download_warnings)  # Include download warnings
        if duplicate_structured_name_teams:
            example_names = ", ".join(sorted(duplicate_structured_name_teams)[:3])
            warnings.append(
                "Some teams returned identical location/team fields from the feed. "
                "Used safe single-name fallback for back text. "
                f"Count={len(duplicate_structured_name_teams)}"
                + (f" (examples: {example_names})" if example_names else "")
                + "."
            )

        readme_path = output_dir / "README.md"
        _write_set_readme(
            readme_path=readme_path,
            display_name=team_set.display_name,
            set_code=set_code,
            output_dir=output_dir,
            teams=resolved_teams,
            dpi=dpi,
            card_ratio=card_ratio,
            filename_format=filename_format,
            name_format=name_format,
            card_types=card_types if card_types is not None else {"logo", "text"},
            split_text_colors=split_text_colors,
            location_color=location_color,
            team_color=team_color,
            text_color=text_color,
            text_size=text_size,
            show_conference=show_conference,
            abbreviate_conference=abbreviate_conference,
            index_corner=index_corner,
            league_logo_corner=league_logo_corner,
            bg_color=bg_color,
            text_effect=text_effect,
            text_effect_color=text_effect_color,
            logo_filter=logo_filter,
            pdf_output=pdf_output,
            warnings=warnings,
        )
        if progress_callback:
            progress_callback(f"  Wrote set README: {readme_path.name}")
        
        return {
            "status": "success",
            "set_code": set_code,
            "display_name": team_set.display_name,
            "team_count": len(resolved_teams),
            "file_count": len(created_cards),
            "output_dir": str(output_dir.resolve()),
            "readme_path": str(readme_path.resolve()),
            "pdf_path": pdf_path_result,
            "warnings": warnings,
        }
    
    except Exception as e:
        return {
            "status": "error",
            "set_code": set_code,
            "error": str(e),
        }


def generate_flashcards_batch(
    set_codes: list[str],
    output_dir: Path | str | None = None,
    logos_dir: Path | str | None = None,
    dpi: int = 300,
    card_ratio: str = "3x2",
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
    league_logo_corner: str = "none",
    bg_color: str = "white",
    text_effect: str = "none",
    text_effect_color: str = "#888888",
    logo_filter: str = "none",
    pdf_output: bool = False,
    force_refresh: bool = False,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, object]:
    """Generate flashcards for multiple sets in sequence."""
    normalized_codes = [code.lower() for code in set_codes if code]
    if not normalized_codes:
        return {
            "status": "error",
            "error": "No set codes provided.",
            "results": [],
        }

    # Preserve user order while removing duplicates.
    ordered_unique_codes = list(dict.fromkeys(normalized_codes))
    base_output_dir = Path(output_dir) if output_dir else None

    results: list[dict[str, object]] = []
    success_count = 0
    error_count = 0

    total_sets = len(ordered_unique_codes)

    for index, code in enumerate(ordered_unique_codes, start=1):
        set_output_dir: Path | None = None
        set_info = get_flashcard_set(code)
        if base_output_dir:
            set_output_dir = base_output_dir / set_info.output_folder

        if progress_callback:
            progress_callback("")
            progress_callback(f"[{index}/{total_sets}] Starting set: {set_info.display_name}")

        result = generate_flashcards(
            set_code=code,
            output_dir=set_output_dir,
            logos_dir=logos_dir,
            dpi=dpi,
            card_ratio=card_ratio,
            filename_format=filename_format,
            name_format=name_format,
            card_types=card_types,
            split_text_colors=split_text_colors,
            location_color=location_color,
            team_color=team_color,
            text_color=text_color,
            text_size=text_size,
            show_conference=show_conference,
            abbreviate_conference=abbreviate_conference,
            index_corner=index_corner,
            league_logo_corner=league_logo_corner,
            bg_color=bg_color,
            text_effect=text_effect,
            text_effect_color=text_effect_color,
            logo_filter=logo_filter,
            pdf_output=pdf_output,
            force_refresh=force_refresh,
            progress_callback=progress_callback,
        )
        results.append(result)

        if result.get("status") == "success":
            success_count += 1
            if progress_callback:
                progress_callback(
                    f"[{index}/{total_sets}] Completed set: {set_info.display_name}"
                )
        else:
            error_count += 1
            if progress_callback:
                progress_callback(
                    f"[{index}/{total_sets}] Failed set: {set_info.display_name}"
                )

    return {
        "status": "success" if error_count == 0 else "partial" if success_count > 0 else "error",
        "results": results,
        "set_count": len(ordered_unique_codes),
        "success_count": success_count,
        "error_count": error_count,
        "warnings": [
            f"{item.get('display_name', item.get('set_code', 'unknown'))}: {warning}"
            for item in results
            for warning in item.get("warnings", [])
        ],
    }
