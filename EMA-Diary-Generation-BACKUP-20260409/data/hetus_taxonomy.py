"""
Official HETUS Activity Coding List 2018 (ACL 2018).
Source: Eurostat, Annex IV of HETUS Guidelines.

Complete taxonomy with:
- Activity codes (main + secondary)
- Social context codes
- Location codes
- Transport mode codes

Used as the structured reference for diary generation, ensuring
our synthetic diaries use the official European time-use classification.
"""


# ──────────────────────────────────────────────────────────────────────
# ACTIVITY CODES (Main + Secondary)
# ──────────────────────────────────────────────────────────────────────

ACTIVITIES = {
    # 0 PERSONAL CARE
    "011": "Sleeping",
    "012": "Sick in bed",
    "021": "Eating",
    "031": "Washing and dressing",
    "032": "Personal care services",
    "039": "Other or unspecified personal care",

    # 1 EMPLOYMENT
    "111": "Working time in main and second job",
    "121": "Lunch break in main and second jobs",
    "129": "Other or unspecified activities related to employment",

    # 2 STUDY
    "211": "Classes and lectures",
    "212": "Homework",
    "213": "Internship",
    "214": "Breaks at school/university",
    "215": "Extracurricular classes",
    "219": "Other/unspecified activities related to study",
    "221": "Free time study",

    # 3 HOUSEHOLD AND FAMILY CARE
    "300": "Unspecified household and family care",
    "311": "Food preparation and baking",
    "312": "Dish washing",
    "313": "Storing, arranging, preserving food stocks",
    "321": "Cleaning dwelling",
    "322": "Cleaning garden",
    "323": "Heating dwelling and water",
    "324": "Arranging household goods and materials",
    "325": "Recycling and disposal of waste",
    "329": "Other or unspecified household upkeep",
    "331": "Laundry",
    "332": "Ironing",
    "339": "Other or unspecified textile care",
    "341": "Gardening",
    "342": "Tending domestic animals",
    "343": "Caring for pets",
    "344": "Walking the dog",
    "349": "Other or unspecified gardening and pet care",
    "351": "House construction and renovation",
    "352": "Repairs to dwelling",
    "353": "Making, repairing and maintaining equipment",
    "354": "Vehicle maintenance",
    "359": "Other or unspecified construction and repairs",
    "361": "Shopping (including online/e-shopping)",
    "362": "Commercial and administrative services",
    "369": "Other or unspecified shopping and services",
    "371": "Household management",
    "381": "Physical care and supervision of child",
    "382": "Teaching the child",
    "383": "Reading, playing and talking with child",
    "384": "Accompanying child",
    "389": "Other or unspecified childcare",
    "391": "Physical care of an adult household member",
    "392": "Other support to an adult household member",

    # 4 VOLUNTARY WORK AND MEETINGS
    "411": "Organisational work",
    "421": "Construction and repairs as help",
    "422": "Help in employment and farming",
    "423": "Care of own children living in another household",
    "424": "Childcare as help to another household",
    "425": "Help to an adult person of another household",
    "429": "Other/unspecified informal help to another household",
    "431": "Meetings",
    "432": "Religious activities",
    "433": "Visits to cemetery and grave care",
    "439": "Other or unspecified participatory activities",

    # 5 SOCIAL LIFE AND ENTERTAINMENT
    "511": "Socialising with family",
    "512": "Visiting and receiving visitors",
    "513": "Celebrations",
    "514": "Audio and video conversation",
    "515": "Communication by text messaging",
    "516": "Time spent on social media",
    "519": "Other or unspecified social life",
    "521": "Cinema",
    "522": "Theatre and concerts",
    "523": "Art exhibitions and museums",
    "524": "Library",
    "525": "Attending live sports events",
    "526": "Zoos, botanical gardens, natural reserves",
    "529": "Other or unspecified entertainment and culture",
    "531": "Resting — Time out",

    # 6 SPORTS AND OUTDOOR ACTIVITIES
    "611": "Walking and hiking",
    "612": "Jogging and running",
    "613": "Cycling, skiing and skating",
    "614": "Ball games",
    "615": "Gymnastics and fitness",
    "616": "Water sports",
    "619": "Other or unspecified sports or outdoor activities",
    "621": "Productive exercise (hunting, fishing, picking berries)",
    "631": "Sports related activities",

    # 7 HOBBIES
    "711": "Arts (visual, performing, literary)",
    "712": "Collecting",
    "713": "Making handicraft products",
    "719": "Other or unspecified hobbies",
    "721": "Computing",
    "722": "Information search using internet",
    "729": "Other or unspecified computing",
    "731": "Solo games and play, gambling",
    "732": "Parlour games and play",
    "733": "Computer games",
    "734": "Console games",
    "735": "Mobile games",
    "739": "Other or unspecified games",

    # 8 MASS MEDIA
    "811": "Reading periodicals",
    "812": "Reading books",
    "819": "Other or unspecified reading",
    "821": "Watching TV, video or DVD",
    "831": "Listening to radio or recordings",

    # 9 TRAVEL
    "910": "Travel to/from work",
    "920": "Travel related to study",
    "936": "Travel related to shopping and services",
    "938": "Travel related to childcare",
    "939": "Travel related to other household care",
    "940": "Travel related to voluntary work and meetings",
    "950": "Travel related to social life",
    "960": "Travel related to other leisure",
    "980": "Travel related to changing locality",
    "900": "Other or unspecified travel purpose",

    # AUXILIARY
    "995": "Filling in the time use diary",
    "998": "Unspecified leisure time",
    "999": "Other unspecified time use",
}


# ──────────────────────────────────────────────────────────────────────
# SOCIAL CONTEXT CODES (With whom time is spent)
# ──────────────────────────────────────────────────────────────────────

SOCIAL_CONTEXT = {
    "1": "Alone (also with unknown persons, alone in crowd)",
    "2": "Partner",
    "3": "Parent(s): mother, father",
    "4": "Children up to 17 years",
    "5": "Other household member(s)",
    "6": "Other person(s) known to the respondent",
}


# ──────────────────────────────────────────────────────────────────────
# LOCATION CODES
# ──────────────────────────────────────────────────────────────────────

LOCATIONS = {
    "00": "Unspecified location/transport mode",
    "10": "Unspecified location (not travelling)",
    "11": "Home",
    "12": "Weekend home or holiday apartment",
    "13": "Workplace or school",
    "14": "Other people's home",
    "15": "Restaurant, cafe or pub",
    "16": "Shopping centres, malls, markets, other shops",
    "17": "Hotel, guesthouse, camping site",
    "19": "Other specified location (not travelling)",
}


# ──────────────────────────────────────────────────────────────────────
# TRANSPORT MODE CODES
# ──────────────────────────────────────────────────────────────────────

TRANSPORT_MODES = {
    "20": "Unspecified transport mode",
    "21": "Travelling on foot",
    "22": "Travelling by bicycle",
    "23": "Travelling by moped, motorcycle or motorboat",
    "24": "Travelling by passenger car",
    "29": "Other or unspecified private transport mode",
    "31": "Travelling by public transport",
}


# ──────────────────────────────────────────────────────────────────────
# MAPPING: HETUS CODE -> Our Diary Fields
# ──────────────────────────────────────────────────────────────────────

HETUS_TO_OUR_FORMAT = {
    # Sleeping
    "011": {"primary_activity": "lying", "domain": "self_care", "purpose": "sleeping"},
    "012": {"primary_activity": "lying", "domain": "self_care", "purpose": "sick in bed"},

    # Eating
    "021": {"primary_activity": "sitting", "domain": "self_care", "purpose": "eating"},

    # Personal care
    "031": {"primary_activity": "standing", "domain": "self_care", "purpose": "washing and dressing"},
    "032": {"primary_activity": "sitting", "domain": "self_care", "purpose": "personal care services"},

    # Employment
    "111": {"primary_activity": "sitting", "domain": "work", "purpose": "working time"},
    "121": {"primary_activity": "sitting", "domain": "work", "purpose": "lunch break"},

    # Study
    "211": {"primary_activity": "sitting", "domain": "work", "purpose": "classes and lectures"},
    "212": {"primary_activity": "sitting", "domain": "work", "purpose": "homework"},

    # Household
    "311": {"primary_activity": "standing", "domain": "household", "purpose": "food preparation"},
    "312": {"primary_activity": "standing", "domain": "household", "purpose": "dish washing"},
    "321": {"primary_activity": "standing", "domain": "household", "purpose": "cleaning dwelling"},
    "322": {"primary_activity": "standing", "domain": "household", "purpose": "cleaning garden"},
    "341": {"primary_activity": "standing", "domain": "household", "purpose": "gardening"},
    "344": {"primary_activity": "walking", "domain": "household", "purpose": "walking the dog"},
    "361": {"primary_activity": "walking", "domain": "household", "purpose": "shopping"},

    # Social
    "511": {"primary_activity": "sitting", "domain": "social", "purpose": "socialising with family"},
    "512": {"primary_activity": "sitting", "domain": "social", "purpose": "visiting/receiving visitors"},

    # Resting
    "531": {"primary_activity": "lying", "domain": "leisure", "purpose": "resting"},

    # SPORTS (the key ones for active transport)
    "611": {"primary_activity": "walking", "domain": "exercise", "purpose": "walking and hiking"},
    "612": {"primary_activity": "running", "domain": "exercise", "purpose": "jogging and running"},
    "613": {"primary_activity": "cycling", "domain": "exercise", "purpose": "cycling for exercise"},
    "614": {"primary_activity": "standing", "domain": "exercise", "purpose": "ball games"},
    "615": {"primary_activity": "standing", "domain": "exercise", "purpose": "gymnastics and fitness"},

    # Hobbies (sedentary leisure)
    "721": {"primary_activity": "sitting", "domain": "leisure", "purpose": "computing"},
    "722": {"primary_activity": "sitting", "domain": "leisure", "purpose": "information search"},
    "733": {"primary_activity": "sitting", "domain": "leisure", "purpose": "computer games"},

    # Mass media (sedentary leisure)
    "811": {"primary_activity": "sitting", "domain": "leisure", "purpose": "reading periodicals"},
    "812": {"primary_activity": "sitting", "domain": "leisure", "purpose": "reading books"},
    "821": {"primary_activity": "sitting", "domain": "leisure", "purpose": "watching TV"},
    "831": {"primary_activity": "sitting", "domain": "leisure", "purpose": "listening to radio"},

    # TRAVEL (the critical ones for active transport research)
    "910": {"primary_activity": "cycling", "domain": "transport", "purpose": "travel to/from work"},
    "920": {"primary_activity": "cycling", "domain": "transport", "purpose": "travel related to study"},
    "936": {"primary_activity": "walking", "domain": "transport", "purpose": "travel related to shopping"},
    "950": {"primary_activity": "cycling", "domain": "transport", "purpose": "travel related to social life"},
    "960": {"primary_activity": "cycling", "domain": "transport", "purpose": "travel related to leisure"},
    "900": {"primary_activity": "cycling", "domain": "transport", "purpose": "unspecified travel"},
}


# ──────────────────────────────────────────────────────────────────────
# PROMPT SECTION
# ──────────────────────────────────────────────────────────────────────

def get_hetus_prompt_section() -> str:
    """Get condensed HETUS reference for diary generation prompts."""
    return (
        "HETUS ACL 2018 CODES (use ONLY these exact codes):\n"
        "011 Sleeping | 021 Eating | 031 Washing/dressing | "
        "111 Working time | 121 Lunch break | "
        "311 Food prep | 312 Dish washing | 321 Cleaning | 344 Walking dog | 361 Shopping | "
        "511 Socialising family | 512 Visiting | 531 Resting | "
        "611 Walking/hiking(exercise) | 612 Jogging/running | 613 Cycling(exercise) | 615 Gym/fitness | "
        "721 Computing(leisure) | 733 Computer games | 812 Reading | 821 Watching TV | "
        "910 Travel to/from work | 936 Travel shopping | 950 Travel social | 960 Travel leisure\n"
        "Transport modes: 21 On foot | 22 Bicycle | 24 Car | 31 Public transport\n"
        "Social: 1 Alone | 2 Partner | 3 Parents | 4 Children | 5 Other household | 6 Other known\n"
        "Location: 11 Home | 13 Work/school | 14 Other home | 15 Restaurant | 16 Shops | 19 Other\n"
        "CRITICAL: Exercise walking=cycling is 611/613. Transport walking=cycling is 910+mode21/22.\n"
    )
