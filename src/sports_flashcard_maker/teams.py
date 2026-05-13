"""Static team metadata used by the logo downloader."""

from __future__ import annotations

from dataclasses import dataclass
import re

CFB_TEAMS_ENDPOINT = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams?limit=1000"


@dataclass(frozen=True)
class Team:
    name: str
    logo_slug: str | None = None
    api_lookup_name: str | None = None
    location_name: str | None = None
    mascot_name: str | None = None


@dataclass(frozen=True)
class FlashcardSet:
    code: str
    display_name: str
    source_mode: str
    source_template: str | None
    source_api_endpoint: str | None
    output_folder: str
    teams: tuple[Team, ...]
    league_logo_url: str | None = None


def normalize_team_name(name: str) -> str:
    """
    Normalize team names from API data.
    
    Converts ALL CAPS team names to proper Title Case.
    Preserves known acronyms (city abbreviations, FC, USA, etc.).
    
    Examples:
    - "DC DEFENDERS" → "DC Defenders"
    - "NEW YORK YANKEES" → "New York Yankees"
    - "ALABAMA" → "Alabama"
    - "Boston Red Sox" → "Boston Red Sox" (no change, already mixed case)
    """
    if not name or len(name) < 2:
        return name
    
    # Check if ALL CAPS (all letters are uppercase; allow spaces and numbers)
    letters_only = ''.join(c for c in name if c.isalpha())
    if not (letters_only and letters_only.isupper()):
        # Already mixed case or no alphabetic characters, return as-is
        return name
    
    # ALL CAPS detected: convert to title case but preserve known acronyms
    known_acronyms = {
        "DC", "LA", "NY", "SF", "NJ", "FC", "USA", "MLB", "NFL", "NBA",
        "NHL", "MLS", "WNBA", "AAC", "ACC", "AHL", "ECU", "USF", "UCF",
    }
    
    words = name.split()
    result = []
    
    for word in words:
        # If word is a known acronym, keep it uppercase
        if word in known_acronyms:
            result.append(word)
        # Otherwise, convert to title case (first letter uppercase, rest lowercase)
        else:
            result.append(word.capitalize())
    
    return " ".join(result)

# ESPN logo slugs are not always the same as common abbreviations.
MLB_TEAMS: tuple[Team, ...] = (
    Team("Arizona Diamondbacks", "ari"),
    Team("Atlanta Braves", "atl"),
    Team("Baltimore Orioles", "bal"),
    Team("Boston Red Sox", "bos"),
    Team("Chicago Cubs", "chc"),
    Team("Chicago White Sox", "chw"),
    Team("Cincinnati Reds", "cin"),
    Team("Cleveland Guardians", "cle"),
    Team("Colorado Rockies", "col"),
    Team("Detroit Tigers", "det"),
    Team("Houston Astros", "hou"),
    Team("Kansas City Royals", "kc"),
    Team("Los Angeles Angels", "laa"),
    Team("Los Angeles Dodgers", "lad"),
    Team("Miami Marlins", "mia"),
    Team("Milwaukee Brewers", "mil"),
    Team("Minnesota Twins", "min"),
    Team("New York Mets", "nym"),
    Team("New York Yankees", "nyy"),
    Team("Athletics", "oak"),
    Team("Philadelphia Phillies", "phi"),
    Team("Pittsburgh Pirates", "pit"),
    Team("San Diego Padres", "sd"),
    Team("San Francisco Giants", "sf"),
    Team("Seattle Mariners", "sea"),
    Team("St. Louis Cardinals", "stl"),
    Team("Tampa Bay Rays", "tb"),
    Team("Texas Rangers", "tex"),
    Team("Toronto Blue Jays", "tor"),
    Team("Washington Nationals", "wsh"),
)


ACC_TEAMS: tuple[Team, ...] = (
    Team("Boston College", api_lookup_name="Boston College"),
    Team("California", api_lookup_name="California"),
    Team("Clemson", api_lookup_name="Clemson"),
    Team("Duke", api_lookup_name="Duke"),
    Team("Florida State", api_lookup_name="Florida St"),
    Team("Georgia Tech", api_lookup_name="Georgia Tech"),
    Team("Louisville", api_lookup_name="Louisville"),
    Team("Miami", api_lookup_name="Miami"),
    Team("NC State", api_lookup_name="NC State"),
    Team("North Carolina", api_lookup_name="North Carolina"),
    Team("Notre Dame", api_lookup_name="Notre Dame"),
    Team("Pittsburgh", api_lookup_name="Pitt"),
    Team("SMU", api_lookup_name="SMU"),
    Team("Stanford", api_lookup_name="Stanford"),
    Team("Syracuse", api_lookup_name="Syracuse"),
    Team("Virginia", api_lookup_name="Virginia"),
    Team("Virginia Tech", api_lookup_name="Virginia Tech"),
    Team("Wake Forest", api_lookup_name="Wake Forest"),
)


BIG_TEN_TEAMS: tuple[Team, ...] = (
    Team("Illinois", api_lookup_name="Illinois"),
    Team("Indiana", api_lookup_name="Indiana"),
    Team("Iowa", api_lookup_name="Iowa"),
    Team("Maryland", api_lookup_name="Maryland"),
    Team("Michigan", api_lookup_name="Michigan"),
    Team("Michigan State", api_lookup_name="Michigan St"),
    Team("Minnesota", api_lookup_name="Minnesota"),
    Team("Nebraska", api_lookup_name="Nebraska"),
    Team("Northwestern", api_lookup_name="Northwestern"),
    Team("Ohio State", api_lookup_name="Ohio State"),
    Team("Oregon", api_lookup_name="Oregon"),
    Team("Penn State", api_lookup_name="Penn State"),
    Team("Purdue", api_lookup_name="Purdue"),
    Team("Rutgers", api_lookup_name="Rutgers"),
    Team("UCLA", api_lookup_name="UCLA"),
    Team("USC", api_lookup_name="USC"),
    Team("Washington", api_lookup_name="Washington"),
    Team("Wisconsin", api_lookup_name="Wisconsin"),
)


BIG_12_TEAMS: tuple[Team, ...] = (
    Team("Arizona", api_lookup_name="Arizona"),
    Team("Arizona State", api_lookup_name="Arizona St"),
    Team("Baylor", api_lookup_name="Baylor"),
    Team("BYU", api_lookup_name="BYU"),
    Team("Cincinnati", api_lookup_name="Cincinnati"),
    Team("Colorado", api_lookup_name="Colorado"),
    Team("Houston", api_lookup_name="Houston"),
    Team("Iowa State", api_lookup_name="Iowa State"),
    Team("Kansas", api_lookup_name="Kansas"),
    Team("Kansas State", api_lookup_name="Kansas St"),
    Team("Oklahoma State", api_lookup_name="Oklahoma St"),
    Team("TCU", api_lookup_name="TCU"),
    Team("Texas Tech", api_lookup_name="Texas Tech"),
    Team("UCF", api_lookup_name="UCF"),
    Team("Utah", api_lookup_name="Utah"),
    Team("West Virginia", api_lookup_name="West Virginia"),
)


SEC_TEAMS: tuple[Team, ...] = (
    Team("Alabama", api_lookup_name="Alabama"),
    Team("Arkansas", api_lookup_name="Arkansas"),
    Team("Auburn", api_lookup_name="Auburn"),
    Team("Florida", api_lookup_name="Florida"),
    Team("Georgia", api_lookup_name="Georgia"),
    Team("Kentucky", api_lookup_name="Kentucky"),
    Team("LSU", api_lookup_name="LSU"),
    Team("Mississippi State", api_lookup_name="Mississippi St"),
    Team("Missouri", api_lookup_name="Missouri"),
    Team("Oklahoma", api_lookup_name="Oklahoma"),
    Team("Ole Miss", api_lookup_name="Ole Miss"),
    Team("South Carolina", api_lookup_name="South Carolina"),
    Team("Tennessee", api_lookup_name="Tennessee"),
    Team("Texas", api_lookup_name="Texas"),
    Team("Texas A&M", api_lookup_name="Texas A&M"),
    Team("Vanderbilt", api_lookup_name="Vanderbilt"),
)


MAC_TEAMS: tuple[Team, ...] = (
    Team("Akron", api_lookup_name="Akron"),
    Team("Ball State", api_lookup_name="Ball State"),
    Team("Bowling Green", api_lookup_name="Bowling Green"),
    Team("Buffalo", api_lookup_name="Buffalo"),
    Team("Central Michigan", api_lookup_name="C Michigan"),
    Team("Eastern Michigan", api_lookup_name="E Michigan"),
    Team("Kent State", api_lookup_name="Kent State"),
    Team("Miami", api_lookup_name="Miami OH"),
    Team("Northern Illinois", api_lookup_name="N Illinois"),
    Team("Ohio", api_lookup_name="Ohio"),
    Team("Toledo", api_lookup_name="Toledo"),
    Team("Western Michigan", api_lookup_name="W Michigan"),
)


AAC_TEAMS: tuple[Team, ...] = (
    Team("East Carolina", api_lookup_name="East Carolina"),
    Team("Houston", api_lookup_name="Houston"),
    Team("Memphis", api_lookup_name="Memphis"),
    Team("SMU", api_lookup_name="SMU"),
    Team("South Florida", api_lookup_name="South Florida"),
    Team("Temple", api_lookup_name="Temple"),
    Team("Tulane", api_lookup_name="Tulane"),
    Team("Tulsa", api_lookup_name="Tulsa"),
)


IVY_LEAGUE_TEAMS: tuple[Team, ...] = (
    Team("Brown", api_lookup_name="Brown"),
    Team("Columbia", api_lookup_name="Columbia"),
    Team("Cornell", api_lookup_name="Cornell"),
    Team("Dartmouth", api_lookup_name="Dartmouth"),
    Team("Harvard", api_lookup_name="Harvard"),
    Team("Pennsylvania", api_lookup_name="Penn"),
    Team("Princeton", api_lookup_name="Princeton"),
    Team("Yale", api_lookup_name="Yale"),
)


PAC_12_TEAMS: tuple[Team, ...] = (
    Team("Arizona", api_lookup_name="Arizona"),
    Team("Arizona State", api_lookup_name="Arizona St"),
    Team("California", api_lookup_name="California"),
    Team("Colorado", api_lookup_name="Colorado"),
    Team("Oregon", api_lookup_name="Oregon"),
    Team("Oregon State", api_lookup_name="Oregon St"),
    Team("Stanford", api_lookup_name="Stanford"),
    Team("Utah", api_lookup_name="Utah"),
    Team("Washington", api_lookup_name="Washington"),
    Team("Washington State", api_lookup_name="Washington St"),
)


FLASHCARD_SETS: dict[str, FlashcardSet] = {
    "mlb": FlashcardSet(
        code="mlb",
        display_name="MLB",
        source_mode="template",
        source_template="https://a.espncdn.com/i/teamlogos/mlb/500/{slug}.png",
        source_api_endpoint=None,
        output_folder="MLB",
        teams=MLB_TEAMS,
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/mlb.png",
    ),
    "acc": FlashcardSet(
        code="acc",
        display_name="ACC",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="ACC",
        teams=ACC_TEAMS,
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/acc.png",
    ),
    "big_ten": FlashcardSet(
        code="big_ten",
        display_name="Big Ten",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="BIG_TEN",
        teams=BIG_TEN_TEAMS,
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/big_ten.png",
    ),
    "big_12": FlashcardSet(
        code="big_12",
        display_name="Big 12",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="BIG_12",
        teams=BIG_12_TEAMS,
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/big12.png",
    ),
    "sec": FlashcardSet(
        code="sec",
        display_name="SEC",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="SEC",
        teams=SEC_TEAMS,
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/sec.png",
    ),
    "mac": FlashcardSet(
        code="mac",
        display_name="MAC",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="MAC",
        teams=MAC_TEAMS,
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/mac.png",
    ),
    "aac": FlashcardSet(
        code="aac",
        display_name="AAC",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="AAC",
        teams=AAC_TEAMS,
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/aac.png",
    ),
    "ivy_league": FlashcardSet(
        code="ivy_league",
        display_name="Ivy League",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="IVY_LEAGUE",
        teams=IVY_LEAGUE_TEAMS,
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/ivy.png",
    ),
    "pac_12": FlashcardSet(
        code="pac_12",
        display_name="Pac-12",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="PAC_12",
        teams=PAC_12_TEAMS,
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/pac12.png",
    ),
    "nfl": FlashcardSet(
        code="nfl",
        display_name="NFL",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams?limit=200",
        output_folder="NFL",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png",
    ),
    "nba": FlashcardSet(
        code="nba",
        display_name="NBA",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams?limit=200",
        output_folder="NBA",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/nba.png",
    ),
    "nhl": FlashcardSet(
        code="nhl",
        display_name="NHL",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams?limit=200",
        output_folder="NHL",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/nhl.png",
    ),
    "wnba": FlashcardSet(
        code="wnba",
        display_name="WNBA",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/teams?limit=200",
        output_folder="WNBA",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/wnba.png",
    ),
    "mls": FlashcardSet(
        code="mls",
        display_name="MLS",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/teams?limit=200",
        output_folder="MLS",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/mls.png",
    ),
    "epl": FlashcardSet(
        code="epl",
        display_name="Premier League",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams?limit=200",
        output_folder="PREMIER_LEAGUE",
        teams=(),
    ),
    "efl_championship": FlashcardSet(
        code="efl_championship",
        display_name="EFL Championship",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/soccer/eng.2/teams?limit=200",
        output_folder="EFL_CHAMPIONSHIP",
        teams=(),
    ),
    "efl_league_one": FlashcardSet(
        code="efl_league_one",
        display_name="EFL League One",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/soccer/eng.3/teams?limit=200",
        output_folder="EFL_LEAGUE_ONE",
        teams=(),
    ),
    "efl_league_two": FlashcardSet(
        code="efl_league_two",
        display_name="EFL League Two",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/soccer/eng.4/teams?limit=200",
        output_folder="EFL_LEAGUE_TWO",
        teams=(),
    ),
    "nwsl": FlashcardSet(
        code="nwsl",
        display_name="NWSL",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/soccer/usa.nwsl/teams?limit=200",
        output_folder="NWSL",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/nwsl.png",
    ),
    "ufl": FlashcardSet(
        code="ufl",
        display_name="UFL",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/football/ufl/teams?limit=200",
        output_folder="UFL",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/ufl.png",
    ),
}


def sorted_teams(teams: tuple[Team, ...]) -> tuple[Team, ...]:
    """Return teams sorted alphabetically by full team name."""
    return tuple(sorted(teams, key=lambda team: team.name.lower()))


def team_filename_stem(team: Team) -> str:
    """Convert a team full name to a filesystem-safe lowercase stem."""
    slug = re.sub(r"[^a-z0-9]+", "_", team.name.lower())
    return slug.strip("_")


def get_flashcard_set(code: str) -> FlashcardSet:
    normalized = code.lower()
    if normalized not in FLASHCARD_SETS:
        options = ", ".join(sorted(FLASHCARD_SETS))
        raise ValueError(f"Unknown flashcard set '{code}'. Valid options: {options}")
    return FLASHCARD_SETS[normalized]


def split_team_name(team: Team) -> tuple[str, str]:
    """
    Split a team's full name into location/city and team name.
    
    Assumes the first word(s) are location/city, remaining words are team name.
    Examples:
    - "San Francisco 49ers" → ("San Francisco", "49ers")
    - "University of North Carolina Tar Heels" → ("University of North Carolina", "Tar Heels")
    - "Denver Summit FC" → ("Denver", "Summit FC")  # NWSL pattern
    - "Chicago Red Stars" → ("Chicago", "Red Stars")  # NWSL pattern
    - "Orlando Pride" → ("Orlando", "Pride")
    """
    if team.location_name and team.mascot_name:
        location = team.location_name.strip()
        mascot = team.mascot_name.strip()
        # Some league feeds provide identical location/name values (for example,
        # "Orlando Pride" for both). Fall back to heuristic splitting in that case.
        if location and mascot and location.lower() != mascot.lower():
            return location, mascot

    parts = team.name.split()
    if len(parts) <= 1:
        # For single-word names, use the same token for both location and team
        # so city_only/team_only modes remain non-empty.
        return team.name, team.name
    
    # Handle NWSL/soccer teams: common suffixes like FC, Stars, United, Athletic
    # These have multi-word team names where last word is the suffix
    # E.g., "Denver Summit FC" → ("Denver", "Summit FC"), "Chicago Red Stars" → ("Chicago", "Red Stars")
    last_word_lower = parts[-1].lower()
    soccer_suffixes = {"fc", "stars", "united", "athletic", "city", "town", "club", "republic"}
    
    if len(parts) >= 3 and last_word_lower in soccer_suffixes:
        team_name = " ".join(parts[-2:])
        location = " ".join(parts[:-2])
        return location, team_name
    
    # Default: assume last word is team name, everything else is location
    team_name = parts[-1]
    location = " ".join(parts[:-1])
    
    # Check if 2-word team name (like "Tar Heels", "State Wildcats")
    if len(parts) >= 2:
        potential_team = " ".join(parts[-2:])
        # If second-to-last word is capitalized and not obviously a location word
        if not parts[-2].lower() in ("of", "the", "and", "&"):
            # Heuristic: use 2 words for college teams (universities have longer names)
            if "university" in team.name.lower() or "college" in team.name.lower():
                team_name = potential_team
                location = " ".join(parts[:-2])
    
    return location, team_name


def format_team_name(
    team: Team,
    name_format: str = "full",
) -> str:
    """
    Format a team name according to config options.
    
    Args:
        team: The team object
        name_format: "full" (city+team), "city_only", or "team_only"
    
    Returns:
        Formatted team name string
    """
    if name_format == "team_only":
        _, team_name = split_team_name(team)
        return team_name
    elif name_format == "city_only":
        location, _ = split_team_name(team)
        return location
    elif name_format == "full":
        location, team_name = split_team_name(team)
        if location.strip().lower() == team_name.strip().lower():
            return location.strip()
        return f"{location} {team_name}".strip()
    else:
        return team.name


def format_filename(
    team: Team,
    filename_format: str = "prefix",
    name_format: str = "full",
) -> tuple[str, str, str]:
    """
    Generate logo, text, and combo filename stems for a team.

    Args:
        team: The team object
        filename_format: "prefix" or "suffix"
        name_format: "full", "city_only", or "team_only"

    Returns:
        Tuple of (logo_stem, text_stem, combo_stem) without extension
    """
    formatted_name = format_team_name(team, name_format)
    stem = re.sub(r"[^a-z0-9]+", "_", formatted_name.lower()).strip("_")

    if filename_format == "suffix":
        return f"{stem}_logo", f"{stem}_text", f"{stem}_combo"
    else:  # prefix (default)
        return f"logo_{stem}", f"text_{stem}", f"combo_{stem}"


def format_output_filenames(
    team: Team,
    filename_format: str = "prefix",
    name_format: str = "full",
    card_types: set[str] | None = None,
) -> list[str]:
    """Generate output filename stems for the selected card types.

    Args:
        card_types: Set of types to include — any of "logo", "text", "combo".
                    Defaults to {"logo", "text"}.

    Returns:
        Filename stems in order: logo first, text second, combo third.
    """
    if card_types is None:
        card_types = {"logo", "text"}

    logo_name, text_name, combo_name = format_filename(
        team,
        filename_format=filename_format,
        name_format=name_format,
    )

    result: list[str] = []
    if "logo" in card_types:
        result.append(logo_name)
    if "text" in card_types:
        result.append(text_name)
    if "combo" in card_types:
        result.append(combo_name)
    return result
