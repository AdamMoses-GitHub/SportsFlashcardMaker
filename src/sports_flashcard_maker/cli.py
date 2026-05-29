"""CLI interface for flashcard generation - handles user interaction and formatting."""

from __future__ import annotations

import argparse
from pathlib import Path

from .core import generate_flashcards, generate_flashcards_batch
from .teams import FLASHCARD_SETS


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Download team logos and generate print-ready flashcard images."
    )
    parser.add_argument(
        "--set",
        dest="set_codes",
        nargs="+",
        choices=tuple(sorted(FLASHCARD_SETS.keys())),
        default=["mlb"],
        help="One or more flashcard sets to generate.",
    )
    parser.add_argument(
        "--logos-dir",
        type=Path,
        default=Path("data/logos_raw"),
        help="Directory where downloaded logo PNG files are saved.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where generated flashcard images are saved.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI metadata used in saved flashcard PNG files.",
    )
    parser.add_argument(
        "--card-ratio",
        dest="card_ratio",
        choices=["1x1", "3x2", "2x3", "5x4", "4x5", "7x5", "5x7", "8x10", "10x8"],
        default="3x2",
        help="Flashcard ratio: '1x1', '3x2', '2x3', '5x4', '4x5', '7x5', '5x7', '8x10', or '10x8'.",
    )
    parser.add_argument(
        "--filename-format",
        dest="filename_format",
        choices=["prefix", "suffix"],
        default="prefix",
        help="How to format filenames: 'prefix' (CARDTYPE_TEAMTEXT.png) or 'suffix' (TEAMTEXT_CARDTYPE.png).",
    )
    parser.add_argument(
        "--name-format",
        dest="name_format",
        choices=["full", "team_only", "city_only"],
        default="full",
        help="What to include in card text and filenames: 'full' (city+team), 'team_only', or 'city_only'.",
    )
    parser.add_argument(
        "--name-order",
        dest="name_order",
        choices=["city_first", "team_first"],
        default="city_first",
        help="Part order in full-name mode: 'city_first' (default, e.g. 'Boston Red Sox') or 'team_first' (e.g. 'Red Sox Boston').",
    )
    parser.add_argument(
        "--card-types",
        dest="card_types",
        nargs="+",
        choices=["logo", "text", "combo"],
        default=["logo", "text"],
        help="Card types to generate: any combination of 'logo', 'text', 'combo'. Defaults to logo text.",
    )
    parser.add_argument(
        "--text-color",
        dest="text_color",
        default="black",
        help="Text color when split text colors is disabled (hex or named color).",
    )
    parser.add_argument(
        "--text-size",
        dest="text_size",
        choices=["large", "medium", "small"],
        default="large",
        help="Font size for text-only cards: 'large' (default, fills card), 'medium', or 'small'.",
    )
    parser.add_argument(
        "--split-text-colors",
        dest="split_text_colors",
        action="store_true",
        help="Render location and team name in different colors on text cards (full-name mode).",
    )
    parser.add_argument(
        "--location-color",
        dest="location_color",
        default="#1f4e79",
        help="Location text color when --split-text-colors is enabled (hex or named color).",
    )
    parser.add_argument(
        "--team-color",
        dest="team_color",
        default="#b22222",
        help="Team text color when --split-text-colors is enabled (hex or named color).",
    )
    parser.add_argument(
        "--league-logo-corner",
        dest="league_logo_corner",
        choices=["none", "top-left", "top-right", "bottom-left", "bottom-right"],
        default="none",
        help="Overlay the league/conference logo in a corner of every card. Defaults to none (disabled).",
    )
    parser.add_argument(
        "--show-conference",
        dest="show_conference",
        action="store_true",
        default=False,
        help="Show conference/division below the team name on text and combo cards.",
    )
    parser.add_argument(
        "--abbreviate-conference",
        dest="abbreviate_conference",
        action="store_true",
        default=False,
        help="Use abbreviated conference names (e.g. 'AL' instead of 'American League'). Only applies when --show-conference is set.",
    )
    parser.add_argument(
        "--index-corner",
        dest="index_corner",
        choices=["none", "top-left", "top-center", "top-right", "bottom-left", "bottom-center", "bottom-right"],
        default="none",
        help="Print a subtle card index (e.g. '1/18') in the specified corner of every card. Defaults to none (disabled).",
    )
    parser.add_argument(
        "--force-refresh",
        dest="force_refresh",
        action="store_true",
        default=False,
        help="Re-download all logos even if cached copies already exist.",
    )
    return parser.parse_args()


def cli_main() -> None:
    """CLI entry point - parse args and call core business logic."""
    args = parse_args()

    # Single set mode (same output style as before).
    if len(args.set_codes) == 1:
        result = generate_flashcards(
            set_code=args.set_codes[0],
            output_dir=args.output_dir,
            logos_dir=args.logos_dir,
            dpi=args.dpi,
            card_ratio=args.card_ratio,
            filename_format=args.filename_format,
            name_format=args.name_format,
            name_order=args.name_order,
            card_types=set(args.card_types),
            split_text_colors=args.split_text_colors,
            location_color=args.location_color,
            team_color=args.team_color,
            text_color=args.text_color,
            text_size=args.text_size,
            show_conference=args.show_conference,
            abbreviate_conference=args.abbreviate_conference,
            index_corner=args.index_corner,
            league_logo_corner=args.league_logo_corner,
            force_refresh=args.force_refresh,
        )

        if result["status"] == "error":
            print(f"❌ Error: {result['error']}", flush=True)
            return

        print(f"✓ Set: {result['display_name']}")
        print(f"✓ Generated: {result['team_count']} teams ({result['file_count']} cards)")
        print(f"✓ Saved to: {result['output_dir']}")
        return

    # Batch mode for multiple sets.
    batch = generate_flashcards_batch(
        set_codes=args.set_codes,
        output_dir=args.output_dir,
        logos_dir=args.logos_dir,
        dpi=args.dpi,
        card_ratio=args.card_ratio,
        filename_format=args.filename_format,
        name_format=args.name_format,
        name_order=args.name_order,
        card_types=set(args.card_types),
        split_text_colors=args.split_text_colors,
        location_color=args.location_color,
        team_color=args.team_color,
        text_color=args.text_color,
        text_size=args.text_size,
        show_conference=args.show_conference,
        abbreviate_conference=args.abbreviate_conference,
        index_corner=args.index_corner,
        league_logo_corner=args.league_logo_corner,
        force_refresh=args.force_refresh,
    )

    print(
        f"Batch complete: {batch['success_count']}/{batch['set_count']} sets succeeded, "
        f"{batch['error_count']} failed."
    )
    for result in batch["results"]:
        if result.get("status") == "success":
            print(
                f"✓ {result['display_name']}: {result['team_count']} teams "
                f"({result['file_count']} cards) -> {result['output_dir']}"
            )
        else:
            print(f"❌ {result.get('set_code', 'unknown')}: {result.get('error', 'Unknown error')}")
