"""
A pool of generic "background" follower handles - not full characters, just
the crowd. Used for the "liked by" preview line and for a handful of short
generic one-line reactions on high-clout posts, layered on top of each
fandom's three named cast members.
"""

CROWD_HANDLES = [
    # desi-coded
    "aaravmehta", "riyan_singh", "zaynkapoor", "arjunrao", "neilvarma",
    "kabirshah", "ishaanpatel", "rohanmalik", "devanshraj", "vihaanmehra",
    "adityanair", "aryanjoshi", "rehan_khan", "krishverma", "vivaanr",
    "dhruvsethi", "ayaanm", "rudra_s", "nikhilrao", "samarthjain",
    "mira_shah", "ananyaverma", "kiaramehta", "ishitarao", "myrasingh",
    "tara_kapoor", "navyashah", "aishamehra", "riya_n", "siarajain",
    "aravwrites", "kabironline", "neilafterdark", "rohan.jpg", "zaynoffline",
    "ayaanverse", "vihaan.exe", "ishaanfiles", "devcalled", "rudrawas_here",
    "miraonline", "taraonx", "kiarawrites", "ananyacore", "siathinks",
    "navyaoffline", "myrafiles", "aishadaily", "riyacoded", "meeraonair",
    # western-coded
    "alexmorgan", "ethanblake", "liamcarter", "noahhayes", "owenparker",
    "lucasreed", "masoncole", "evanbrooks", "juliantate", "ryanbennett",
    "nathanross", "calebstone", "adrianwest", "loganprice", "dylanford",
    "theomills", "isaaclane", "jordanfrost", "milesgrant", "aidanwright",
    "oliviahart", "emmarose", "chloebennett", "sophiaclark", "mayawells",
    "elliejames", "lilybrooks", "zoemorgan", "avahudson", "isabellareed",
    "noraellis", "ameliagrace", "lucyparker", "harperlane", "ellawest",
    "stellafox", "ariaholland", "clairemills", "ivycarter", "rubyhayes",
    "alexdoesntsleep", "ethanontheweb", "liamafterhours", "noaharchive", "owenwas_here",
    "lucasoffline", "masonposting", "evan.txt", "julianonline", "ryanfromsomewhere",
    # fantasy-coded
    "velorin", "kaelvoss", "nyxhaven", "eliorayne", "cassianvale",
    "zevren", "orionvex", "lyraquinn", "kaiverren", "novarae",
    "aeronvale", "serenvoss", "evrennoir", "lucaivory", "mavenross",
    "sorenvale", "azielnorth", "rivenhart", "elarafox", "virelune",
    "caelrowe", "noxmarlow", "aurelvane", "zoraellis", "renvoss",
    "kaelthorne", "lyranox", "evrenvale", "solenray", "vanyaquill",
    "arisnoir", "zephyrvale", "nyxrowe", "elionyx", "sorenvex",
    "miraeon", "cassvale", "orionmarlow", "lyranoir", "rivenrowe",
    "kaelarchive", "noxonline", "velorinthinks", "elaraafterdark", "zevposting",
    "sorenoffline", "orionfiles", "nyxwasthere", "rivenonline", "kaivex",
    # extremely online
    "midnightaarav", "justkabir", "neilprobably", "rohanactually", "zaynmaybe",
    "ayaanlater", "vihaanagain", "ishaanhere", "arjunposting", "dhruvonline",
    "miraactually", "taraagain", "navyaonline", "kiaraactually", "siaposting",
    "meeraoffline", "alexprobably", "ethanactually", "liamagain", "noahposting",
    "owenonline", "lucasactually", "masonagain", "evanprobably", "juliandaily",
    "ryanposting", "nathanonline", "calebactually", "adrianagain", "logannotfound",
    "dylanposting", "theoonline", "isaacprobably", "jordanactually", "milesagain",
    "aidanonline", "oliviaactually", "emmaposting", "chloehere", "sophiadaily",
    "mayaprobably", "ellieonline", "lilyactually", "zoeposting", "avanotfound",
    "noraagain", "ameliadaily", "lucyprobably", "harperonline", "stellaposting",
]

CROWD_AVATARS = ["👤", "🫥", "🙂", "😶", "🫧", "🐣"]


def crowd_avatar(handle):
    return CROWD_AVATARS[sum(ord(c) for c in handle) % len(CROWD_AVATARS)]
