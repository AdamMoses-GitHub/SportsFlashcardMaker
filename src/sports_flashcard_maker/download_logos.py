"""Download team logos for a configured flashcard set."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from .teams import ConferenceEndpoint, FlashcardSet, Team, CONFERENCE_LOOKUP, normalize_team_name, sorted_teams, team_filename_stem

TIMEOUT_SECONDS = 20
_MAX_WORKERS = 8


def _download_one_logo(logo_url: str, destination: Path) -> None:
    """Download one logo to *destination* (thread-safe: creates its own session)."""
    with requests.Session() as session:
        response = session.get(logo_url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
    destination.write_bytes(response.content)


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


def _fetch_cfb_multi_conference(
    conf_endpoints: tuple[ConferenceEndpoint, ...],
    progress_callback: Callable[[str], None] | None = None,
) -> tuple[Team, ...]:
    """Fetch teams from multiple ESPN conference endpoints in parallel; deduplicate by display name."""

    def _fetch_one(ce: ConferenceEndpoint) -> tuple[str, list[Team]]:
        with requests.Session() as s:
            team_map = _fetch_cfb_team_map(s, ce.url)
        tagged = [
            Team(
                name=t.name,
                logo_slug=t.logo_slug,
                api_lookup_name=t.api_lookup_name,
                location_name=t.location_name,
                mascot_name=t.mascot_name,
                conference=ce.conference,
                conference_abbr=ce.conference_abbr,
            )
            for t in team_map.values()
        ]
        return ce.conference, tagged

    teams_by_conf: dict[str, list[Team]] = {}
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=min(len(conf_endpoints), _MAX_WORKERS)) as executor:
        future_to_ce = {executor.submit(_fetch_one, ce): ce for ce in conf_endpoints}
        for future in as_completed(future_to_ce):
            ce = future_to_ce[future]
            try:
                conf_name, teams = future.result()
                teams_by_conf[conf_name] = teams
                if progress_callback:
                    progress_callback(f"    {conf_name}: {len(teams)} teams fetched")
            except Exception as exc:
                errors.append(f"{ce.conference}: {str(exc)[:80]}")

    if errors:
        raise RuntimeError(
            f"Failed to fetch {len(errors)} conference roster(s): {'; '.join(errors)}"
        )

    # Preserve conference order from input; deduplicate by lowercased display name.
    seen: set[str] = set()
    result: list[Team] = []
    for ce in conf_endpoints:
        for team in teams_by_conf.get(ce.conference, []):
            key = team.name.lower()
            if key not in seen:
                seen.add(key)
                result.append(team)
    return tuple(result)


def download_logos(
    team_set: FlashcardSet,
    output_dir: Path,
    progress_callback: Callable[[str], None] | None = None,
    force_refresh: bool = False,
) -> tuple[list[Path], tuple[Team, ...], list[str], Path | None]:
    """Download logos and return (downloaded_files, resolved_teams, warnings)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded_files: list[Path] = []
    warnings: list[str] = []
    skipped_teams: list[str] = []

    with requests.Session() as session:
        cfb_team_map: dict[str, Team] | None = None
        resolved_teams: tuple[Team, ...] = team_set.teams

        if team_set.source_mode == "espn_cfb_api":
            if team_set.teams:
                # Legacy static-roster mode: enrich static teams with live logo URLs.
                if not team_set.source_api_endpoint:
                    raise RuntimeError(f"Missing source_api_endpoint for set {team_set.code}.")
                if progress_callback:
                    progress_callback("  Fetching conference team data from ESPN...")
                cfb_team_map = _fetch_cfb_team_map(session, team_set.source_api_endpoint)

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
                            conference=team.conference,
                            conference_abbr=team.conference_abbr,
                            division=team.division,
                        )
                    )

                resolved_teams = tuple(enriched_teams)

            elif team_set.source_api_endpoints:
                # Dynamic multi-conference mode (e.g. cfb_all): fetch all in parallel.
                if progress_callback:
                    progress_callback(
                        f"  Fetching {len(team_set.source_api_endpoints)} conference roster(s) from ESPN..."
                    )
                resolved_teams = _fetch_cfb_multi_conference(
                    team_set.source_api_endpoints,
                    progress_callback=progress_callback,
                )

            elif team_set.source_api_endpoint:
                # Dynamic single-conference mode: fetch live roster and tag with FlashcardSet defaults.
                if progress_callback:
                    progress_callback("  Fetching dynamic conference roster from ESPN...")
                cfb_team_map = _fetch_cfb_team_map(session, team_set.source_api_endpoint)
                resolved_teams = tuple(
                    Team(
                        name=t.name,
                        logo_slug=t.logo_slug,
                        api_lookup_name=t.api_lookup_name,
                        location_name=t.location_name,
                        mascot_name=t.mascot_name,
                        conference=team_set.default_conference,
                        conference_abbr=team_set.default_conference_abbr,
                    )
                    for t in cfb_team_map.values()
                )

            else:
                raise RuntimeError(
                    f"Set '{team_set.code}' uses espn_cfb_api but has no teams or endpoints configured."
                )
        elif team_set.source_mode == "espn_league_api_all":
            if not team_set.source_api_endpoint:
                raise RuntimeError(f"Missing source_api_endpoint for set {team_set.code}.")
            if progress_callback:
                progress_callback("  Fetching league teams from ESPN...")
            resolved_teams = _fetch_league_teams(session, team_set.source_api_endpoint)
            # Enrich teams with hardcoded conference/division data if available.
            conf_data = CONFERENCE_LOOKUP.get(team_set.code)
            if conf_data:
                enriched: list[Team] = []
                for t in resolved_teams:
                    cd = conf_data.get(t.name.lower())
                    if cd is not None:
                        enriched.append(Team(
                            name=t.name,
                            logo_slug=t.logo_slug,
                            api_lookup_name=t.api_lookup_name,
                            location_name=t.location_name,
                            mascot_name=t.mascot_name,
                            conference=cd[0],
                            conference_abbr=cd[1],
                            division=cd[2],
                        ))
                    else:
                        enriched.append(t)
                resolved_teams = tuple(enriched)

        ordered_teams = list(sorted_teams(resolved_teams))

        # Separate cached files from logos that need downloading.
        download_tasks: list[tuple[Team, str, Path]] = []
        for team in ordered_teams:
            try:
                if team_set.source_mode == "template":
                    if not team_set.source_template or not team.logo_slug:
                        skipped_teams.append(f"{team.name}: missing template configuration")
                        continue
                    logo_url = team_set.source_template.format(slug=team.logo_slug)
                elif team_set.source_mode in ("espn_cfb_api", "espn_league_api_all"):
                    if not team.logo_slug:
                        skipped_teams.append(f"{team.name}: missing logo URL")
                        continue
                    logo_url = team.logo_slug
                else:
                    skipped_teams.append(f"{team.name}: unsupported source mode {team_set.source_mode}")
                    continue

                destination = output_dir / f"{team_filename_stem(team)}.png"

                if not force_refresh and destination.exists():
                    downloaded_files.append(destination)
                    if progress_callback:
                        progress_callback(f"      Cached logo: {destination.name}")
                    continue

                download_tasks.append((team, logo_url, destination))
            except Exception as e:
                skipped_teams.append(f"{team.name}: unexpected error ({str(e)[:50]})")

        # Download pending logos in parallel.
        if download_tasks:
            if progress_callback:
                progress_callback(
                    f"  Downloading {len(download_tasks)} logo(s)"
                    f" ({min(len(download_tasks), _MAX_WORKERS)} parallel workers)..."
                )
            with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
                future_to_team = {
                    executor.submit(_download_one_logo, url, dest): (team, dest)
                    for team, url, dest in download_tasks
                }
                for future in as_completed(future_to_team):
                    team, dest = future_to_team[future]
                    try:
                        future.result()
                        downloaded_files.append(dest)
                        if progress_callback:
                            progress_callback(f"      Saved logo: {dest.name}")
                    except Timeout:
                        skipped_teams.append(f"{team.name}: network timeout (exceeded {TIMEOUT_SECONDS}s)")
                    except ConnectionError:
                        skipped_teams.append(f"{team.name}: connection error (check network)")
                    except RequestException as exc:
                        skipped_teams.append(f"{team.name}: network error ({str(exc)[:50]})")
                    except Exception as exc:
                        skipped_teams.append(f"{team.name}: unexpected error ({str(exc)[:50]})")

        if skipped_teams:
            warnings.append(
                f"Skipped {len(skipped_teams)} teams due to download or configuration errors. "
                f"Examples: {', '.join(skipped_teams[:3])}"
                + (f" (and {len(skipped_teams) - 3} more)" if len(skipped_teams) > 3 else "")
            )

        # Download league / conference logo (non-fatal; skip on any error)
        league_logo_path: Path | None = None
        if team_set.league_logo_url:
            league_logo_dest = output_dir / f"_league_{team_set.code}.png"
            if not force_refresh and league_logo_dest.exists():
                league_logo_path = league_logo_dest
            else:
                try:
                    if progress_callback:
                        progress_callback("  Downloading league logo...")
                    response = session.get(team_set.league_logo_url, timeout=TIMEOUT_SECONDS)
                    response.raise_for_status()
                    league_logo_dest.write_bytes(response.content)
                    league_logo_path = league_logo_dest
                    if progress_callback:
                        progress_callback(f"      Saved league logo: {league_logo_dest.name}")
                except Exception as exc:
                    warnings.append(
                        f"League logo download failed (overlay will be skipped): {str(exc)[:80]}"
                    )

    return downloaded_files, resolved_teams, warnings, league_logo_path
