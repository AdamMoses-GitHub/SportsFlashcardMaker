"""Download team logos for a configured flashcard set."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from .teams import FlashcardSet, Team, normalize_team_name, sorted_teams, team_filename_stem

TIMEOUT_SECONDS = 20


def _fetch_espn_teams(session: requests.Session, endpoint: str) -> list[dict[str, object]]:
    response = session.get(endpoint, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    return payload["sports"][0]["leagues"][0]["teams"]


def _fetch_cfb_team_map(session: requests.Session, endpoint: str) -> dict[str, Team]:
    entries = _fetch_espn_teams(session, endpoint)

    team_map: dict[str, Team] = {}
    for entry in entries:
        team = entry.get("team", {})
        short_name = team.get("shortDisplayName")
        display_name = team.get("displayName") or team.get("location")
        location_name = team.get("location")
        mascot_name = team.get("name")
        logos = team.get("logos") or []
        if not short_name or not display_name or not logos:
            continue
        logo_href = logos[0].get("href")
        if logo_href:
            team_map[str(short_name)] = Team(
                name=normalize_team_name(str(display_name)),
                api_lookup_name=str(short_name),
                logo_slug=str(logo_href),
                location_name=normalize_team_name(str(location_name)) if location_name else None,
                mascot_name=normalize_team_name(str(mascot_name)) if mascot_name else None,
            )

    return team_map


def _fetch_league_teams(session: requests.Session, endpoint: str) -> tuple[Team, ...]:
    entries = _fetch_espn_teams(session, endpoint)
    teams: list[Team] = []

    for entry in entries:
        raw_team = entry.get("team", {})
        display_name = raw_team.get("displayName") or raw_team.get("name") or raw_team.get("shortDisplayName")
        short_name = raw_team.get("shortDisplayName")
        location_name = raw_team.get("location")
        mascot_name = raw_team.get("name")
        logos = raw_team.get("logos") or []
        logo_href = logos[0].get("href") if logos else None
        if display_name and logo_href:
            lookup = str(short_name) if short_name else str(display_name)
            teams.append(
                Team(
                    name=normalize_team_name(str(display_name)),
                    api_lookup_name=lookup,
                    logo_slug=str(logo_href),
                    location_name=normalize_team_name(str(location_name)) if location_name else None,
                    mascot_name=normalize_team_name(str(mascot_name)) if mascot_name else None,
                )
            )

    return tuple(teams)


def download_logos(
    team_set: FlashcardSet,
    output_dir: Path,
    progress_callback: Callable[[str], None] | None = None,
) -> tuple[list[Path], tuple[Team, ...], list[str]]:
    """Download logos and return (downloaded_files, resolved_teams, warnings)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded_files: list[Path] = []
    warnings: list[str] = []
    skipped_teams: list[str] = []

    with requests.Session() as session:
        cfb_team_map: dict[str, Team] | None = None
        resolved_teams: tuple[Team, ...] = team_set.teams

        if team_set.source_mode == "espn_cfb_api":
            if not team_set.source_api_endpoint:
                raise RuntimeError(f"Missing source_api_endpoint for set {team_set.code}.")
            if progress_callback:
                progress_callback("  Fetching conference team data from ESPN...")
            cfb_team_map = _fetch_cfb_team_map(session, team_set.source_api_endpoint)

            # Preserve conference membership but enrich each team with full school+mascot name.
            enriched_teams: list[Team] = []
            for team in team_set.teams:
                if not team.api_lookup_name:
                    raise RuntimeError(
                        f"Missing api_lookup_name for {team.name} in set {team_set.code}."
                    )

                resolved_team = (cfb_team_map or {}).get(team.api_lookup_name)
                if not resolved_team:
                    raise RuntimeError(
                        f"Could not resolve NCAA team '{team.name}' using ESPN API key "
                        f"'{team.api_lookup_name}'."
                    )

                enriched_teams.append(
                    Team(
                        name=resolved_team.name,
                        api_lookup_name=team.api_lookup_name,
                        logo_slug=resolved_team.logo_slug,
                        location_name=resolved_team.location_name,
                        mascot_name=resolved_team.mascot_name,
                    )
                )

            resolved_teams = tuple(enriched_teams)
        elif team_set.source_mode == "espn_league_api_all":
            if not team_set.source_api_endpoint:
                raise RuntimeError(f"Missing source_api_endpoint for set {team_set.code}.")
            if progress_callback:
                progress_callback("  Fetching league teams from ESPN...")
            resolved_teams = _fetch_league_teams(session, team_set.source_api_endpoint)

        ordered_teams = list(sorted_teams(resolved_teams))

        for index, team in enumerate(ordered_teams, start=1):
            try:
                if progress_callback:
                    progress_callback(f"    Logo {index}/{len(ordered_teams)}: {team.name}")
                if team_set.source_mode == "template":
                    if not team_set.source_template or not team.logo_slug:
                        skipped_teams.append(f"{team.name}: missing template configuration")
                        continue
                    logo_url = team_set.source_template.format(slug=team.logo_slug)
                elif team_set.source_mode == "espn_cfb_api":
                    if not team.api_lookup_name or not team.logo_slug:
                        skipped_teams.append(f"{team.name}: missing ESPN API lookup")
                        continue
                    logo_url = team.logo_slug
                elif team_set.source_mode == "espn_league_api_all":
                    if not team.logo_slug:
                        skipped_teams.append(f"{team.name}: missing logo URL")
                        continue
                    logo_url = team.logo_slug
                else:
                    skipped_teams.append(f"{team.name}: unsupported source mode {team_set.source_mode}")
                    continue

                destination = output_dir / f"{team_filename_stem(team)}.png"

                try:
                    response = session.get(logo_url, timeout=TIMEOUT_SECONDS)
                    response.raise_for_status()
                except Timeout:
                    skipped_teams.append(f"{team.name}: network timeout (exceeded {TIMEOUT_SECONDS}s)")
                    continue
                except ConnectionError:
                    skipped_teams.append(f"{team.name}: connection error (check network)")
                    continue
                except RequestException as e:
                    skipped_teams.append(f"{team.name}: network error ({str(e)[:50]})")
                    continue

                destination.write_bytes(response.content)
                downloaded_files.append(destination)
                if progress_callback:
                    progress_callback(f"      Saved logo: {destination.name}")

            except Exception as e:
                skipped_teams.append(f"{team.name}: unexpected error ({str(e)[:50]})")
                continue

        if skipped_teams:
            warnings.append(
                f"Skipped {len(skipped_teams)} teams due to download or configuration errors. "
                f"Examples: {', '.join(skipped_teams[:3])}"
                + (f" (and {len(skipped_teams) - 3} more)" if len(skipped_teams) > 3 else "")
            )

    return downloaded_files, resolved_teams, warnings
