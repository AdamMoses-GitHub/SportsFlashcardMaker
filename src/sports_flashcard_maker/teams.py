"""Static team metadata used by the logo downloader."""

from __future__ import annotations

from dataclasses import dataclass
import re

CFB_TEAMS_ENDPOINT = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams?limit=1000"

# Per-conference ESPN endpoints — filtered by ESPN conference group ID.
_CFB_CONF_URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams?groups={}&limit=200"
CFB_ACC_ENDPOINT     = _CFB_CONF_URL.format(1)
CFB_BIG_12_ENDPOINT  = _CFB_CONF_URL.format(4)
CFB_BIG_TEN_ENDPOINT = _CFB_CONF_URL.format(5)
CFB_SEC_ENDPOINT     = _CFB_CONF_URL.format(8)
CFB_PAC_12_ENDPOINT  = _CFB_CONF_URL.format(9)
CFB_MAC_ENDPOINT     = _CFB_CONF_URL.format(15)
CFB_AAC_ENDPOINT     = _CFB_CONF_URL.format(151)
CFB_IVY_ENDPOINT     = _CFB_CONF_URL.format(22)


@dataclass(frozen=True)
class Team:
    name: str
    logo_slug: str | None = None
    api_lookup_name: str | None = None
    location_name: str | None = None
    mascot_name: str | None = None
    conference: str | None = None
    conference_abbr: str | None = None
    division: str | None = None


@dataclass(frozen=True)
class ConferenceEndpoint:
    """Pairs an ESPN API URL with the conference metadata used to tag fetched teams."""
    url: str
    conference: str
    conference_abbr: str


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
    default_conference: str | None = None
    default_conference_abbr: str | None = None
    source_api_endpoints: tuple[ConferenceEndpoint, ...] = ()


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
    Team("Arizona Diamondbacks",  "ari", conference="National League",  conference_abbr="NL", division="West"),
    Team("Atlanta Braves",        "atl", conference="National League",  conference_abbr="NL", division="East"),
    Team("Baltimore Orioles",     "bal", conference="American League",  conference_abbr="AL", division="East"),
    Team("Boston Red Sox",        "bos", conference="American League",  conference_abbr="AL", division="East"),
    Team("Chicago Cubs",          "chc", conference="National League",  conference_abbr="NL", division="Central"),
    Team("Chicago White Sox",     "chw", conference="American League",  conference_abbr="AL", division="Central"),
    Team("Cincinnati Reds",       "cin", conference="National League",  conference_abbr="NL", division="Central"),
    Team("Cleveland Guardians",   "cle", conference="American League",  conference_abbr="AL", division="Central"),
    Team("Colorado Rockies",      "col", conference="National League",  conference_abbr="NL", division="West"),
    Team("Detroit Tigers",        "det", conference="American League",  conference_abbr="AL", division="Central"),
    Team("Houston Astros",        "hou", conference="American League",  conference_abbr="AL", division="West"),
    Team("Kansas City Royals",    "kc",  conference="American League",  conference_abbr="AL", division="Central"),
    Team("Los Angeles Angels",    "laa", conference="American League",  conference_abbr="AL", division="West"),
    Team("Los Angeles Dodgers",   "lad", conference="National League",  conference_abbr="NL", division="West"),
    Team("Miami Marlins",         "mia", conference="National League",  conference_abbr="NL", division="East"),
    Team("Milwaukee Brewers",     "mil", conference="National League",  conference_abbr="NL", division="Central"),
    Team("Minnesota Twins",       "min", conference="American League",  conference_abbr="AL", division="Central"),
    Team("New York Mets",         "nym", conference="National League",  conference_abbr="NL", division="East"),
    Team("New York Yankees",      "nyy", conference="American League",  conference_abbr="AL", division="East"),
    Team("Athletics",             "oak", conference="American League",  conference_abbr="AL", division="West"),
    Team("Philadelphia Phillies", "phi", conference="National League",  conference_abbr="NL", division="East"),
    Team("Pittsburgh Pirates",    "pit", conference="National League",  conference_abbr="NL", division="Central"),
    Team("San Diego Padres",      "sd",  conference="National League",  conference_abbr="NL", division="West"),
    Team("San Francisco Giants",  "sf",  conference="National League",  conference_abbr="NL", division="West"),
    Team("Seattle Mariners",      "sea", conference="American League",  conference_abbr="AL", division="West"),
    Team("St. Louis Cardinals",   "stl", conference="National League",  conference_abbr="NL", division="Central"),
    Team("Tampa Bay Rays",        "tb",  conference="American League",  conference_abbr="AL", division="East"),
    Team("Texas Rangers",         "tex", conference="American League",  conference_abbr="AL", division="West"),
    Team("Toronto Blue Jays",     "tor", conference="American League",  conference_abbr="AL", division="East"),
    Team("Washington Nationals",  "wsh", conference="National League",  conference_abbr="NL", division="East"),
)


ACC_TEAMS: tuple[Team, ...] = (
    Team("Boston College",  api_lookup_name="Boston College",  conference="ACC", conference_abbr="ACC"),
    Team("California",      api_lookup_name="California",      conference="ACC", conference_abbr="ACC"),
    Team("Clemson",         api_lookup_name="Clemson",         conference="ACC", conference_abbr="ACC"),
    Team("Duke",            api_lookup_name="Duke",            conference="ACC", conference_abbr="ACC"),
    Team("Florida State",   api_lookup_name="Florida St",      conference="ACC", conference_abbr="ACC"),
    Team("Georgia Tech",    api_lookup_name="Georgia Tech",    conference="ACC", conference_abbr="ACC"),
    Team("Louisville",      api_lookup_name="Louisville",      conference="ACC", conference_abbr="ACC"),
    Team("Miami",           api_lookup_name="Miami",           conference="ACC", conference_abbr="ACC"),
    Team("NC State",        api_lookup_name="NC State",        conference="ACC", conference_abbr="ACC"),
    Team("North Carolina",  api_lookup_name="North Carolina",  conference="ACC", conference_abbr="ACC"),
    Team("Notre Dame",      api_lookup_name="Notre Dame",      conference="ACC", conference_abbr="ACC"),
    Team("Pittsburgh",      api_lookup_name="Pitt",            conference="ACC", conference_abbr="ACC"),
    Team("SMU",             api_lookup_name="SMU",             conference="ACC", conference_abbr="ACC"),
    Team("Stanford",        api_lookup_name="Stanford",        conference="ACC", conference_abbr="ACC"),
    Team("Syracuse",        api_lookup_name="Syracuse",        conference="ACC", conference_abbr="ACC"),
    Team("Virginia",        api_lookup_name="Virginia",        conference="ACC", conference_abbr="ACC"),
    Team("Virginia Tech",   api_lookup_name="Virginia Tech",   conference="ACC", conference_abbr="ACC"),
    Team("Wake Forest",     api_lookup_name="Wake Forest",     conference="ACC", conference_abbr="ACC"),
)


BIG_TEN_TEAMS: tuple[Team, ...] = (
    Team("Illinois",       api_lookup_name="Illinois",     conference="Big Ten", conference_abbr="Big Ten"),
    Team("Indiana",        api_lookup_name="Indiana",      conference="Big Ten", conference_abbr="Big Ten"),
    Team("Iowa",           api_lookup_name="Iowa",         conference="Big Ten", conference_abbr="Big Ten"),
    Team("Maryland",       api_lookup_name="Maryland",     conference="Big Ten", conference_abbr="Big Ten"),
    Team("Michigan",       api_lookup_name="Michigan",     conference="Big Ten", conference_abbr="Big Ten"),
    Team("Michigan State", api_lookup_name="Michigan St",  conference="Big Ten", conference_abbr="Big Ten"),
    Team("Minnesota",      api_lookup_name="Minnesota",    conference="Big Ten", conference_abbr="Big Ten"),
    Team("Nebraska",       api_lookup_name="Nebraska",     conference="Big Ten", conference_abbr="Big Ten"),
    Team("Northwestern",   api_lookup_name="Northwestern", conference="Big Ten", conference_abbr="Big Ten"),
    Team("Ohio State",     api_lookup_name="Ohio State",   conference="Big Ten", conference_abbr="Big Ten"),
    Team("Oregon",         api_lookup_name="Oregon",       conference="Big Ten", conference_abbr="Big Ten"),
    Team("Penn State",     api_lookup_name="Penn State",   conference="Big Ten", conference_abbr="Big Ten"),
    Team("Purdue",         api_lookup_name="Purdue",       conference="Big Ten", conference_abbr="Big Ten"),
    Team("Rutgers",        api_lookup_name="Rutgers",      conference="Big Ten", conference_abbr="Big Ten"),
    Team("UCLA",           api_lookup_name="UCLA",         conference="Big Ten", conference_abbr="Big Ten"),
    Team("USC",            api_lookup_name="USC",          conference="Big Ten", conference_abbr="Big Ten"),
    Team("Washington",     api_lookup_name="Washington",   conference="Big Ten", conference_abbr="Big Ten"),
    Team("Wisconsin",      api_lookup_name="Wisconsin",    conference="Big Ten", conference_abbr="Big Ten"),
)


BIG_12_TEAMS: tuple[Team, ...] = (
    Team("Arizona",       api_lookup_name="Arizona",       conference="Big 12", conference_abbr="Big 12"),
    Team("Arizona State", api_lookup_name="Arizona St",    conference="Big 12", conference_abbr="Big 12"),
    Team("Baylor",        api_lookup_name="Baylor",        conference="Big 12", conference_abbr="Big 12"),
    Team("BYU",           api_lookup_name="BYU",           conference="Big 12", conference_abbr="Big 12"),
    Team("Cincinnati",    api_lookup_name="Cincinnati",    conference="Big 12", conference_abbr="Big 12"),
    Team("Colorado",      api_lookup_name="Colorado",      conference="Big 12", conference_abbr="Big 12"),
    Team("Houston",       api_lookup_name="Houston",       conference="Big 12", conference_abbr="Big 12"),
    Team("Iowa State",    api_lookup_name="Iowa State",    conference="Big 12", conference_abbr="Big 12"),
    Team("Kansas",        api_lookup_name="Kansas",        conference="Big 12", conference_abbr="Big 12"),
    Team("Kansas State",  api_lookup_name="Kansas St",     conference="Big 12", conference_abbr="Big 12"),
    Team("Oklahoma State",api_lookup_name="Oklahoma St",   conference="Big 12", conference_abbr="Big 12"),
    Team("TCU",           api_lookup_name="TCU",           conference="Big 12", conference_abbr="Big 12"),
    Team("Texas Tech",    api_lookup_name="Texas Tech",    conference="Big 12", conference_abbr="Big 12"),
    Team("UCF",           api_lookup_name="UCF",           conference="Big 12", conference_abbr="Big 12"),
    Team("Utah",          api_lookup_name="Utah",          conference="Big 12", conference_abbr="Big 12"),
    Team("West Virginia", api_lookup_name="West Virginia", conference="Big 12", conference_abbr="Big 12"),
)


SEC_TEAMS: tuple[Team, ...] = (
    Team("Alabama",          api_lookup_name="Alabama",         conference="SEC", conference_abbr="SEC"),
    Team("Arkansas",         api_lookup_name="Arkansas",        conference="SEC", conference_abbr="SEC"),
    Team("Auburn",           api_lookup_name="Auburn",          conference="SEC", conference_abbr="SEC"),
    Team("Florida",          api_lookup_name="Florida",         conference="SEC", conference_abbr="SEC"),
    Team("Georgia",          api_lookup_name="Georgia",         conference="SEC", conference_abbr="SEC"),
    Team("Kentucky",         api_lookup_name="Kentucky",        conference="SEC", conference_abbr="SEC"),
    Team("LSU",              api_lookup_name="LSU",             conference="SEC", conference_abbr="SEC"),
    Team("Mississippi State",api_lookup_name="Mississippi St",  conference="SEC", conference_abbr="SEC"),
    Team("Missouri",         api_lookup_name="Missouri",        conference="SEC", conference_abbr="SEC"),
    Team("Oklahoma",         api_lookup_name="Oklahoma",        conference="SEC", conference_abbr="SEC"),
    Team("Ole Miss",         api_lookup_name="Ole Miss",        conference="SEC", conference_abbr="SEC"),
    Team("South Carolina",   api_lookup_name="South Carolina",  conference="SEC", conference_abbr="SEC"),
    Team("Tennessee",        api_lookup_name="Tennessee",       conference="SEC", conference_abbr="SEC"),
    Team("Texas",            api_lookup_name="Texas",           conference="SEC", conference_abbr="SEC"),
    Team("Texas A&M",        api_lookup_name="Texas A&M",       conference="SEC", conference_abbr="SEC"),
    Team("Vanderbilt",       api_lookup_name="Vanderbilt",      conference="SEC", conference_abbr="SEC"),
)


MAC_TEAMS: tuple[Team, ...] = (
    Team("Akron",             api_lookup_name="Akron",         conference="MAC", conference_abbr="MAC"),
    Team("Ball State",        api_lookup_name="Ball State",    conference="MAC", conference_abbr="MAC"),
    Team("Bowling Green",     api_lookup_name="Bowling Green", conference="MAC", conference_abbr="MAC"),
    Team("Buffalo",           api_lookup_name="Buffalo",       conference="MAC", conference_abbr="MAC"),
    Team("Central Michigan",  api_lookup_name="C Michigan",    conference="MAC", conference_abbr="MAC"),
    Team("Eastern Michigan",  api_lookup_name="E Michigan",    conference="MAC", conference_abbr="MAC"),
    Team("Kent State",        api_lookup_name="Kent State",    conference="MAC", conference_abbr="MAC"),
    Team("Miami",             api_lookup_name="Miami OH",      conference="MAC", conference_abbr="MAC"),
    Team("Northern Illinois", api_lookup_name="N Illinois",    conference="MAC", conference_abbr="MAC"),
    Team("Ohio",              api_lookup_name="Ohio",          conference="MAC", conference_abbr="MAC"),
    Team("Toledo",            api_lookup_name="Toledo",        conference="MAC", conference_abbr="MAC"),
    Team("Western Michigan",  api_lookup_name="W Michigan",    conference="MAC", conference_abbr="MAC"),
)


AAC_TEAMS: tuple[Team, ...] = (
    Team("East Carolina", api_lookup_name="East Carolina",  conference="AAC", conference_abbr="AAC"),
    Team("Houston",       api_lookup_name="Houston",        conference="AAC", conference_abbr="AAC"),
    Team("Memphis",       api_lookup_name="Memphis",        conference="AAC", conference_abbr="AAC"),
    Team("SMU",           api_lookup_name="SMU",            conference="AAC", conference_abbr="AAC"),
    Team("South Florida", api_lookup_name="South Florida",  conference="AAC", conference_abbr="AAC"),
    Team("Temple",        api_lookup_name="Temple",         conference="AAC", conference_abbr="AAC"),
    Team("Tulane",        api_lookup_name="Tulane",         conference="AAC", conference_abbr="AAC"),
    Team("Tulsa",         api_lookup_name="Tulsa",          conference="AAC", conference_abbr="AAC"),
)


IVY_LEAGUE_TEAMS: tuple[Team, ...] = (
    Team("Brown",        api_lookup_name="Brown",      conference="Ivy League", conference_abbr="Ivy"),
    Team("Columbia",     api_lookup_name="Columbia",   conference="Ivy League", conference_abbr="Ivy"),
    Team("Cornell",      api_lookup_name="Cornell",    conference="Ivy League", conference_abbr="Ivy"),
    Team("Dartmouth",    api_lookup_name="Dartmouth",  conference="Ivy League", conference_abbr="Ivy"),
    Team("Harvard",      api_lookup_name="Harvard",    conference="Ivy League", conference_abbr="Ivy"),
    Team("Pennsylvania", api_lookup_name="Penn",       conference="Ivy League", conference_abbr="Ivy"),
    Team("Princeton",    api_lookup_name="Princeton",  conference="Ivy League", conference_abbr="Ivy"),
    Team("Yale",         api_lookup_name="Yale",       conference="Ivy League", conference_abbr="Ivy"),
)


PAC_12_TEAMS: tuple[Team, ...] = (
    Team("Arizona",        api_lookup_name="Arizona",        conference="Pac-12", conference_abbr="Pac-12"),
    Team("Arizona State",  api_lookup_name="Arizona St",     conference="Pac-12", conference_abbr="Pac-12"),
    Team("California",     api_lookup_name="California",     conference="Pac-12", conference_abbr="Pac-12"),
    Team("Colorado",       api_lookup_name="Colorado",       conference="Pac-12", conference_abbr="Pac-12"),
    Team("Oregon",         api_lookup_name="Oregon",         conference="Pac-12", conference_abbr="Pac-12"),
    Team("Oregon State",   api_lookup_name="Oregon St",      conference="Pac-12", conference_abbr="Pac-12"),
    Team("Stanford",       api_lookup_name="Stanford",       conference="Pac-12", conference_abbr="Pac-12"),
    Team("Utah",           api_lookup_name="Utah",           conference="Pac-12", conference_abbr="Pac-12"),
    Team("Washington",     api_lookup_name="Washington",     conference="Pac-12", conference_abbr="Pac-12"),
    Team("Washington State",api_lookup_name="Washington St", conference="Pac-12", conference_abbr="Pac-12"),
)


def _dedup_cfb_teams(*team_tuples: tuple[Team, ...]) -> tuple[Team, ...]:
    """Combine multiple CFB conference tuples, keeping the first occurrence of each team.

    Teams that appear in multiple tuples (due to conference realignment) are kept
    under the conference of the first tuple they appear in.  The key is the
    case-folded api_lookup_name (or display name when absent).
    """
    seen: set[str] = set()
    result: list[Team] = []
    for teams in team_tuples:
        for team in teams:
            key = (team.api_lookup_name or team.name).lower()
            if key not in seen:
                seen.add(key)
                result.append(team)
    return tuple(result)


# Combined set of all supported CFB conferences.  Teams that appear in more than
# one conference tuple (realignment artefacts) are kept under their current
# conference — the order below is ACC → Big Ten → Big 12 → SEC → MAC → AAC →
# Ivy League → Pac-12, so modern conferences take priority over the old Pac-12.
CFB_ALL_TEAMS: tuple[Team, ...] = _dedup_cfb_teams(
    ACC_TEAMS,
    BIG_TEN_TEAMS,
    BIG_12_TEAMS,
    SEC_TEAMS,
    MAC_TEAMS,
    AAC_TEAMS,
    IVY_LEAGUE_TEAMS,
    PAC_12_TEAMS,
)

# Conference / division lookup for API-fetched sets.
# Keys are lowercased team display names (as returned by ESPN API after normalize_team_name).
# Values are (conference_full, conference_abbr, division_or_None).
# Unknown teams simply get no conference data — handled gracefully.
_CD = tuple[str | None, str | None, str | None]  # type alias for readability
CONFERENCE_LOOKUP: dict[str, dict[str, _CD]] = {
    "nfl": {
        # AFC East
        "buffalo bills":           ("American Football Conference", "AFC", "East"),
        "miami dolphins":          ("American Football Conference", "AFC", "East"),
        "new england patriots":    ("American Football Conference", "AFC", "East"),
        "new york jets":           ("American Football Conference", "AFC", "East"),
        # AFC North
        "baltimore ravens":        ("American Football Conference", "AFC", "North"),
        "cincinnati bengals":      ("American Football Conference", "AFC", "North"),
        "cleveland browns":        ("American Football Conference", "AFC", "North"),
        "pittsburgh steelers":     ("American Football Conference", "AFC", "North"),
        # AFC South
        "houston texans":          ("American Football Conference", "AFC", "South"),
        "indianapolis colts":      ("American Football Conference", "AFC", "South"),
        "jacksonville jaguars":    ("American Football Conference", "AFC", "South"),
        "tennessee titans":        ("American Football Conference", "AFC", "South"),
        # AFC West
        "denver broncos":          ("American Football Conference", "AFC", "West"),
        "kansas city chiefs":      ("American Football Conference", "AFC", "West"),
        "las vegas raiders":       ("American Football Conference", "AFC", "West"),
        "los angeles chargers":    ("American Football Conference", "AFC", "West"),
        # NFC East
        "dallas cowboys":          ("National Football Conference", "NFC", "East"),
        "new york giants":         ("National Football Conference", "NFC", "East"),
        "philadelphia eagles":     ("National Football Conference", "NFC", "East"),
        "washington commanders":   ("National Football Conference", "NFC", "East"),
        # NFC North
        "chicago bears":           ("National Football Conference", "NFC", "North"),
        "detroit lions":           ("National Football Conference", "NFC", "North"),
        "green bay packers":       ("National Football Conference", "NFC", "North"),
        "minnesota vikings":       ("National Football Conference", "NFC", "North"),
        # NFC South
        "atlanta falcons":         ("National Football Conference", "NFC", "South"),
        "carolina panthers":       ("National Football Conference", "NFC", "South"),
        "new orleans saints":      ("National Football Conference", "NFC", "South"),
        "tampa bay buccaneers":    ("National Football Conference", "NFC", "South"),
        # NFC West
        "arizona cardinals":       ("National Football Conference", "NFC", "West"),
        "los angeles rams":        ("National Football Conference", "NFC", "West"),
        "san francisco 49ers":     ("National Football Conference", "NFC", "West"),
        "seattle seahawks":        ("National Football Conference", "NFC", "West"),
    },
    "nba": {
        # Eastern / Atlantic
        "boston celtics":          ("Eastern Conference", "Eastern", "Atlantic"),
        "brooklyn nets":           ("Eastern Conference", "Eastern", "Atlantic"),
        "new york knicks":         ("Eastern Conference", "Eastern", "Atlantic"),
        "philadelphia 76ers":      ("Eastern Conference", "Eastern", "Atlantic"),
        "toronto raptors":         ("Eastern Conference", "Eastern", "Atlantic"),
        # Eastern / Central
        "chicago bulls":           ("Eastern Conference", "Eastern", "Central"),
        "cleveland cavaliers":     ("Eastern Conference", "Eastern", "Central"),
        "detroit pistons":         ("Eastern Conference", "Eastern", "Central"),
        "indiana pacers":          ("Eastern Conference", "Eastern", "Central"),
        "milwaukee bucks":         ("Eastern Conference", "Eastern", "Central"),
        # Eastern / Southeast
        "atlanta hawks":           ("Eastern Conference", "Eastern", "Southeast"),
        "charlotte hornets":       ("Eastern Conference", "Eastern", "Southeast"),
        "miami heat":              ("Eastern Conference", "Eastern", "Southeast"),
        "orlando magic":           ("Eastern Conference", "Eastern", "Southeast"),
        "washington wizards":      ("Eastern Conference", "Eastern", "Southeast"),
        # Western / Northwest
        "denver nuggets":          ("Western Conference", "Western", "Northwest"),
        "minnesota timberwolves":  ("Western Conference", "Western", "Northwest"),
        "oklahoma city thunder":   ("Western Conference", "Western", "Northwest"),
        "portland trail blazers":  ("Western Conference", "Western", "Northwest"),
        "utah jazz":               ("Western Conference", "Western", "Northwest"),
        # Western / Pacific
        "golden state warriors":   ("Western Conference", "Western", "Pacific"),
        "los angeles clippers":    ("Western Conference", "Western", "Pacific"),
        "los angeles lakers":      ("Western Conference", "Western", "Pacific"),
        "phoenix suns":            ("Western Conference", "Western", "Pacific"),
        "sacramento kings":        ("Western Conference", "Western", "Pacific"),
        # Western / Southwest
        "dallas mavericks":        ("Western Conference", "Western", "Southwest"),
        "houston rockets":         ("Western Conference", "Western", "Southwest"),
        "memphis grizzlies":       ("Western Conference", "Western", "Southwest"),
        "new orleans pelicans":    ("Western Conference", "Western", "Southwest"),
        "san antonio spurs":       ("Western Conference", "Western", "Southwest"),
    },
    "nhl": {
        # Eastern / Atlantic
        "boston bruins":           ("Eastern Conference", "Eastern", "Atlantic"),
        "buffalo sabres":          ("Eastern Conference", "Eastern", "Atlantic"),
        "detroit red wings":       ("Eastern Conference", "Eastern", "Atlantic"),
        "florida panthers":        ("Eastern Conference", "Eastern", "Atlantic"),
        "montréal canadiens":      ("Eastern Conference", "Eastern", "Atlantic"),
        "montreal canadiens":      ("Eastern Conference", "Eastern", "Atlantic"),
        "ottawa senators":         ("Eastern Conference", "Eastern", "Atlantic"),
        "tampa bay lightning":     ("Eastern Conference", "Eastern", "Atlantic"),
        "toronto maple leafs":     ("Eastern Conference", "Eastern", "Atlantic"),
        # Eastern / Metropolitan
        "carolina hurricanes":     ("Eastern Conference", "Eastern", "Metropolitan"),
        "columbus blue jackets":   ("Eastern Conference", "Eastern", "Metropolitan"),
        "new jersey devils":       ("Eastern Conference", "Eastern", "Metropolitan"),
        "new york islanders":      ("Eastern Conference", "Eastern", "Metropolitan"),
        "new york rangers":        ("Eastern Conference", "Eastern", "Metropolitan"),
        "philadelphia flyers":     ("Eastern Conference", "Eastern", "Metropolitan"),
        "pittsburgh penguins":     ("Eastern Conference", "Eastern", "Metropolitan"),
        "washington capitals":     ("Eastern Conference", "Eastern", "Metropolitan"),
        # Western / Central
        "chicago blackhawks":      ("Western Conference", "Western", "Central"),
        "colorado avalanche":      ("Western Conference", "Western", "Central"),
        "dallas stars":            ("Western Conference", "Western", "Central"),
        "minnesota wild":          ("Western Conference", "Western", "Central"),
        "nashville predators":     ("Western Conference", "Western", "Central"),
        "st. louis blues":         ("Western Conference", "Western", "Central"),
        "utah hockey club":        ("Western Conference", "Western", "Central"),
        "winnipeg jets":           ("Western Conference", "Western", "Central"),
        # Western / Pacific
        "anaheim ducks":           ("Western Conference", "Western", "Pacific"),
        "calgary flames":          ("Western Conference", "Western", "Pacific"),
        "edmonton oilers":         ("Western Conference", "Western", "Pacific"),
        "los angeles kings":       ("Western Conference", "Western", "Pacific"),
        "san jose sharks":         ("Western Conference", "Western", "Pacific"),
        "seattle kraken":          ("Western Conference", "Western", "Pacific"),
        "vancouver canucks":       ("Western Conference", "Western", "Pacific"),
        "vegas golden knights":    ("Western Conference", "Western", "Pacific"),
    },
    "wnba": {
        # Eastern Conference (no divisions)
        "atlanta dream":           ("Eastern Conference", "Eastern", None),
        "chicago sky":             ("Eastern Conference", "Eastern", None),
        "connecticut sun":         ("Eastern Conference", "Eastern", None),
        "indiana fever":           ("Eastern Conference", "Eastern", None),
        "new york liberty":        ("Eastern Conference", "Eastern", None),
        "toronto tempo":           ("Eastern Conference", "Eastern", None),
        "washington mystics":      ("Eastern Conference", "Eastern", None),
        # Western Conference (no divisions)
        "dallas wings":            ("Western Conference", "Western", None),
        "golden state valkyries":  ("Western Conference", "Western", None),
        "las vegas aces":          ("Western Conference", "Western", None),
        "los angeles sparks":      ("Western Conference", "Western", None),
        "minnesota lynx":          ("Western Conference", "Western", None),
        "phoenix mercury":         ("Western Conference", "Western", None),
        "seattle storm":           ("Western Conference", "Western", None),
    },
    "mls": {
        # Eastern Conference (no divisions)
        "atlanta united fc":       ("Eastern Conference", "Eastern", None),
        "cf montréal":             ("Eastern Conference", "Eastern", None),
        "cf montreal":             ("Eastern Conference", "Eastern", None),
        "charlotte fc":            ("Eastern Conference", "Eastern", None),
        "chicago fire fc":         ("Eastern Conference", "Eastern", None),
        "columbus crew":           ("Eastern Conference", "Eastern", None),
        "d.c. united":             ("Eastern Conference", "Eastern", None),
        "fc cincinnati":           ("Eastern Conference", "Eastern", None),
        "inter miami cf":          ("Eastern Conference", "Eastern", None),
        "nashville sc":            ("Eastern Conference", "Eastern", None),
        "new england revolution":  ("Eastern Conference", "Eastern", None),
        "new york city fc":        ("Eastern Conference", "Eastern", None),
        "new york red bulls":      ("Eastern Conference", "Eastern", None),
        "orlando city sc":         ("Eastern Conference", "Eastern", None),
        "philadelphia union":      ("Eastern Conference", "Eastern", None),
        "toronto fc":              ("Eastern Conference", "Eastern", None),
        # Western Conference (no divisions)
        "austin fc":               ("Western Conference", "Western", None),
        "colorado rapids":         ("Western Conference", "Western", None),
        "fc dallas":               ("Western Conference", "Western", None),
        "houston dynamo fc":       ("Western Conference", "Western", None),
        "l.a. galaxy":             ("Western Conference", "Western", None),
        "la galaxy":               ("Western Conference", "Western", None),
        "lafc":                    ("Western Conference", "Western", None),
        "los angeles fc":          ("Western Conference", "Western", None),
        "minnesota united fc":     ("Western Conference", "Western", None),
        "portland timbers":        ("Western Conference", "Western", None),
        "real salt lake":          ("Western Conference", "Western", None),
        "san diego fc":            ("Western Conference", "Western", None),
        "san jose earthquakes":    ("Western Conference", "Western", None),
        "seattle sounders fc":     ("Western Conference", "Western", None),
        "sporting kansas city":    ("Western Conference", "Western", None),
        "vancouver whitecaps fc":  ("Western Conference", "Western", None),
    },
}


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
        source_api_endpoint=CFB_ACC_ENDPOINT,
        output_folder="ACC",
        teams=(),
        default_conference="ACC",
        default_conference_abbr="ACC",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/acc.png",
    ),
    "big_ten": FlashcardSet(
        code="big_ten",
        display_name="Big Ten",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_BIG_TEN_ENDPOINT,
        output_folder="BIG_TEN",
        teams=(),
        default_conference="Big Ten",
        default_conference_abbr="Big Ten",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/big_ten.png",
    ),
    "big_12": FlashcardSet(
        code="big_12",
        display_name="Big 12",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_BIG_12_ENDPOINT,
        output_folder="BIG_12",
        teams=(),
        default_conference="Big 12",
        default_conference_abbr="Big 12",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/big12.png",
    ),
    "sec": FlashcardSet(
        code="sec",
        display_name="SEC",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_SEC_ENDPOINT,
        output_folder="SEC",
        teams=(),
        default_conference="SEC",
        default_conference_abbr="SEC",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/sec.png",
    ),
    "mac": FlashcardSet(
        code="mac",
        display_name="MAC",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_MAC_ENDPOINT,
        output_folder="MAC",
        teams=(),
        default_conference="MAC",
        default_conference_abbr="MAC",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/mac.png",
    ),
    "aac": FlashcardSet(
        code="aac",
        display_name="AAC",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_AAC_ENDPOINT,
        output_folder="AAC",
        teams=(),
        default_conference="AAC",
        default_conference_abbr="AAC",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/aac.png",
    ),
    "ivy_league": FlashcardSet(
        code="ivy_league",
        display_name="Ivy League",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_IVY_ENDPOINT,
        output_folder="IVY_LEAGUE",
        teams=(),
        default_conference="Ivy League",
        default_conference_abbr="Ivy",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/ivy.png",
    ),
    "pac_12": FlashcardSet(
        code="pac_12",
        display_name="Pac-12",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_PAC_12_ENDPOINT,
        output_folder="PAC_12",
        teams=(),
        default_conference="Pac-12",
        default_conference_abbr="Pac-12",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/pac12.png",
    ),
    "cfb_all": FlashcardSet(
        code="cfb_all",
        display_name="All Conferences",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=None,
        source_api_endpoints=(
            ConferenceEndpoint(CFB_ACC_ENDPOINT,     "ACC",        "ACC"),
            ConferenceEndpoint(CFB_BIG_TEN_ENDPOINT, "Big Ten",    "Big Ten"),
            ConferenceEndpoint(CFB_BIG_12_ENDPOINT,  "Big 12",     "Big 12"),
            ConferenceEndpoint(CFB_SEC_ENDPOINT,     "SEC",        "SEC"),
            ConferenceEndpoint(CFB_MAC_ENDPOINT,     "MAC",        "MAC"),
            ConferenceEndpoint(CFB_AAC_ENDPOINT,     "AAC",        "AAC"),
            ConferenceEndpoint(CFB_IVY_ENDPOINT,     "Ivy League", "Ivy"),
            ConferenceEndpoint(CFB_PAC_12_ENDPOINT,  "Pac-12",     "Pac-12"),
        ),
        output_folder="CFB_ALL",
        teams=(),
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

    # Known compound (two-word) mascot names — mainly needed for hardcoded teams
    # that lack location_name/mascot_name fields (e.g. static MLB definitions).
    two_word_mascots = {
        "white sox", "red sox", "blue jays",         # MLB
        "blue jackets", "maple leafs", "red wings",  # NHL (fallback)
        "golden knights", "golden state",            # NHL/NBA (fallback)
    }
    if len(parts) >= 3 and " ".join(parts[-2:]).lower() in two_word_mascots:
        return " ".join(parts[:-2]), " ".join(parts[-2:])

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
