"""Pure business logic for flashcard generation - zero CLI dependencies."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from .download_logos import download_logos
from .flashcards import build_flashcards
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
    side_labels: str,
    name_format: str,
    name_order: str,
    card_output_mode: str,
    split_text_colors: bool,
    location_color: str,
    team_color: str,
    warnings: list[str],
) -> None:
    team_lines: list[str] = []
    file_lines: list[str] = []

    for team in teams:
        output_names = format_output_filenames(
            team,
            filename_format=filename_format,
            name_format=name_format,
            name_order=name_order,
            side_labels=side_labels,
            card_output_mode=card_output_mode,
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
            f"- Side labels: {side_labels}",
            f"- Card output mode: {card_output_mode}",
            f"- Name format: {name_format}",
            f"- Name order: {name_order}",
            f"- Split text colors: {'on' if split_text_colors else 'off'}",
            f"- Location color: {location_color}",
            f"- Team color: {team_color}",
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
    side_labels: str = "front_back",
    name_format: str = "full",
    name_order: str = "city_first",
    card_output_mode: str = "logo_text",
    split_text_colors: bool = False,
    location_color: str = "#1f4e79",
    team_color: str = "#b22222",
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
        filename_format: "prefix" (front_XXX.png) or "suffix" (XXX_front.png). Defaults to "prefix".
        side_labels: Filename side labels: "front_back" or "logo_text". Defaults to "front_back".
        name_format: "full" (city+team), "city_only", or "team_only". Defaults to "full".
        name_order: "city_first" or "team_first" (only used for "full"). Defaults to "city_first".
        card_output_mode: "logo_text", "logo_only", "text_only", or "combined".
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
        downloaded_files, resolved_teams, download_warnings = download_logos(
            team_set,
            logos_dir,
            progress_callback=progress_callback,
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
            side_labels=side_labels,
            name_format=name_format,
            name_order=name_order,
            card_output_mode=card_output_mode,
            split_text_colors=split_text_colors,
            location_color=location_color,
            team_color=team_color,
            progress_callback=progress_callback,
        )
        if progress_callback:
            progress_callback(
                f"  Finished set: {team_set.display_name} ({len(resolved_teams)} teams, {len(created_cards)} cards)"
            )

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
            side_labels=side_labels,
            name_format=name_format,
            name_order=name_order,
            card_output_mode=card_output_mode,
            split_text_colors=split_text_colors,
            location_color=location_color,
            team_color=team_color,
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
    side_labels: str = "front_back",
    name_format: str = "full",
    name_order: str = "city_first",
    card_output_mode: str = "logo_text",
    split_text_colors: bool = False,
    location_color: str = "#1f4e79",
    team_color: str = "#b22222",
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
            side_labels=side_labels,
            name_format=name_format,
            name_order=name_order,
            card_output_mode=card_output_mode,
            split_text_colors=split_text_colors,
            location_color=location_color,
            team_color=team_color,
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
