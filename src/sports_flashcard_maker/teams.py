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
    abbreviation: str | None = None


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
        # Geographic / league abbreviations
        "DC", "LA", "NY", "SF", "NJ", "FC", "USA",
        # Pro league abbreviations
        "MLB", "NFL", "NBA", "NHL", "MLS", "WNBA", "AHL", "AAC", "ACC",
        # FBS school acronyms
        "BYU", "ECU", "FAU", "FIU", "FLA", "LSU", "SMU", "TCU",
        "UAB", "UCLA", "UCF", "UNLV", "UNT", "USC", "USF",
        "UTEP", "UTSA",
        # FCS school acronyms
        "APSU", "EKU", "ETSU", "EWU", "LIU", "MVSU", "NDSU",
        "NISU", "SDSU", "SFA", "SHSU", "SIU", "UIW", "UCA", "VMI",
        "WKU",
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
    Team("Arizona Diamondbacks",  "ari", conference="National League",  conference_abbr="NL", division="West",    abbreviation="ARI"),
    Team("Atlanta Braves",        "atl", conference="National League",  conference_abbr="NL", division="East",    abbreviation="ATL"),
    Team("Baltimore Orioles",     "bal", conference="American League",  conference_abbr="AL", division="East",    abbreviation="BAL"),
    Team("Boston Red Sox",        "bos", conference="American League",  conference_abbr="AL", division="East",    abbreviation="BOS"),
    Team("Chicago Cubs",          "chc", conference="National League",  conference_abbr="NL", division="Central", abbreviation="CHC"),
    Team("Chicago White Sox",     "chw", conference="American League",  conference_abbr="AL", division="Central", abbreviation="CWS"),
    Team("Cincinnati Reds",       "cin", conference="National League",  conference_abbr="NL", division="Central", abbreviation="CIN"),
    Team("Cleveland Guardians",   "cle", conference="American League",  conference_abbr="AL", division="Central", abbreviation="CLE"),
    Team("Colorado Rockies",      "col", conference="National League",  conference_abbr="NL", division="West",    abbreviation="COL"),
    Team("Detroit Tigers",        "det", conference="American League",  conference_abbr="AL", division="Central", abbreviation="DET"),
    Team("Houston Astros",        "hou", conference="American League",  conference_abbr="AL", division="West",    abbreviation="HOU"),
    Team("Kansas City Royals",    "kc",  conference="American League",  conference_abbr="AL", division="Central", abbreviation="KC"),
    Team("Los Angeles Angels",    "laa", conference="American League",  conference_abbr="AL", division="West",    abbreviation="LAA"),
    Team("Los Angeles Dodgers",   "lad", conference="National League",  conference_abbr="NL", division="West",    abbreviation="LAD"),
    Team("Miami Marlins",         "mia", conference="National League",  conference_abbr="NL", division="East",    abbreviation="MIA"),
    Team("Milwaukee Brewers",     "mil", conference="National League",  conference_abbr="NL", division="Central", abbreviation="MIL"),
    Team("Minnesota Twins",       "min", conference="American League",  conference_abbr="AL", division="Central", abbreviation="MIN"),
    Team("New York Mets",         "nym", conference="National League",  conference_abbr="NL", division="East",    abbreviation="NYM"),
    Team("New York Yankees",      "nyy", conference="American League",  conference_abbr="AL", division="East",    abbreviation="NYY"),
    Team("Athletics",             "oak", conference="American League",  conference_abbr="AL", division="West",    abbreviation="ATH"),
    Team("Philadelphia Phillies", "phi", conference="National League",  conference_abbr="NL", division="East",    abbreviation="PHI"),
    Team("Pittsburgh Pirates",    "pit", conference="National League",  conference_abbr="NL", division="Central", abbreviation="PIT"),
    Team("San Diego Padres",      "sd",  conference="National League",  conference_abbr="NL", division="West",    abbreviation="SD"),
    Team("San Francisco Giants",  "sf",  conference="National League",  conference_abbr="NL", division="West",    abbreviation="SF"),
    Team("Seattle Mariners",      "sea", conference="American League",  conference_abbr="AL", division="West",    abbreviation="SEA"),
    Team("St. Louis Cardinals",   "stl", conference="National League",  conference_abbr="NL", division="Central", abbreviation="STL"),
    Team("Tampa Bay Rays",        "tb",  conference="American League",  conference_abbr="AL", division="East",    abbreviation="TB"),
    Team("Texas Rangers",         "tex", conference="American League",  conference_abbr="AL", division="West",    abbreviation="TEX"),
    Team("Toronto Blue Jays",     "tor", conference="American League",  conference_abbr="AL", division="East",    abbreviation="TOR"),
    Team("Washington Nationals",  "wsh", conference="National League",  conference_abbr="NL", division="East",    abbreviation="WSH"),
)


ACC_TEAMS: tuple[Team, ...] = (
    Team("Boston College",  api_lookup_name="Boston College",  conference="ACC", conference_abbr="ACC", abbreviation="BC"),
    Team("California",      api_lookup_name="California",      conference="ACC", conference_abbr="ACC", abbreviation="CAL"),
    Team("Clemson",         api_lookup_name="Clemson",         conference="ACC", conference_abbr="ACC", abbreviation="CLEM"),
    Team("Duke",            api_lookup_name="Duke",            conference="ACC", conference_abbr="ACC", abbreviation="DUKE"),
    Team("Florida State",   api_lookup_name="Florida St",      conference="ACC", conference_abbr="ACC", abbreviation="FSU"),
    Team("Georgia Tech",    api_lookup_name="Georgia Tech",    conference="ACC", conference_abbr="ACC", abbreviation="GT"),
    Team("Louisville",      api_lookup_name="Louisville",      conference="ACC", conference_abbr="ACC", abbreviation="LOU"),
    Team("Miami",           api_lookup_name="Miami",           conference="ACC", conference_abbr="ACC", abbreviation="MIA"),
    Team("NC State",        api_lookup_name="NC State",        conference="ACC", conference_abbr="ACC", abbreviation="NCST"),
    Team("North Carolina",  api_lookup_name="North Carolina",  conference="ACC", conference_abbr="ACC", abbreviation="UNC"),
    Team("Pittsburgh",      api_lookup_name="Pitt",            conference="ACC", conference_abbr="ACC", abbreviation="PITT"),
    Team("SMU",             api_lookup_name="SMU",             conference="ACC", conference_abbr="ACC", abbreviation="SMU"),
    Team("Stanford",        api_lookup_name="Stanford",        conference="ACC", conference_abbr="ACC", abbreviation="STAN"),
    Team("Syracuse",        api_lookup_name="Syracuse",        conference="ACC", conference_abbr="ACC", abbreviation="SYR"),
    Team("Virginia",        api_lookup_name="Virginia",        conference="ACC", conference_abbr="ACC", abbreviation="UVA"),
    Team("Virginia Tech",   api_lookup_name="Virginia Tech",   conference="ACC", conference_abbr="ACC", abbreviation="VT"),
    Team("Wake Forest",     api_lookup_name="Wake Forest",     conference="ACC", conference_abbr="ACC", abbreviation="WAKE"),
)


BIG_TEN_TEAMS: tuple[Team, ...] = (
    Team("Illinois",       api_lookup_name="Illinois",     conference="Big Ten", conference_abbr="Big Ten", abbreviation="ILL"),
    Team("Indiana",        api_lookup_name="Indiana",      conference="Big Ten", conference_abbr="Big Ten", abbreviation="IU"),
    Team("Iowa",           api_lookup_name="Iowa",         conference="Big Ten", conference_abbr="Big Ten", abbreviation="IOWA"),
    Team("Maryland",       api_lookup_name="Maryland",     conference="Big Ten", conference_abbr="Big Ten", abbreviation="MD"),
    Team("Michigan",       api_lookup_name="Michigan",     conference="Big Ten", conference_abbr="Big Ten", abbreviation="MICH"),
    Team("Michigan State", api_lookup_name="Michigan St",  conference="Big Ten", conference_abbr="Big Ten", abbreviation="MSU"),
    Team("Minnesota",      api_lookup_name="Minnesota",    conference="Big Ten", conference_abbr="Big Ten", abbreviation="MINN"),
    Team("Nebraska",       api_lookup_name="Nebraska",     conference="Big Ten", conference_abbr="Big Ten", abbreviation="NEB"),
    Team("Northwestern",   api_lookup_name="Northwestern", conference="Big Ten", conference_abbr="Big Ten", abbreviation="NW"),
    Team("Ohio State",     api_lookup_name="Ohio State",   conference="Big Ten", conference_abbr="Big Ten", abbreviation="OSU"),
    Team("Oregon",         api_lookup_name="Oregon",       conference="Big Ten", conference_abbr="Big Ten", abbreviation="ORE"),
    Team("Penn State",     api_lookup_name="Penn State",   conference="Big Ten", conference_abbr="Big Ten", abbreviation="PSU"),
    Team("Purdue",         api_lookup_name="Purdue",       conference="Big Ten", conference_abbr="Big Ten", abbreviation="PUR"),
    Team("Rutgers",        api_lookup_name="Rutgers",      conference="Big Ten", conference_abbr="Big Ten", abbreviation="RU"),
    Team("UCLA",           api_lookup_name="UCLA",         conference="Big Ten", conference_abbr="Big Ten", abbreviation="UCLA"),
    Team("USC",            api_lookup_name="USC",          conference="Big Ten", conference_abbr="Big Ten", abbreviation="USC"),
    Team("Washington",     api_lookup_name="Washington",   conference="Big Ten", conference_abbr="Big Ten", abbreviation="WASH"),
    Team("Wisconsin",      api_lookup_name="Wisconsin",    conference="Big Ten", conference_abbr="Big Ten", abbreviation="WIS"),
)


BIG_12_TEAMS: tuple[Team, ...] = (
    Team("Arizona",       api_lookup_name="Arizona",       conference="Big 12", conference_abbr="Big 12", abbreviation="ARIZ"),
    Team("Arizona State", api_lookup_name="Arizona St",    conference="Big 12", conference_abbr="Big 12", abbreviation="ASU"),
    Team("Baylor",        api_lookup_name="Baylor",        conference="Big 12", conference_abbr="Big 12", abbreviation="BAY"),
    Team("BYU",           api_lookup_name="BYU",           conference="Big 12", conference_abbr="Big 12", abbreviation="BYU"),
    Team("Cincinnati",    api_lookup_name="Cincinnati",    conference="Big 12", conference_abbr="Big 12", abbreviation="CIN"),
    Team("Colorado",      api_lookup_name="Colorado",      conference="Big 12", conference_abbr="Big 12", abbreviation="COLO"),
    Team("Houston",       api_lookup_name="Houston",       conference="Big 12", conference_abbr="Big 12", abbreviation="HOU"),
    Team("Iowa State",    api_lookup_name="Iowa State",    conference="Big 12", conference_abbr="Big 12", abbreviation="ISU"),
    Team("Kansas",        api_lookup_name="Kansas",        conference="Big 12", conference_abbr="Big 12", abbreviation="KU"),
    Team("Kansas State",  api_lookup_name="Kansas St",     conference="Big 12", conference_abbr="Big 12", abbreviation="KSU"),
    Team("Oklahoma State",api_lookup_name="Oklahoma St",   conference="Big 12", conference_abbr="Big 12", abbreviation="OKST"),
    Team("TCU",           api_lookup_name="TCU",           conference="Big 12", conference_abbr="Big 12", abbreviation="TCU"),
    Team("Texas Tech",    api_lookup_name="Texas Tech",    conference="Big 12", conference_abbr="Big 12", abbreviation="TTU"),
    Team("UCF",           api_lookup_name="UCF",           conference="Big 12", conference_abbr="Big 12", abbreviation="UCF"),
    Team("Utah",          api_lookup_name="Utah",          conference="Big 12", conference_abbr="Big 12", abbreviation="UTAH"),
    Team("West Virginia", api_lookup_name="West Virginia", conference="Big 12", conference_abbr="Big 12", abbreviation="WVU"),
)


SEC_TEAMS: tuple[Team, ...] = (
    Team("Alabama",          api_lookup_name="Alabama",         conference="SEC", conference_abbr="SEC", abbreviation="ALA"),
    Team("Arkansas",         api_lookup_name="Arkansas",        conference="SEC", conference_abbr="SEC", abbreviation="ARK"),
    Team("Auburn",           api_lookup_name="Auburn",          conference="SEC", conference_abbr="SEC", abbreviation="AUB"),
    Team("Florida",          api_lookup_name="Florida",         conference="SEC", conference_abbr="SEC", abbreviation="FLA"),
    Team("Georgia",          api_lookup_name="Georgia",         conference="SEC", conference_abbr="SEC", abbreviation="UGA"),
    Team("Kentucky",         api_lookup_name="Kentucky",        conference="SEC", conference_abbr="SEC", abbreviation="UK"),
    Team("LSU",              api_lookup_name="LSU",             conference="SEC", conference_abbr="SEC", abbreviation="LSU"),
    Team("Mississippi State",api_lookup_name="Mississippi St",  conference="SEC", conference_abbr="SEC", abbreviation="MSST"),
    Team("Missouri",         api_lookup_name="Missouri",        conference="SEC", conference_abbr="SEC", abbreviation="MIZ"),
    Team("Oklahoma",         api_lookup_name="Oklahoma",        conference="SEC", conference_abbr="SEC", abbreviation="OU"),
    Team("Ole Miss",         api_lookup_name="Ole Miss",        conference="SEC", conference_abbr="SEC", abbreviation="MISS"),
    Team("South Carolina",   api_lookup_name="South Carolina",  conference="SEC", conference_abbr="SEC", abbreviation="SC"),
    Team("Tennessee",        api_lookup_name="Tennessee",       conference="SEC", conference_abbr="SEC", abbreviation="TENN"),
    Team("Texas",            api_lookup_name="Texas",           conference="SEC", conference_abbr="SEC", abbreviation="TEX"),
    Team("Texas A&M",        api_lookup_name="Texas A&M",       conference="SEC", conference_abbr="SEC", abbreviation="TAMU"),
    Team("Vanderbilt",       api_lookup_name="Vanderbilt",      conference="SEC", conference_abbr="SEC", abbreviation="VAN"),
)


MAC_TEAMS: tuple[Team, ...] = (
    Team("Akron",             api_lookup_name="Akron",         conference="MAC", conference_abbr="MAC", abbreviation="AKR"),
    Team("Ball State",        api_lookup_name="Ball State",    conference="MAC", conference_abbr="MAC", abbreviation="BALL"),
    Team("Bowling Green",     api_lookup_name="Bowling Green", conference="MAC", conference_abbr="MAC", abbreviation="BGSU"),
    Team("Buffalo",           api_lookup_name="Buffalo",       conference="MAC", conference_abbr="MAC", abbreviation="BUFF"),
    Team("Central Michigan",  api_lookup_name="C Michigan",    conference="MAC", conference_abbr="MAC", abbreviation="CMU"),
    Team("Eastern Michigan",  api_lookup_name="E Michigan",    conference="MAC", conference_abbr="MAC", abbreviation="EMU"),
    Team("Kent State",        api_lookup_name="Kent State",    conference="MAC", conference_abbr="MAC", abbreviation="KENT"),
    Team("Massachusetts",     api_lookup_name="UMass",         conference="MAC", conference_abbr="MAC", abbreviation="UMASS"),
    Team("Miami (OH)",        api_lookup_name="Miami OH",      conference="MAC", conference_abbr="MAC", abbreviation="MIOH"),
    Team("Northern Illinois", api_lookup_name="N Illinois",    conference="MAC", conference_abbr="MAC", abbreviation="NIU"),
    Team("Ohio",              api_lookup_name="Ohio",          conference="MAC", conference_abbr="MAC", abbreviation="OHIO"),
    Team("Toledo",            api_lookup_name="Toledo",        conference="MAC", conference_abbr="MAC", abbreviation="TOL"),
    Team("Western Michigan",  api_lookup_name="W Michigan",    conference="MAC", conference_abbr="MAC", abbreviation="WMU"),
)


AAC_TEAMS: tuple[Team, ...] = (
    Team("Army",          api_lookup_name="Army",          conference="AAC", conference_abbr="AAC", abbreviation="ARMY"),
    Team("Charlotte",     api_lookup_name="Charlotte",     conference="AAC", conference_abbr="AAC", abbreviation="CLT"),
    Team("East Carolina", api_lookup_name="East Carolina", conference="AAC", conference_abbr="AAC", abbreviation="ECU"),
    Team("FAU",           api_lookup_name="FAU",           conference="AAC", conference_abbr="AAC", abbreviation="FAU"),
    Team("Memphis",       api_lookup_name="Memphis",       conference="AAC", conference_abbr="AAC", abbreviation="MEM"),
    Team("Navy",          api_lookup_name="Navy",          conference="AAC", conference_abbr="AAC", abbreviation="NAVY"),
    Team("North Texas",   api_lookup_name="North Texas",   conference="AAC", conference_abbr="AAC", abbreviation="UNT"),
    Team("Rice",          api_lookup_name="Rice",          conference="AAC", conference_abbr="AAC", abbreviation="RICE"),
    Team("South Florida", api_lookup_name="South Florida", conference="AAC", conference_abbr="AAC", abbreviation="USF"),
    Team("Temple",        api_lookup_name="Temple",        conference="AAC", conference_abbr="AAC", abbreviation="TEM"),
    Team("Tulane",        api_lookup_name="Tulane",        conference="AAC", conference_abbr="AAC", abbreviation="TULN"),
    Team("Tulsa",         api_lookup_name="Tulsa",         conference="AAC", conference_abbr="AAC", abbreviation="TLSA"),
    Team("UAB",           api_lookup_name="UAB",           conference="AAC", conference_abbr="AAC", abbreviation="UAB"),
    Team("UTSA",          api_lookup_name="UTSA",          conference="AAC", conference_abbr="AAC", abbreviation="UTSA"),
)


IVY_LEAGUE_TEAMS: tuple[Team, ...] = (
    Team("Brown",        api_lookup_name="Brown",      conference="Ivy League", conference_abbr="Ivy", abbreviation="BRWN"),
    Team("Columbia",     api_lookup_name="Columbia",   conference="Ivy League", conference_abbr="Ivy", abbreviation="CLMB"),
    Team("Cornell",      api_lookup_name="Cornell",    conference="Ivy League", conference_abbr="Ivy", abbreviation="CRNL"),
    Team("Dartmouth",    api_lookup_name="Dartmouth",  conference="Ivy League", conference_abbr="Ivy", abbreviation="DART"),
    Team("Harvard",      api_lookup_name="Harvard",    conference="Ivy League", conference_abbr="Ivy", abbreviation="HARV"),
    Team("Pennsylvania", api_lookup_name="Penn",       conference="Ivy League", conference_abbr="Ivy", abbreviation="PENN"),
    Team("Princeton",    api_lookup_name="Princeton",  conference="Ivy League", conference_abbr="Ivy", abbreviation="PRIN"),
    Team("Yale",         api_lookup_name="Yale",       conference="Ivy League", conference_abbr="Ivy", abbreviation="YALE"),
)


PAC_12_TEAMS: tuple[Team, ...] = (
    Team("Oregon State",    api_lookup_name="Oregon St",      conference="Pac-12", conference_abbr="Pac-12", abbreviation="ORST"),
    Team("Washington State",api_lookup_name="Washington St",  conference="Pac-12", conference_abbr="Pac-12", abbreviation="WSU"),
)

# FBS Independents
FBS_INDEPENDENTS_TEAMS: tuple[Team, ...] = (
    Team("Notre Dame",  api_lookup_name="Notre Dame", conference="FBS Independents", conference_abbr="Ind", abbreviation="ND"),
    Team("UConn",       api_lookup_name="UConn",      conference="FBS Independents", conference_abbr="Ind", abbreviation="UCONN"),
)

# --- FBS Group of 5 ---

MOUNTAIN_WEST_TEAMS: tuple[Team, ...] = (
    Team("Air Force",       api_lookup_name="Air Force",   conference="Mountain West", conference_abbr="MWC", abbreviation="AFA"),
    Team("Boise State",     api_lookup_name="Boise St",    conference="Mountain West", conference_abbr="MWC", abbreviation="BSU"),
    Team("Colorado State",  api_lookup_name="Colorado St", conference="Mountain West", conference_abbr="MWC", abbreviation="CSU"),
    Team("Fresno State",    api_lookup_name="Fresno St",   conference="Mountain West", conference_abbr="MWC", abbreviation="FRES"),
    Team("Hawai'i",         api_lookup_name="Hawai'i",     conference="Mountain West", conference_abbr="MWC", abbreviation="HAW"),
    Team("Nevada",          api_lookup_name="Nevada",      conference="Mountain West", conference_abbr="MWC", abbreviation="NEV"),
    Team("New Mexico",      api_lookup_name="New Mexico",  conference="Mountain West", conference_abbr="MWC", abbreviation="UNM"),
    Team("San Diego State", api_lookup_name="San Diego St",conference="Mountain West", conference_abbr="MWC", abbreviation="SDSU"),
    Team("San Jos\u00e9 State", api_lookup_name="San Jos\u00e9 St", conference="Mountain West", conference_abbr="MWC", abbreviation="SJSU"),
    Team("UNLV",            api_lookup_name="UNLV",        conference="Mountain West", conference_abbr="MWC", abbreviation="UNLV"),
    Team("Utah State",      api_lookup_name="Utah State",  conference="Mountain West", conference_abbr="MWC", abbreviation="USU"),
    Team("Wyoming",         api_lookup_name="Wyoming",     conference="Mountain West", conference_abbr="MWC", abbreviation="WYO"),
)

SUN_BELT_TEAMS: tuple[Team, ...] = (
    Team("Appalachian State",  api_lookup_name="App State",      conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="APP"),
    Team("Arkansas State",     api_lookup_name="Arkansas St",    conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="ARST"),
    Team("Coastal Carolina",   api_lookup_name="Coastal",        conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="CCU"),
    Team("Georgia Southern",   api_lookup_name="GA Southern",    conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="GASO"),
    Team("Georgia State",      api_lookup_name="Georgia St",     conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="GAST"),
    Team("James Madison",      api_lookup_name="James Madison",  conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="JMU"),
    Team("Louisiana",          api_lookup_name="Louisiana",      conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="ULL"),
    Team("Marshall",           api_lookup_name="Marshall",       conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="MRSH"),
    Team("Old Dominion",       api_lookup_name="Old Dominion",   conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="ODU"),
    Team("South Alabama",      api_lookup_name="South Alabama",  conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="USA"),
    Team("Southern Miss",      api_lookup_name="Southern Miss",  conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="USM"),
    Team("Texas State",        api_lookup_name="Texas St",       conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="TXST"),
    Team("Troy",               api_lookup_name="Troy",           conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="TROY"),
    Team("UL Monroe",          api_lookup_name="UL Monroe",      conference="Sun Belt", conference_abbr="Sun Belt", abbreviation="ULM"),
)

CUSA_TEAMS: tuple[Team, ...] = (
    Team("Delaware",         api_lookup_name="Delaware",       conference="Conference USA", conference_abbr="CUSA", abbreviation="DEL"),
    Team("FIU",              api_lookup_name="FIU",            conference="Conference USA", conference_abbr="CUSA", abbreviation="FIU"),
    Team("Jacksonville State",api_lookup_name="Jax State",    conference="Conference USA", conference_abbr="CUSA", abbreviation="JVST"),
    Team("Kennesaw State",   api_lookup_name="Kennesaw St",    conference="Conference USA", conference_abbr="CUSA", abbreviation="KENN"),
    Team("Liberty",          api_lookup_name="Liberty",        conference="Conference USA", conference_abbr="CUSA", abbreviation="LIB"),
    Team("Louisiana Tech",   api_lookup_name="Louisiana Tech", conference="Conference USA", conference_abbr="CUSA", abbreviation="LT"),
    Team("Middle Tennessee", api_lookup_name="MTSU",           conference="Conference USA", conference_abbr="CUSA", abbreviation="MTSU"),
    Team("Missouri State",   api_lookup_name="Missouri St",    conference="Conference USA", conference_abbr="CUSA", abbreviation="MOST"),
    Team("New Mexico State", api_lookup_name="New Mexico St",  conference="Conference USA", conference_abbr="CUSA", abbreviation="NMST"),
    Team("Sam Houston",      api_lookup_name="Sam Houston",    conference="Conference USA", conference_abbr="CUSA", abbreviation="SHSU"),
    Team("UTEP",             api_lookup_name="UTEP",           conference="Conference USA", conference_abbr="CUSA", abbreviation="UTEP"),
    Team("Western Kentucky", api_lookup_name="Western KY",     conference="Conference USA", conference_abbr="CUSA", abbreviation="WKU"),
)

# --- FCS Conferences ---

BIG_SKY_TEAMS: tuple[Team, ...] = (
    Team("Cal Poly",         api_lookup_name="Cal Poly",      conference="Big Sky", conference_abbr="Big Sky", abbreviation="CP"),
    Team("Eastern Washington",api_lookup_name="E Washington", conference="Big Sky", conference_abbr="Big Sky", abbreviation="EWU"),
    Team("Idaho State",      api_lookup_name="Idaho St",      conference="Big Sky", conference_abbr="Big Sky", abbreviation="ISU"),
    Team("Idaho",            api_lookup_name="Idaho",         conference="Big Sky", conference_abbr="Big Sky", abbreviation="IDHO"),
    Team("Montana",          api_lookup_name="Montana",       conference="Big Sky", conference_abbr="Big Sky", abbreviation="MONT"),
    Team("Montana State",    api_lookup_name="Montana St",    conference="Big Sky", conference_abbr="Big Sky", abbreviation="MTST"),
    Team("Northern Arizona", api_lookup_name="N Arizona",     conference="Big Sky", conference_abbr="Big Sky", abbreviation="NAU"),
    Team("Northern Colorado",api_lookup_name="N Colorado",    conference="Big Sky", conference_abbr="Big Sky", abbreviation="UNC"),
    Team("Portland State",   api_lookup_name="Portland St",   conference="Big Sky", conference_abbr="Big Sky", abbreviation="PSU"),
    Team("Sacramento State", api_lookup_name="Sacramento St", conference="Big Sky", conference_abbr="Big Sky", abbreviation="SAC"),
    Team("UC Davis",         api_lookup_name="UC Davis",      conference="Big Sky", conference_abbr="Big Sky", abbreviation="UCD"),
    Team("Weber State",      api_lookup_name="Weber St",      conference="Big Sky", conference_abbr="Big Sky", abbreviation="WSU"),
)

CAA_TEAMS: tuple[Team, ...] = (
    Team("Bryant",           api_lookup_name="Bryant",         conference="CAA Football", conference_abbr="CAA", abbreviation="BRYA"),
    Team("Campbell",         api_lookup_name="Campbell",       conference="CAA Football", conference_abbr="CAA", abbreviation="CAMP"),
    Team("Elon",             api_lookup_name="Elon",           conference="CAA Football", conference_abbr="CAA", abbreviation="ELON"),
    Team("Hampton",          api_lookup_name="Hampton",        conference="CAA Football", conference_abbr="CAA", abbreviation="HAMP"),
    Team("Maine",            api_lookup_name="Maine",          conference="CAA Football", conference_abbr="CAA", abbreviation="ME"),
    Team("Monmouth",         api_lookup_name="Monmouth",       conference="CAA Football", conference_abbr="CAA", abbreviation="MNMO"),
    Team("New Hampshire",    api_lookup_name="New Hampshire",  conference="CAA Football", conference_abbr="CAA", abbreviation="UNH"),
    Team("NC A&T",           api_lookup_name="NC A&T",         conference="CAA Football", conference_abbr="CAA", abbreviation="NCAT"),
    Team("Rhode Island",     api_lookup_name="Rhode Island",   conference="CAA Football", conference_abbr="CAA", abbreviation="URI"),
    Team("Stony Brook",      api_lookup_name="Stony Brook",    conference="CAA Football", conference_abbr="CAA", abbreviation="SBU"),
    Team("Towson",           api_lookup_name="Towson",         conference="CAA Football", conference_abbr="CAA", abbreviation="TOW"),
    Team("UAlbany",          api_lookup_name="UAlbany",        conference="CAA Football", conference_abbr="CAA", abbreviation="ALBA"),
    Team("Villanova",        api_lookup_name="Villanova",      conference="CAA Football", conference_abbr="CAA", abbreviation="VILL"),
    Team("William & Mary",   api_lookup_name="William & Mary", conference="CAA Football", conference_abbr="CAA", abbreviation="WM"),
)

MEAC_TEAMS: tuple[Team, ...] = (
    Team("Delaware State",         api_lookup_name="Delaware St",  conference="MEAC", conference_abbr="MEAC", abbreviation="DSU"),
    Team("Howard",                 api_lookup_name="Howard",       conference="MEAC", conference_abbr="MEAC", abbreviation="HOW"),
    Team("Morgan State",           api_lookup_name="Morgan St",    conference="MEAC", conference_abbr="MEAC", abbreviation="MORG"),
    Team("Norfolk State",          api_lookup_name="Norfolk St",   conference="MEAC", conference_abbr="MEAC", abbreviation="NSU"),
    Team("North Carolina Central", api_lookup_name="NC Central",   conference="MEAC", conference_abbr="MEAC", abbreviation="NCCU"),
    Team("South Carolina State",   api_lookup_name="SC State",     conference="MEAC", conference_abbr="MEAC", abbreviation="SCST"),
)

MVFC_TEAMS: tuple[Team, ...] = (
    Team("Illinois State",    api_lookup_name="Illinois St",   conference="MVFC", conference_abbr="MVFC", abbreviation="ILST"),
    Team("Indiana State",     api_lookup_name="Indiana St",    conference="MVFC", conference_abbr="MVFC", abbreviation="INST"),
    Team("Murray State",      api_lookup_name="Murray St",     conference="MVFC", conference_abbr="MVFC", abbreviation="MUR"),
    Team("North Dakota",      api_lookup_name="North Dakota",  conference="MVFC", conference_abbr="MVFC", abbreviation="UND"),
    Team("North Dakota State",api_lookup_name="N Dakota St",   conference="MVFC", conference_abbr="MVFC", abbreviation="NDSU"),
    Team("Northern Iowa",     api_lookup_name="Northern Iowa", conference="MVFC", conference_abbr="MVFC", abbreviation="UNI"),
    Team("South Dakota",      api_lookup_name="South Dakota",  conference="MVFC", conference_abbr="MVFC", abbreviation="USD"),
    Team("South Dakota State",api_lookup_name="S Dakota St",   conference="MVFC", conference_abbr="MVFC", abbreviation="SDSU"),
    Team("Southern Illinois", api_lookup_name="S Illinois",    conference="MVFC", conference_abbr="MVFC", abbreviation="SIU"),
    Team("Youngstown State",  api_lookup_name="Youngstown St", conference="MVFC", conference_abbr="MVFC", abbreviation="YSU"),
)

NEC_TEAMS: tuple[Team, ...] = (
    Team("Central Connecticut",  api_lookup_name="C Connecticut",  conference="NEC", conference_abbr="NEC", abbreviation="CCSU"),
    Team("Duquesne",             api_lookup_name="Duquesne",       conference="NEC", conference_abbr="NEC", abbreviation="DUQ"),
    Team("LIU",                  api_lookup_name="Long Island",    conference="NEC", conference_abbr="NEC", abbreviation="LIU"),
    Team("Mercyhurst",           api_lookup_name="Mercyhurst",     conference="NEC", conference_abbr="NEC", abbreviation="MHU"),
    Team("New Haven",            api_lookup_name="New Haven",      conference="NEC", conference_abbr="NEC", abbreviation="UNH"),
    Team("Robert Morris",        api_lookup_name="Robert Morris",  conference="NEC", conference_abbr="NEC", abbreviation="RMU"),
    Team("Saint Francis",        api_lookup_name="Saint Francis",  conference="NEC", conference_abbr="NEC", abbreviation="SFU"),
    Team("Stonehill",            api_lookup_name="Stonehill",      conference="NEC", conference_abbr="NEC", abbreviation="STON"),
    Team("Wagner",               api_lookup_name="Wagner",         conference="NEC", conference_abbr="NEC", abbreviation="WAG"),
)

OVC_BIG_SOUTH_TEAMS: tuple[Team, ...] = (
    Team("Charleston Southern",      api_lookup_name="Charleston So",  conference="OVC-Big South", conference_abbr="OVC-BS", abbreviation="CSU"),
    Team("Eastern Illinois",         api_lookup_name="E Illinois",     conference="OVC-Big South", conference_abbr="OVC-BS", abbreviation="EIU"),
    Team("Gardner-Webb",             api_lookup_name="Gardner-Webb",   conference="OVC-Big South", conference_abbr="OVC-BS", abbreviation="GWU"),
    Team("Lindenwood",               api_lookup_name="Lindenwood",     conference="OVC-Big South", conference_abbr="OVC-BS", abbreviation="LU"),
    Team("Southeast Missouri State", api_lookup_name="SE Missouri",    conference="OVC-Big South", conference_abbr="OVC-BS", abbreviation="SEMO"),
    Team("Tennessee State",          api_lookup_name="Tennessee St",   conference="OVC-Big South", conference_abbr="OVC-BS", abbreviation="TSU"),
    Team("Tennessee Tech",           api_lookup_name="Tennessee Tech", conference="OVC-Big South", conference_abbr="OVC-BS", abbreviation="TTU"),
    Team("UT Martin",                api_lookup_name="UT Martin",      conference="OVC-Big South", conference_abbr="OVC-BS", abbreviation="UTM"),
    Team("Western Illinois",         api_lookup_name="W Illinois",     conference="OVC-Big South", conference_abbr="OVC-BS", abbreviation="WIU"),
)

PATRIOT_TEAMS: tuple[Team, ...] = (
    Team("Bucknell",    api_lookup_name="Bucknell",   conference="Patriot League", conference_abbr="Patriot", abbreviation="BUCK"),
    Team("Colgate",     api_lookup_name="Colgate",    conference="Patriot League", conference_abbr="Patriot", abbreviation="COLG"),
    Team("Fordham",     api_lookup_name="Fordham",    conference="Patriot League", conference_abbr="Patriot", abbreviation="FOR"),
    Team("Georgetown",  api_lookup_name="Georgetown", conference="Patriot League", conference_abbr="Patriot", abbreviation="GTWN"),
    Team("Holy Cross",  api_lookup_name="Holy Cross", conference="Patriot League", conference_abbr="Patriot", abbreviation="HC"),
    Team("Lafayette",   api_lookup_name="Lafayette",  conference="Patriot League", conference_abbr="Patriot", abbreviation="LAF"),
    Team("Lehigh",      api_lookup_name="Lehigh",     conference="Patriot League", conference_abbr="Patriot", abbreviation="LEH"),
    Team("Richmond",    api_lookup_name="Richmond",   conference="Patriot League", conference_abbr="Patriot", abbreviation="RICH"),
)

PIONEER_TEAMS: tuple[Team, ...] = (
    Team("Butler",          api_lookup_name="Butler",          conference="Pioneer Football League", conference_abbr="PFL", abbreviation="BUT"),
    Team("Davidson",        api_lookup_name="Davidson",        conference="Pioneer Football League", conference_abbr="PFL", abbreviation="DAV"),
    Team("Dayton",          api_lookup_name="Dayton",          conference="Pioneer Football League", conference_abbr="PFL", abbreviation="DAY"),
    Team("Drake",           api_lookup_name="Drake",           conference="Pioneer Football League", conference_abbr="PFL", abbreviation="DRKE"),
    Team("Marist",          api_lookup_name="Marist",          conference="Pioneer Football League", conference_abbr="PFL", abbreviation="MRST"),
    Team("Morehead State",  api_lookup_name="Morehead St",     conference="Pioneer Football League", conference_abbr="PFL", abbreviation="MORE"),
    Team("Presbyterian",    api_lookup_name="Presbyterian",    conference="Pioneer Football League", conference_abbr="PFL", abbreviation="PRES"),
    Team("San Diego",       api_lookup_name="San Diego",       conference="Pioneer Football League", conference_abbr="PFL", abbreviation="USD"),
    Team("St. Thomas",      api_lookup_name="St Thomas (MN)",  conference="Pioneer Football League", conference_abbr="PFL", abbreviation="STTH"),
    Team("Stetson",         api_lookup_name="Stetson",         conference="Pioneer Football League", conference_abbr="PFL", abbreviation="STET"),
    Team("Valparaiso",      api_lookup_name="Valparaiso",      conference="Pioneer Football League", conference_abbr="PFL", abbreviation="VALP"),
)

SOCON_TEAMS: tuple[Team, ...] = (
    Team("Chattanooga",    api_lookup_name="Chattanooga",  conference="SoCon", conference_abbr="SoCon", abbreviation="UTC"),
    Team("ETSU",           api_lookup_name="ETSU",         conference="SoCon", conference_abbr="SoCon", abbreviation="ETSU"),
    Team("Furman",         api_lookup_name="Furman",       conference="SoCon", conference_abbr="SoCon", abbreviation="FUR"),
    Team("Mercer",         api_lookup_name="Mercer",       conference="SoCon", conference_abbr="SoCon", abbreviation="MER"),
    Team("Samford",        api_lookup_name="Samford",      conference="SoCon", conference_abbr="SoCon", abbreviation="SAM"),
    Team("The Citadel",    api_lookup_name="The Citadel",  conference="SoCon", conference_abbr="SoCon", abbreviation="CIT"),
    Team("VMI",            api_lookup_name="VMI",          conference="SoCon", conference_abbr="SoCon", abbreviation="VMI"),
    Team("Western Carolina",api_lookup_name="W Carolina",  conference="SoCon", conference_abbr="SoCon", abbreviation="WCU"),
    Team("Wofford",        api_lookup_name="Wofford",      conference="SoCon", conference_abbr="SoCon", abbreviation="WOF"),
)

SOUTHLAND_TEAMS: tuple[Team, ...] = (
    Team("East Texas A&M",        api_lookup_name="E Texas A&M",    conference="Southland", conference_abbr="Southland", abbreviation="ETAM"),
    Team("Houston Christian",     api_lookup_name="Hou Christian",  conference="Southland", conference_abbr="Southland", abbreviation="HBU"),
    Team("Incarnate Word",        api_lookup_name="Incarnate Word", conference="Southland", conference_abbr="Southland", abbreviation="UIW"),
    Team("Lamar",                 api_lookup_name="Lamar",          conference="Southland", conference_abbr="Southland", abbreviation="LAM"),
    Team("McNeese",               api_lookup_name="McNeese",        conference="Southland", conference_abbr="Southland", abbreviation="MCNS"),
    Team("Nicholls",              api_lookup_name="Nicholls",       conference="Southland", conference_abbr="Southland", abbreviation="NICH"),
    Team("Northwestern State",    api_lookup_name="N'Western St",   conference="Southland", conference_abbr="Southland", abbreviation="NWST"),
    Team("SE Louisiana",          api_lookup_name="SE Louisiana",   conference="Southland", conference_abbr="Southland", abbreviation="SELU"),
    Team("Stephen F. Austin",     api_lookup_name="SF Austin",      conference="Southland", conference_abbr="Southland", abbreviation="SFA"),
    # UT Rio Grande Valley is in the Southland conference but has no ESPN logo — excluded
)

SWAC_TEAMS: tuple[Team, ...] = (
    Team("Alabama A&M",            api_lookup_name="Alabama A&M",    conference="SWAC", conference_abbr="SWAC", abbreviation="AAMU"),
    Team("Alabama State",          api_lookup_name="Alabama St",     conference="SWAC", conference_abbr="SWAC", abbreviation="ALST"),
    Team("Alcorn State",           api_lookup_name="Alcorn St",      conference="SWAC", conference_abbr="SWAC", abbreviation="ALCN"),
    Team("Arkansas-Pine Bluff",    api_lookup_name="AR-Pine Bluff",  conference="SWAC", conference_abbr="SWAC", abbreviation="UAPB"),
    Team("Bethune-Cookman",        api_lookup_name="Bethune",        conference="SWAC", conference_abbr="SWAC", abbreviation="BCU"),
    Team("Florida A&M",            api_lookup_name="Florida A&M",    conference="SWAC", conference_abbr="SWAC", abbreviation="FAMU"),
    Team("Grambling",              api_lookup_name="Grambling",      conference="SWAC", conference_abbr="SWAC", abbreviation="GRAM"),
    Team("Jackson State",          api_lookup_name="Jackson St",     conference="SWAC", conference_abbr="SWAC", abbreviation="JKST"),
    Team("Mississippi Valley State",api_lookup_name="Miss Valley St",conference="SWAC", conference_abbr="SWAC", abbreviation="MVSU"),
    Team("Prairie View A&M",       api_lookup_name="Prairie View",   conference="SWAC", conference_abbr="SWAC", abbreviation="PVAM"),
    Team("Southern",               api_lookup_name="Southern",       conference="SWAC", conference_abbr="SWAC", abbreviation="SOU"),
    Team("Texas Southern",         api_lookup_name="Texas Southern", conference="SWAC", conference_abbr="SWAC", abbreviation="TXSO"),
)

UAC_TEAMS: tuple[Team, ...] = (
    Team("Abilene Christian",  api_lookup_name="Abilene Chrstn", conference="United Athletic Conference", conference_abbr="UAC", abbreviation="ACU"),
    Team("Austin Peay",        api_lookup_name="Austin Peay",    conference="United Athletic Conference", conference_abbr="UAC", abbreviation="APSU"),
    Team("Central Arkansas",   api_lookup_name="C Arkansas",     conference="United Athletic Conference", conference_abbr="UAC", abbreviation="UCA"),
    Team("Eastern Kentucky",   api_lookup_name="E Kentucky",     conference="United Athletic Conference", conference_abbr="UAC", abbreviation="EKU"),
    Team("North Alabama",      api_lookup_name="North Alabama",  conference="United Athletic Conference", conference_abbr="UAC", abbreviation="UNA"),
    Team("Southern Utah",      api_lookup_name="Southern Utah",  conference="United Athletic Conference", conference_abbr="UAC", abbreviation="SUU"),
    Team("Tarleton State",     api_lookup_name="Tarleton St",    conference="United Athletic Conference", conference_abbr="UAC", abbreviation="TART"),
    Team("Utah Tech",          api_lookup_name="Utah Tech",      conference="United Athletic Conference", conference_abbr="UAC", abbreviation="UTEH"),
    Team("West Georgia",       api_lookup_name="West Georgia",   conference="United Athletic Conference", conference_abbr="UAC", abbreviation="UWG"),
)

FCS_INDEPENDENTS_TEAMS: tuple[Team, ...] = (
    Team("Merrimack",    api_lookup_name="Merrimack",    conference="FCS Independents", conference_abbr="Ind", abbreviation="MERR"),
    Team("Sacred Heart", api_lookup_name="Sacred Heart", conference="FCS Independents", conference_abbr="Ind", abbreviation="SHU"),
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


POWER_FOUR_TEAMS: tuple[Team, ...] = _dedup_cfb_teams(
    ACC_TEAMS,
    BIG_TEN_TEAMS,
    BIG_12_TEAMS,
    SEC_TEAMS,
)

GROUP_OF_FIVE_TEAMS: tuple[Team, ...] = _dedup_cfb_teams(
    AAC_TEAMS,
    CUSA_TEAMS,
    MAC_TEAMS,
    MOUNTAIN_WEST_TEAMS,
    SUN_BELT_TEAMS,
    PAC_12_TEAMS,
    FBS_INDEPENDENTS_TEAMS,
)

FBS_ALL_TEAMS: tuple[Team, ...] = _dedup_cfb_teams(
    ACC_TEAMS,
    BIG_TEN_TEAMS,
    BIG_12_TEAMS,
    SEC_TEAMS,
    AAC_TEAMS,
    MAC_TEAMS,
    MOUNTAIN_WEST_TEAMS,
    SUN_BELT_TEAMS,
    CUSA_TEAMS,
    PAC_12_TEAMS,
    FBS_INDEPENDENTS_TEAMS,
)

FCS_ALL_TEAMS: tuple[Team, ...] = _dedup_cfb_teams(
    BIG_SKY_TEAMS,
    CAA_TEAMS,
    IVY_LEAGUE_TEAMS,
    MEAC_TEAMS,
    MVFC_TEAMS,
    NEC_TEAMS,
    OVC_BIG_SOUTH_TEAMS,
    PATRIOT_TEAMS,
    PIONEER_TEAMS,
    SOCON_TEAMS,
    SOUTHLAND_TEAMS,
    SWAC_TEAMS,
    UAC_TEAMS,
    FCS_INDEPENDENTS_TEAMS,
)

# Combined set of all supported CFB conferences.  Teams appearing in more than
# one tuple (realignment artefacts) are kept under the first conference listed.
CFB_ALL_TEAMS: tuple[Team, ...] = _dedup_cfb_teams(
    # FBS – Power 4
    ACC_TEAMS,
    BIG_TEN_TEAMS,
    BIG_12_TEAMS,
    SEC_TEAMS,
    # FBS – Group of 5
    AAC_TEAMS,
    MAC_TEAMS,
    MOUNTAIN_WEST_TEAMS,
    SUN_BELT_TEAMS,
    CUSA_TEAMS,
    PAC_12_TEAMS,
    # FBS Independents
    FBS_INDEPENDENTS_TEAMS,
    # FCS
    BIG_SKY_TEAMS,
    CAA_TEAMS,
    IVY_LEAGUE_TEAMS,
    MEAC_TEAMS,
    MVFC_TEAMS,
    NEC_TEAMS,
    OVC_BIG_SOUTH_TEAMS,
    PATRIOT_TEAMS,
    PIONEER_TEAMS,
    SOCON_TEAMS,
    SOUTHLAND_TEAMS,
    SWAC_TEAMS,
    UAC_TEAMS,
    FCS_INDEPENDENTS_TEAMS,
)

# Approximate team counts for sets whose teams are fetched dynamically at runtime.
# Used by the GUI to show a ballpark number next to each set label.
APPROX_TEAM_COUNTS: dict[str, int] = {
    # Professional leagues (API-fetched; static approximations)
    "nfl": 32,
    "nba": 30,
    "nhl": 32,
    "wnba": 14,
    "mls": 30,
    "nwsl": 14,
    "ufl": 8,
    # English football (API-fetched; static approximations)
    "epl": 20,
    "efl_championship": 24,
    "efl_league_one": 24,
    "efl_league_two": 24,
    # Other professional football
    "cfl": 9,
    # International football / soccer (API-fetched; static approximations)
    "la_liga": 20,
    "bundesliga": 18,
    "serie_a": 20,
    "ligue_1": 18,
    # FBS – Power 4
    "acc": len(ACC_TEAMS),
    "big_ten": len(BIG_TEN_TEAMS),
    "big_12": len(BIG_12_TEAMS),
    "sec": len(SEC_TEAMS),
    # FBS – Group of 5
    "aac": len(AAC_TEAMS),
    "mac": len(MAC_TEAMS),
    "mountain_west": len(MOUNTAIN_WEST_TEAMS),
    "sun_belt": len(SUN_BELT_TEAMS),
    "cusa": len(CUSA_TEAMS),
    "pac_12": len(PAC_12_TEAMS),
    # FBS Independents
    "fbs_independents": len(FBS_INDEPENDENTS_TEAMS),
    # FCS
    "big_sky": len(BIG_SKY_TEAMS),
    "caa": len(CAA_TEAMS),
    "ivy_league": len(IVY_LEAGUE_TEAMS),
    "meac": len(MEAC_TEAMS),
    "mvfc": len(MVFC_TEAMS),
    "nec": len(NEC_TEAMS),
    "ovc_big_south": len(OVC_BIG_SOUTH_TEAMS),
    "patriot": len(PATRIOT_TEAMS),
    "pioneer": len(PIONEER_TEAMS),
    "socon": len(SOCON_TEAMS),
    "southland": len(SOUTHLAND_TEAMS),
    "swac": len(SWAC_TEAMS),
    "uac": len(UAC_TEAMS),
    "fcs_independents": len(FCS_INDEPENDENTS_TEAMS),
    # FBS sub-group combined
    "power_four": len(POWER_FOUR_TEAMS),
    "group_of_five": len(GROUP_OF_FIVE_TEAMS),
    # FBS / FCS combined
    "fbs_all": len(FBS_ALL_TEAMS),
    "fcs_all": len(FCS_ALL_TEAMS),
    # All CFB
    "cfb_all": len(CFB_ALL_TEAMS),
}

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

# Abbreviation lookup for API-fetched pro leagues.
# Keys are lowercased team display names (as returned by ESPN API after normalize_team_name).
ABBREVIATION_LOOKUP: dict[str, dict[str, str]] = {
    "nfl": {
        # AFC East
        "buffalo bills":           "BUF",
        "miami dolphins":          "MIA",
        "new england patriots":    "NE",
        "new york jets":           "NYJ",
        # AFC North
        "baltimore ravens":        "BAL",
        "cincinnati bengals":      "CIN",
        "cleveland browns":        "CLE",
        "pittsburgh steelers":     "PIT",
        # AFC South
        "houston texans":          "HOU",
        "indianapolis colts":      "IND",
        "jacksonville jaguars":    "JAX",
        "tennessee titans":        "TEN",
        # AFC West
        "denver broncos":          "DEN",
        "kansas city chiefs":      "KC",
        "las vegas raiders":       "LV",
        "los angeles chargers":    "LAC",
        # NFC East
        "dallas cowboys":          "DAL",
        "new york giants":         "NYG",
        "philadelphia eagles":     "PHI",
        "washington commanders":   "WSH",
        # NFC North
        "chicago bears":           "CHI",
        "detroit lions":           "DET",
        "green bay packers":       "GB",
        "minnesota vikings":       "MIN",
        # NFC South
        "atlanta falcons":         "ATL",
        "carolina panthers":       "CAR",
        "new orleans saints":      "NO",
        "tampa bay buccaneers":    "TB",
        # NFC West
        "arizona cardinals":       "ARI",
        "los angeles rams":        "LAR",
        "san francisco 49ers":     "SF",
        "seattle seahawks":        "SEA",
    },
    "nba": {
        # Eastern / Atlantic
        "boston celtics":          "BOS",
        "brooklyn nets":           "BKN",
        "new york knicks":         "NYK",
        "philadelphia 76ers":      "PHI",
        "toronto raptors":         "TOR",
        # Eastern / Central
        "chicago bulls":           "CHI",
        "cleveland cavaliers":     "CLE",
        "detroit pistons":         "DET",
        "indiana pacers":          "IND",
        "milwaukee bucks":         "MIL",
        # Eastern / Southeast
        "atlanta hawks":           "ATL",
        "charlotte hornets":       "CHA",
        "miami heat":              "MIA",
        "orlando magic":           "ORL",
        "washington wizards":      "WAS",
        # Western / Northwest
        "denver nuggets":          "DEN",
        "minnesota timberwolves":  "MIN",
        "oklahoma city thunder":   "OKC",
        "portland trail blazers":  "POR",
        "utah jazz":               "UTA",
        # Western / Pacific
        "golden state warriors":   "GSW",
        "los angeles clippers":    "LAC",
        "los angeles lakers":      "LAL",
        "phoenix suns":            "PHX",
        "sacramento kings":        "SAC",
        # Western / Southwest
        "dallas mavericks":        "DAL",
        "houston rockets":         "HOU",
        "memphis grizzlies":       "MEM",
        "new orleans pelicans":    "NOP",
        "san antonio spurs":       "SAS",
    },
    "nhl": {
        # Eastern / Atlantic
        "boston bruins":           "BOS",
        "buffalo sabres":          "BUF",
        "detroit red wings":       "DET",
        "florida panthers":        "FLA",
        "montr\u00e9al canadiens": "MTL",
        "montreal canadiens":      "MTL",
        "ottawa senators":         "OTT",
        "tampa bay lightning":     "TBL",
        "toronto maple leafs":     "TOR",
        # Eastern / Metropolitan
        "carolina hurricanes":     "CAR",
        "columbus blue jackets":   "CBJ",
        "new jersey devils":       "NJD",
        "new york islanders":      "NYI",
        "new york rangers":        "NYR",
        "philadelphia flyers":     "PHI",
        "pittsburgh penguins":     "PIT",
        "washington capitals":     "WSH",
        # Western / Central
        "chicago blackhawks":      "CHI",
        "colorado avalanche":      "COL",
        "dallas stars":            "DAL",
        "minnesota wild":          "MIN",
        "nashville predators":     "NSH",
        "st. louis blues":         "STL",
        "utah hockey club":        "UTA",
        "winnipeg jets":           "WPG",
        # Western / Pacific
        "anaheim ducks":           "ANA",
        "calgary flames":          "CGY",
        "edmonton oilers":         "EDM",
        "los angeles kings":       "LAK",
        "san jose sharks":         "SJS",
        "seattle kraken":          "SEA",
        "vancouver canucks":       "VAN",
        "vegas golden knights":    "VGK",
    },
    "wnba": {
        # Eastern Conference
        "atlanta dream":           "ATL",
        "chicago sky":             "CHI",
        "connecticut sun":         "CONN",
        "indiana fever":           "IND",
        "new york liberty":        "NY",
        "toronto tempo":           "TOR",
        "washington mystics":      "WSH",
        # Western Conference
        "dallas wings":            "DAL",
        "golden state valkyries":  "GSV",
        "las vegas aces":          "LV",
        "los angeles sparks":      "LA",
        "minnesota lynx":          "MIN",
        "phoenix mercury":         "PHX",
        "seattle storm":           "SEA",
    },
    "mls": {
        # Eastern Conference
        "atlanta united fc":       "ATL",
        "cf montr\u00e9al":        "MTL",
        "cf montreal":             "MTL",
        "charlotte fc":            "CLT",
        "chicago fire fc":         "CHI",
        "columbus crew":           "CLB",
        "d.c. united":             "DC",
        "fc cincinnati":           "CIN",
        "inter miami cf":          "MIA",
        "nashville sc":            "NSH",
        "new england revolution":  "NE",
        "new york city fc":        "NYCFC",
        "new york red bulls":      "RBNY",
        "orlando city sc":         "ORL",
        "philadelphia union":      "PHI",
        "toronto fc":              "TOR",
        # Western Conference
        "austin fc":               "ATX",
        "colorado rapids":         "COL",
        "fc dallas":               "DAL",
        "houston dynamo fc":       "HOU",
        "l.a. galaxy":             "LA",
        "la galaxy":               "LA",
        "lafc":                    "LAFC",
        "los angeles fc":          "LAFC",
        "minnesota united fc":     "MIN",
        "portland timbers":        "POR",
        "real salt lake":          "RSL",
        "san diego fc":            "SD",
        "san jose earthquakes":    "SJ",
        "seattle sounders fc":     "SEA",
        "sporting kansas city":    "SKC",
        "vancouver whitecaps fc":  "VAN",
    },
    "nwsl": {
        "angel city fc":           "ACFC",
        "boston legacy fc":        "BOS",
        "boston legacy":           "BOS",
        "carolina courage":        "NC",
        "chicago red stars":       "CHI",
        "gotham fc":               "NJ",
        "houston dash":            "HOU",
        "kansas city current":     "KC",
        "nj/ny gotham fc":         "NJ",
        "north carolina courage":  "NC",
        "ol reign":                "SEA",
        "orlando pride":           "ORL",
        "portland thorns fc":      "POR",
        "portland thorns":         "POR",
        "racing louisville fc":    "LOU",
        "racing louisville":       "LOU",
        "san diego wave fc":       "SD",
        "san diego wave":          "SD",
        "seattle reign fc":        "SEA",
        "utah royals fc":          "UTA",
        "utah royals":             "UTA",
        "washington spirit":       "WAS",
    },
    "ufl": {
        "arlington renegades":     "ARLN",
        "birmingham stallions":    "BHAM",
        "dc defenders":            "DC",
        "houston roughnecks":      "HOU",
        "memphis showboats":       "MEM",
        "michigan panthers":       "MICH",
        "san antonio brahmas":     "SA",
        "st. louis battlehawks":   "STL",
    },
    "cfl": {
        "bc lions":                "BC",
        "calgary stampeders":      "CGY",
        "edmonton elks":           "EDM",
        "hamilton tiger-cats":     "HAM",
        "montreal alouettes":      "MTL",
        "ottawa redblacks":        "OTT",
        "saskatchewan roughriders":"SSK",
        "toronto argonauts":       "TOR",
        "winnipeg blue bombers":   "WPG",
    },
}


FLASHCARD_SETS: dict[str, FlashcardSet] = {
    "mlb": FlashcardSet(
        code="mlb",
        display_name="Major League Baseball (MLB)",
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
        default_conference="ACC",
        default_conference_abbr="ACC",
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
        default_conference="Big Ten",
        default_conference_abbr="Big Ten",
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
        default_conference="Big 12",
        default_conference_abbr="Big 12",
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
        default_conference="SEC",
        default_conference_abbr="SEC",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/sec.png",
    ),
    "aac": FlashcardSet(
        code="aac",
        display_name="AAC",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="AAC",
        teams=AAC_TEAMS,
        default_conference="AAC",
        default_conference_abbr="AAC",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/aac.png",
    ),
    "mac": FlashcardSet(
        code="mac",
        display_name="MAC",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="MAC",
        teams=MAC_TEAMS,
        default_conference="MAC",
        default_conference_abbr="MAC",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/mac.png",
    ),
    "mountain_west": FlashcardSet(
        code="mountain_west",
        display_name="Mountain West",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="MOUNTAIN_WEST",
        teams=MOUNTAIN_WEST_TEAMS,
        default_conference="Mountain West",
        default_conference_abbr="MWC",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/mwc.png",
    ),
    "sun_belt": FlashcardSet(
        code="sun_belt",
        display_name="Sun Belt",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="SUN_BELT",
        teams=SUN_BELT_TEAMS,
        default_conference="Sun Belt",
        default_conference_abbr="Sun Belt",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/sunbelt.png",
    ),
    "cusa": FlashcardSet(
        code="cusa",
        display_name="Conference USA",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="CUSA",
        teams=CUSA_TEAMS,
        default_conference="Conference USA",
        default_conference_abbr="CUSA",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/cusa.png",
    ),
    "ivy_league": FlashcardSet(
        code="ivy_league",
        display_name="Ivy League",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="IVY_LEAGUE",
        teams=IVY_LEAGUE_TEAMS,
        default_conference="Ivy League",
        default_conference_abbr="Ivy",
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
        default_conference="Pac-12",
        default_conference_abbr="Pac-12",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/pac12.png",
    ),
    "fbs_independents": FlashcardSet(
        code="fbs_independents",
        display_name="FBS Independents",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="FBS_INDEPENDENTS",
        teams=FBS_INDEPENDENTS_TEAMS,
        default_conference="FBS Independents",
        default_conference_abbr="Ind",
    ),
    "big_sky": FlashcardSet(
        code="big_sky",
        display_name="Big Sky",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="BIG_SKY",
        teams=BIG_SKY_TEAMS,
        default_conference="Big Sky",
        default_conference_abbr="Big Sky",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/big_sky.png",
    ),
    "caa": FlashcardSet(
        code="caa",
        display_name="CAA Football",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="CAA",
        teams=CAA_TEAMS,
        default_conference="CAA Football",
        default_conference_abbr="CAA",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/caa.png",
    ),
    "meac": FlashcardSet(
        code="meac",
        display_name="MEAC",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="MEAC",
        teams=MEAC_TEAMS,
        default_conference="MEAC",
        default_conference_abbr="MEAC",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/meac.png",
    ),
    "mvfc": FlashcardSet(
        code="mvfc",
        display_name="MVFC",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="MVFC",
        teams=MVFC_TEAMS,
        default_conference="MVFC",
        default_conference_abbr="MVFC",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/mvfc.png",
    ),
    "nec": FlashcardSet(
        code="nec",
        display_name="NEC",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="NEC",
        teams=NEC_TEAMS,
        default_conference="NEC",
        default_conference_abbr="NEC",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/nec.png",
    ),
    "ovc_big_south": FlashcardSet(
        code="ovc_big_south",
        display_name="OVC-Big South",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="OVC_BIG_SOUTH",
        teams=OVC_BIG_SOUTH_TEAMS,
        default_conference="OVC-Big South",
        default_conference_abbr="OVC-BS",
    ),
    "patriot": FlashcardSet(
        code="patriot",
        display_name="Patriot League",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="PATRIOT",
        teams=PATRIOT_TEAMS,
        default_conference="Patriot League",
        default_conference_abbr="Patriot",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/patriot.png",
    ),
    "pioneer": FlashcardSet(
        code="pioneer",
        display_name="Pioneer Football League",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="PIONEER",
        teams=PIONEER_TEAMS,
        default_conference="Pioneer Football League",
        default_conference_abbr="PFL",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/pioneer.png",
    ),
    "socon": FlashcardSet(
        code="socon",
        display_name="SoCon",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="SOCON",
        teams=SOCON_TEAMS,
        default_conference="SoCon",
        default_conference_abbr="SoCon",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/socon.png",
    ),
    "southland": FlashcardSet(
        code="southland",
        display_name="Southland",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="SOUTHLAND",
        teams=SOUTHLAND_TEAMS,
        default_conference="Southland",
        default_conference_abbr="Southland",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/southland.png",
    ),
    "swac": FlashcardSet(
        code="swac",
        display_name="SWAC",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="SWAC",
        teams=SWAC_TEAMS,
        default_conference="SWAC",
        default_conference_abbr="SWAC",
        league_logo_url="https://a.espncdn.com/i/teamlogos/ncaa_conf/500/swac.png",
    ),
    "uac": FlashcardSet(
        code="uac",
        display_name="United Athletic Conference",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="UAC",
        teams=UAC_TEAMS,
        default_conference="United Athletic Conference",
        default_conference_abbr="UAC",
    ),
    "fcs_independents": FlashcardSet(
        code="fcs_independents",
        display_name="FCS Independents",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="FCS_INDEPENDENTS",
        teams=FCS_INDEPENDENTS_TEAMS,
        default_conference="FCS Independents",
        default_conference_abbr="Ind",
    ),
    "power_four": FlashcardSet(
        code="power_four",
        display_name="All Power Four",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="POWER_FOUR",
        teams=POWER_FOUR_TEAMS,
    ),
    "group_of_five": FlashcardSet(
        code="group_of_five",
        display_name="All G5 & Independents",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="GROUP_OF_FIVE",
        teams=GROUP_OF_FIVE_TEAMS,
    ),
    "fbs_all": FlashcardSet(
        code="fbs_all",
        display_name="All FBS Conferences",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="FBS_ALL",
        teams=FBS_ALL_TEAMS,
    ),
    "fcs_all": FlashcardSet(
        code="fcs_all",
        display_name="All FCS Conferences",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="FCS_ALL",
        teams=FCS_ALL_TEAMS,
    ),
    "cfb_all": FlashcardSet(
        code="cfb_all",
        display_name="All CFB Conferences",
        source_mode="espn_cfb_api",
        source_template=None,
        source_api_endpoint=CFB_TEAMS_ENDPOINT,
        output_folder="CFB_ALL",
        teams=CFB_ALL_TEAMS,
    ),
    "nfl": FlashcardSet(
        code="nfl",
        display_name="National Football League (NFL)",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams?limit=200",
        output_folder="NFL",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png",
    ),
    "nba": FlashcardSet(
        code="nba",
        display_name="National Basketball Association (NBA)",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams?limit=200",
        output_folder="NBA",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/nba.png",
    ),
    "nhl": FlashcardSet(
        code="nhl",
        display_name="National Hockey League (NHL)",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams?limit=200",
        output_folder="NHL",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/nhl.png",
    ),
    "wnba": FlashcardSet(
        code="wnba",
        display_name="Women's National Basketball Association (WNBA)",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/teams?limit=200",
        output_folder="WNBA",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/wnba.png",
    ),
    "mls": FlashcardSet(
        code="mls",
        display_name="Major League Soccer (MLS)",
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
        display_name="National Women's Soccer League (NWSL)",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/soccer/usa.nwsl/teams?limit=200",
        output_folder="NWSL",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/nwsl.png",
    ),
    "ufl": FlashcardSet(
        code="ufl",
        display_name="United Football League (UFL)",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/football/ufl/teams?limit=200",
        output_folder="UFL",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/ufl.png",
    ),
    "cfl": FlashcardSet(
        code="cfl",
        display_name="Canadian Football League (CFL)",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/football/cfl/teams?limit=200",
        output_folder="CFL",
        teams=(),
        league_logo_url="https://a.espncdn.com/i/teamlogos/leagues/500/cfl.png",
    ),
    "la_liga": FlashcardSet(
        code="la_liga",
        display_name="La Liga",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/teams?limit=200",
        output_folder="LA_LIGA",
        teams=(),
    ),
    "bundesliga": FlashcardSet(
        code="bundesliga",
        display_name="Bundesliga",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/teams?limit=200",
        output_folder="BUNDESLIGA",
        teams=(),
    ),
    "serie_a": FlashcardSet(
        code="serie_a",
        display_name="Serie A",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/teams?limit=200",
        output_folder="SERIE_A",
        teams=(),
    ),
    "ligue_1": FlashcardSet(
        code="ligue_1",
        display_name="Ligue 1",
        source_mode="espn_league_api_all",
        source_template=None,
        source_api_endpoint="https://site.api.espn.com/apis/site/v2/sports/soccer/fra.1/teams?limit=200",
        output_folder="LIGUE_1",
        teams=(),
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
    name_order: str = "city_first",
) -> str:
    """
    Format a team name according to config options.
    
    Args:
        team: The team object
        name_format: "full" (city+team), "city_only", or "team_only"
        name_order: "city_first" (default) or "team_first" — controls part order in full mode
    
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
        if name_order == "team_first":
            return f"{team_name} {location}".strip()
        return f"{location} {team_name}".strip()
    else:
        return team.name


def format_filename(
    team: Team,
    filename_format: str = "prefix",
    name_format: str = "full",
    name_order: str = "city_first",
) -> tuple[str, str, str]:
    """
    Generate logo, text, and combo filename stems for a team.

    Args:
        team: The team object
        filename_format: "prefix" or "suffix"
        name_format: "full", "city_only", or "team_only"
        name_order: "city_first" or "team_first" — controls part order in full mode

    Returns:
        Tuple of (logo_stem, text_stem, combo_stem) without extension
    """
    formatted_name = format_team_name(team, name_format, name_order)
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
    name_order: str = "city_first",
) -> list[str]:
    """Generate output filename stems for the selected card types.

    Args:
        card_types: Set of types to include — any of "logo", "text", "combo".
                    Defaults to {"logo", "text"}.
        name_order: "city_first" or "team_first" — controls part order in full mode.

    Returns:
        Filename stems in order: logo first, text second, combo third.
    """
    if card_types is None:
        card_types = {"logo", "text"}

    logo_name, text_name, combo_name = format_filename(
        team,
        filename_format=filename_format,
        name_format=name_format,
        name_order=name_order,
    )

    result: list[str] = []
    if "logo" in card_types:
        result.append(logo_name)
    if "text" in card_types:
        result.append(text_name)
    if "combo" in card_types:
        result.append(combo_name)
    return result
