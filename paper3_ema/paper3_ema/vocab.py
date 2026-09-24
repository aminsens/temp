"""Controlled vocabularies and ordinal scale definitions.

Vocabulary provenance
---------------------
The activity / domain / place / social / indoor-outdoor / device-wear /
trigger vocabularies are adapted from the historical EMA data models
(``EMA-Diary-Generation/data/models.py``, salvaged per
``docs/PHASE0_ARCHAEOLOGY.md`` §2) and cross-checked against the variable
hierarchy in ``EMA_Definitive_Synthesis.md`` §6.1 and §9.5.

The subjective items (valence, energy, stress) are *synthetic simulation
outputs*, not observed human measurements.  Their 5-point ordinal labels are
documented here and are the single source of truth for every serialisation.

Nothing in this module encodes a claim about human psychology; see
``docs/SCIENTIFIC_ASSUMPTIONS.md``.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

SCHEMA_VERSION = "1.0.0"


class Activity(str, Enum):
    """Physical behaviour at prompt time (inherited contextual fact)."""

    SLEEPING = "sleeping"
    LYING_AWAKE = "lying_awake"
    SITTING = "sitting"
    STANDING = "standing"
    WALKING = "walking"
    RUNNING = "running"
    CYCLING = "cycling"
    DRIVING = "driving"
    PUBLIC_TRANSPORT = "public_transport"
    OTHER_VIGOROUS = "other_vigorous"
    OTHER_LIGHT = "other_light"
    UNKNOWN = "unknown"


class Domain(str, Enum):
    """Behavioural domain - the highest-value contextual variable
    (``EMA_Definitive_Synthesis.md`` §10.2 UNDERRATED #2)."""

    WORK = "work"
    STUDY = "study"
    TRANSPORT = "transport"
    HOUSEHOLD = "household"
    CHILDCARE = "childcare"
    EXERCISE = "exercise"
    LEISURE = "leisure"
    SOCIAL = "social"
    SELF_CARE = "self_care"
    SHOPPING = "shopping"
    OTHER = "other"


class PlaceType(str, Enum):
    """Coarse place type.  Proper names never enter the EMA context packet."""

    HOME = "home"
    WORKPLACE = "workplace"
    SCHOOL = "school"
    SHOP = "shop"
    FOOD_VENUE = "food_venue"
    GYM = "gym"
    PARK = "park"
    OUTDOOR_GENERIC = "outdoor_generic"
    STREET = "street"
    VEHICLE = "vehicle"
    TRANSIT_STOP = "transit_stop"
    HEALTHCARE = "healthcare"
    OTHER_BUILDING = "other_building"
    OTHER = "other"
    UNKNOWN = "unknown"


class SocialContext(str, Enum):
    ALONE = "alone"
    WITH_PARTNER = "with_partner"
    WITH_FAMILY = "with_family"
    WITH_CHILDREN = "with_children"
    WITH_FRIENDS = "with_friends"
    WITH_COLLEAGUES = "with_colleagues"
    WITH_KNOWN_OTHERS = "with_known_others"
    WITH_STRANGERS = "with_strangers"
    UNKNOWN = "unknown"


class IndoorOutdoor(str, Enum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class DeviceWear(str, Enum):
    """Optional.  Never fabricated: if the host day supplies no wear
    information the value is ``None`` (not ``WORN``)."""

    WORN = "worn"
    NOT_WORN = "not_worn"
    PARTIALLY_WORN = "partially_worn"


class TriggerType(str, Enum):
    """Paper 3 prompt triggers.

    ``SEMI_RANDOM`` is the background/stratified sample.  The remaining values
    are event-enriched, listed here in Paper 3 priority order (see
    ``EVENT_PRIORITY``).
    """

    SEMI_RANDOM = "semi_random"
    POST_TRIP = "post_trip"
    POST_ACTIVE_EPISODE = "post_active_episode"
    CONTEXT_TRANSITION = "context_transition"
    DISCRETIONARY_FALLBACK = "discretionary_fallback"


EVENT_PRIORITY: tuple[TriggerType, ...] = (
    TriggerType.POST_TRIP,
    TriggerType.POST_ACTIVE_EPISODE,
    TriggerType.CONTEXT_TRANSITION,
    TriggerType.DISCRETIONARY_FALLBACK,
)
"""Event-enriched triggers, highest priority first (Paper 3 protocol)."""

EVENT_TRIGGERS: frozenset[TriggerType] = frozenset(EVENT_PRIORITY)
BACKGROUND_TRIGGERS: frozenset[TriggerType] = frozenset({TriggerType.SEMI_RANDOM})


class ResponseStatus(str, Enum):
    """Outcome of one EMA opportunity.

    ``ANSWERED``          response recorded within the expiry window
    ``EXPIRED``           a response arrived after the expiry window (recorded,
                          flagged, excluded from alignment by default)
    ``MISSED``            no response at all
    """

    ANSWERED = "answered"
    EXPIRED = "expired"
    MISSED = "missed"


class AuditStatus(str, Enum):
    VALID = "VALID"
    NEEDS_REPAIR = "NEEDS_REPAIR"


class ProvenanceClass(str, Enum):
    """Origin class of a field value.  Every field of every emitted record is
    mapped to exactly one of these (see :mod:`paper3_ema.provenance`)."""

    INHERITED_CONTEXT = "inherited_context"
    DERIVED_CONTEXT = "derived_context"
    SYNTHETIC_PROTOCOL = "synthetic_protocol"
    SYNTHETIC_SUBJECTIVE = "synthetic_subjective"
    LLM_RENDERED = "llm_rendered"


# --------------------------------------------------------------------------
# ordinal subjective scales (synthetic)
# --------------------------------------------------------------------------

SUBJECTIVE_ITEMS: tuple[str, ...] = ("valence", "energy", "stress")
SCALE_MIN = 1
SCALE_MAX = 5

SCALE_LABELS: dict[str, dict[int, str]] = {
    "valence": {
        1: "very negative",
        2: "negative",
        3: "neutral",
        4: "positive",
        5: "very positive",
    },
    "energy": {
        1: "very low",
        2: "low",
        3: "moderate",
        4: "high",
        5: "very high",
    },
    "stress": {
        1: "none/very low",
        2: "low",
        3: "moderate",
        4: "high",
        5: "very high",
    },
}


def scale_label(item: str, value: int) -> str:
    return SCALE_LABELS[item][int(value)]


def describe_scales() -> dict[str, dict[str, str]]:
    """Human-readable scale documentation (emitted in every bundle)."""
    return {
        item: {str(k): v for k, v in labels.items()} for item, labels in SCALE_LABELS.items()
    }


def clamp_scale(value: float) -> int:
    """Round a latent value onto the 1-5 ordinal scale."""
    return int(max(SCALE_MIN, min(SCALE_MAX, round(value))))


# --------------------------------------------------------------------------
# demographic safeguard
# --------------------------------------------------------------------------

ALLOWED_PERSONA_FACTS: frozenset[str] = frozenset(
    {
        # only stable attributes with a direct contextual role are permitted
        "childcare_responsibility",   # usable when the current episode is childcare
        "work_schedule_pattern",      # usable when evaluating schedule pressure
        "usual_commute_mode",         # usable for transport contexts
        "usual_sleep_schedule",       # usable for minutes-since-waking only
    }
)

FORBIDDEN_PERSONA_FACTS: frozenset[str] = frozenset(
    {
        "age",
        "sex",
        "gender",
        "ethnicity",
        "race",
        "occupation",
        "income",
        "education",
        "health_notes",
        "health",
        "diagnosis",
        "fitness",
        "fitness_level",
        "personality",
        "personality_traits",
        "hobbies",
        "name",
        "weight",
        "bmi",
    }
)


def check_persona_keys(keys: Iterable[str]) -> tuple[list[str], list[str]]:
    """Split persona keys into ``(allowed, rejected)``.

    ``rejected`` contains both explicitly forbidden keys and unknown keys: the
    allowlist is closed, so anything not explicitly permitted is refused.
    """
    allowed: list[str] = []
    rejected: list[str] = []
    for key in keys:
        normalised = str(key).strip().lower()
        if normalised in ALLOWED_PERSONA_FACTS:
            allowed.append(normalised)
        else:
            rejected.append(str(key))
    return allowed, rejected


# --------------------------------------------------------------------------
# vocabulary normalisation (tolerant input, strict output)
# --------------------------------------------------------------------------

_ACTIVITY_ALIASES: dict[str, Activity] = {
    "sleep": Activity.SLEEPING,
    "asleep": Activity.SLEEPING,
    "nap": Activity.SLEEPING,
    "lying": Activity.LYING_AWAKE,
    "lying_down": Activity.LYING_AWAKE,
    "resting_lying": Activity.LYING_AWAKE,
    "sit": Activity.SITTING,
    "seated": Activity.SITTING,
    "sedentary": Activity.SITTING,
    "stand": Activity.STANDING,
    "walk": Activity.WALKING,
    "hiking": Activity.WALKING,
    "run": Activity.RUNNING,
    "jogging": Activity.RUNNING,
    "bike": Activity.CYCLING,
    "bicycle": Activity.CYCLING,
    "car": Activity.DRIVING,
    "car_driver": Activity.DRIVING,
    "motorcycle": Activity.DRIVING,
    "bus": Activity.PUBLIC_TRANSPORT,
    "train": Activity.PUBLIC_TRANSPORT,
    "tram": Activity.PUBLIC_TRANSPORT,
    "metro": Activity.PUBLIC_TRANSPORT,
    "subway": Activity.PUBLIC_TRANSPORT,
    "passenger": Activity.PUBLIC_TRANSPORT,
    "public_transit": Activity.PUBLIC_TRANSPORT,
    "exercise": Activity.OTHER_VIGOROUS,
    "gym": Activity.OTHER_VIGOROUS,
    "strength_training": Activity.OTHER_VIGOROUS,
    "swimming": Activity.OTHER_VIGOROUS,
    "sports": Activity.OTHER_VIGOROUS,
    "transition": Activity.OTHER_LIGHT,
    "other": Activity.UNKNOWN,
}

VIGOROUS_ACTIVITIES: frozenset[Activity] = frozenset(
    {Activity.RUNNING, Activity.CYCLING, Activity.OTHER_VIGOROUS}
)
"""Activities treated as 'actively exercising' for prompt exclusion."""

TRANSPORT_ACTIVITIES: frozenset[Activity] = frozenset(
    {Activity.DRIVING, Activity.PUBLIC_TRANSPORT, Activity.CYCLING}
)


def _normalise(value: object, enum: type[Enum], aliases: Optional[dict[str, Enum]] = None) -> Optional[Enum]:
    if value is None:
        return None
    if isinstance(value, enum):  # type: ignore[arg-type]
        return value  # type: ignore[return-value]
    text = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    if not text or text in {"none", "null", "n/a", "na", ""}:
        return None
    try:
        return enum(text)  # type: ignore[return-value]
    except ValueError:
        pass
    if aliases and text in aliases:
        return aliases[text]
    return None


def normalise_activity(value: object) -> Optional[Activity]:
    return _normalise(value, Activity, _ACTIVITY_ALIASES)  # type: ignore[arg-type,return-value]


def normalise_domain(value: object) -> Optional[Domain]:
    aliases = {
        "employment": Domain.WORK,
        "job": Domain.WORK,
        "occupation": Domain.WORK,
        "school": Domain.STUDY,
        "education": Domain.STUDY,
        "study": Domain.STUDY,
        "travel": Domain.TRANSPORT,
        "commute": Domain.TRANSPORT,
        "transport": Domain.TRANSPORT,
        "chores": Domain.HOUSEHOLD,
        "housework": Domain.HOUSEHOLD,
        "home": Domain.HOUSEHOLD,
        "family_care": Domain.CHILDCARE,
        "childcare": Domain.CHILDCARE,
        "sport": Domain.EXERCISE,
        "training": Domain.EXERCISE,
        "free_time": Domain.LEISURE,
        "hobby": Domain.LEISURE,
        "hobbies": Domain.LEISURE,
        "socialising": Domain.SOCIAL,
        "social": Domain.SOCIAL,
        "personal_care": Domain.SELF_CARE,
        "selfcare": Domain.SELF_CARE,
        "sleep": Domain.SELF_CARE,
        "shopping": Domain.SHOPPING,
        "errands": Domain.SHOPPING,
    }
    return _normalise(value, Domain, aliases)  # type: ignore[arg-type,return-value]


def normalise_place_type(value: object) -> Optional[PlaceType]:
    aliases = {
        "house": PlaceType.HOME,
        "apartment": PlaceType.HOME,
        "flat": PlaceType.HOME,
        "residence": PlaceType.HOME,
        "office": PlaceType.WORKPLACE,
        "work": PlaceType.WORKPLACE,
        "work_office": PlaceType.WORKPLACE,
        "workplace": PlaceType.WORKPLACE,
        "work_outdoor": PlaceType.OUTDOOR_GENERIC,
        "university": PlaceType.SCHOOL,
        "college": PlaceType.SCHOOL,
        "store": PlaceType.SHOP,
        "supermarket": PlaceType.SHOP,
        "shopping": PlaceType.SHOP,
        "cafe": PlaceType.FOOD_VENUE,
        "restaurant": PlaceType.FOOD_VENUE,
        "pub": PlaceType.FOOD_VENUE,
        "cafeteria": PlaceType.FOOD_VENUE,
        "fitness": PlaceType.GYM,
        "fitness_centre": PlaceType.GYM,
        "sports_centre": PlaceType.GYM,
        "garden": PlaceType.OUTDOOR_GENERIC,
        "nature": PlaceType.OUTDOOR_GENERIC,
        "outdoor": PlaceType.OUTDOOR_GENERIC,
        "outdoor_general": PlaceType.OUTDOOR_GENERIC,
        "road": PlaceType.STREET,
        "bus_stop": PlaceType.TRANSIT_STOP,
        "station": PlaceType.TRANSIT_STOP,
        "transit_stop": PlaceType.TRANSIT_STOP,
        "hospital": PlaceType.HEALTHCARE,
        "clinic": PlaceType.HEALTHCARE,
        "medical": PlaceType.HEALTHCARE,
        "vehicle": PlaceType.VEHICLE,
        "transit_vehicle": PlaceType.VEHICLE,
        "car": PlaceType.VEHICLE,
        "indoor_other": PlaceType.OTHER_BUILDING,
        "friend_home": PlaceType.OTHER_BUILDING,
        "other_people_s_home": PlaceType.OTHER_BUILDING,
    }
    return _normalise(value, PlaceType, aliases)  # type: ignore[arg-type,return-value]


def normalise_social(value: object) -> Optional[SocialContext]:
    aliases = {
        "solo": SocialContext.ALONE,
        "partner": SocialContext.WITH_PARTNER,
        "spouse": SocialContext.WITH_PARTNER,
        "family": SocialContext.WITH_FAMILY,
        "children": SocialContext.WITH_CHILDREN,
        "kids": SocialContext.WITH_CHILDREN,
        "child": SocialContext.WITH_CHILDREN,
        "friends": SocialContext.WITH_FRIENDS,
        "colleagues": SocialContext.WITH_COLLEAGUES,
        "coworkers": SocialContext.WITH_COLLEAGUES,
        "strangers": SocialContext.WITH_STRANGERS,
        "crowd": SocialContext.WITH_STRANGERS,
        "others": SocialContext.WITH_KNOWN_OTHERS,
        "known_others": SocialContext.WITH_KNOWN_OTHERS,
    }
    return _normalise(value, SocialContext, aliases)  # type: ignore[arg-type,return-value]


def normalise_indoor_outdoor(value: object) -> Optional[IndoorOutdoor]:
    aliases = {"inside": IndoorOutdoor.INDOOR, "outside": IndoorOutdoor.OUTDOOR}
    return _normalise(value, IndoorOutdoor, aliases)  # type: ignore[arg-type,return-value]


def normalise_device_wear(value: object) -> Optional[DeviceWear]:
    aliases = {
        "wearing": DeviceWear.WORN,
        "on_body": DeviceWear.WORN,
        "on": DeviceWear.WORN,
        "removed": DeviceWear.NOT_WORN,
        "off_body": DeviceWear.NOT_WORN,
        "off": DeviceWear.NOT_WORN,
        "partial": DeviceWear.PARTIALLY_WORN,
    }
    return _normalise(value, DeviceWear, aliases)  # type: ignore[arg-type,return-value]


def normalise_trigger(value: object) -> Optional[TriggerType]:
    aliases = {
        "random": TriggerType.SEMI_RANDOM,
        "semi_random": TriggerType.SEMI_RANDOM,
        "signal_contingent": TriggerType.SEMI_RANDOM,
        "background": TriggerType.SEMI_RANDOM,
        "trip": TriggerType.POST_TRIP,
        "post_journey": TriggerType.POST_TRIP,
        "post_active": TriggerType.POST_ACTIVE_EPISODE,
        "post_exercise": TriggerType.POST_ACTIVE_EPISODE,
        "transition": TriggerType.CONTEXT_TRANSITION,
        "context_transition": TriggerType.CONTEXT_TRANSITION,
        "meaningful_context_transition": TriggerType.CONTEXT_TRANSITION,
        "discretionary": TriggerType.DISCRETIONARY_FALLBACK,
        "fallback": TriggerType.DISCRETIONARY_FALLBACK,
        "event_triggered": TriggerType.DISCRETIONARY_FALLBACK,
    }
    return _normalise(value, TriggerType, aliases)  # type: ignore[arg-type,return-value]


# --------------------------------------------------------------------------
# closed-world lexicons for LLM note validation
# --------------------------------------------------------------------------

WEATHER_TERMS: frozenset[str] = frozenset(
    {
        "rain", "raining", "rainy", "rained", "drizzle", "downpour", "storm", "stormy",
        "thunder", "lightning", "snow", "snowing", "snowy", "sleet", "hail", "ice", "icy",
        "wind", "windy", "gale", "breeze", "breezy", "sun", "sunny", "sunshine", "cloud",
        "cloudy", "overcast", "fog", "foggy", "mist", "misty", "humid", "humidity", "muggy",
        "heatwave", "frost", "frosty", "freezing", "weather", "forecast", "umbrella",
        "showers", "clear skies", "blue skies",
    }
)

MEDICAL_TERMS: frozenset[str] = frozenset(
    {
        "pain", "painful", "ache", "aching", "sore", "soreness", "injury", "injured",
        "cramp", "cramps", "strain", "sprain", "fracture", "broken", "bruise", "blister",
        "blisters", "fever", "temperature", "ill", "illness", "sick", "sickness", "nausea",
        "nauseous", "dizzy", "dizziness", "headache", "migraine", "flu", "cold", "cough",
        "coughing", "sneeze", "infection", "virus", "viral", "asthma", "breathless",
        "palpitations", "chest tightness", "doctor", "clinic", "appointment", "diagnosis",
        "diagnosed", "symptom", "symptoms", "medication", "medicine", "tablet", "tablets",
        "pill", "pills", "dose", "therapy", "physio", "physiotherapist", "scan", "blood test",
        "treatment", "condition", "disorder", "disease", "chronic", "recovery from illness",
        "hangover", "hungover", "anxiety", "anxious", "panic", "depressed", "depression",
        "burnout", "burnt out", "insomnia",
    }
)

TRANSPORT_DISRUPTION_TERMS: frozenset[str] = frozenset(
    {
        "delay", "delayed", "delays", "late", "lateness", "running late", "missed",
        "cancellation", "cancelled", "canceled", "diverted", "diversion", "replacement bus",
        "strike", "disruption", "disrupted", "breakdown", "broke down", "congestion",
        "traffic jam", "gridlock", "queue", "queued", "overcrowded", "packed", "crush",
        "cramped", "closed", "closure", "roadworks", "accident", "crash", "collision",
        "signal failure", "points failure", "turned back", "skipped my stop", "wrong bus",
        "waited", "waiting for", "wait for", "no bus", "no train", "no tram",
    }
)

UNSUPPORTED_PERSON_TERMS: frozenset[str] = frozenset(
    {
        "someone", "somebody", "anyone", "stranger", "passerby", "passer-by", "neighbour",
        "neighbor", "friend", "buddy", "pal", "colleague", "coworker", "boss", "manager",
        "client", "customer", "teacher", "lecturer", "professor", "student", "child", "kid",
        "toddler", "baby", "son", "daughter", "husband", "wife", "partner", "boyfriend",
        "girlfriend", "spouse", "mum", "mom", "mother", "dad", "father", "brother", "sister",
        "grandmother", "grandfather", "grandma", "grandpa", "family", "relative", "team",
        "group of", "crowd", "people", "person", "man", "woman", "boy", "girl", "guy", "lady",
        "he", "she", "they", "him", "her", "them", "his", "hers", "their", "we", "us", "our",
    }
)
"""Person-referring terms.  A note may only use them when the social setting in
the context packet supports company (see :mod:`paper3_ema.notes`)."""

UNSUPPORTED_EVENT_TERMS: frozenset[str] = frozenset(
    {
        "meeting", "deadline", "presentation", "interview", "exam", "test", "call",
        "phone call", "email", "message", "notification", "alarm", "argument", "row",
        "fight", "argument", "news", "delivery", "parcel", "visitor", "knock", "queue",
        "errand", "appointment", "lecture", "class", "shift", "overtime", "crunch",
        "incident", "emergency", "spilled", "dropped", "lost", "forgot", "broke",
        "surprise", "unexpectedly", "suddenly", "cancelled",
    }
)

CAUSAL_MARKERS: frozenset[str] = frozenset(
    {
        "because", "cos", "cuz", "cause", "since", "due to", "thanks to", "owing to",
        "as a result of", "after", "led to", "made me", "makes me", "left me",
    }
)
"""Causal connectives.  A causal clause is only accepted when its cause is an
entity present in the context packet."""

APPROVED_CAUSE_CONCEPTS: frozenset[str] = frozenset(
    {
        # causes that are directly grounded in packet fields
        "walk", "walking", "run", "running", "cycle", "cycling", "ride", "trip", "journey",
        "commute", "bus", "train", "tram", "drive", "driving", "travel", "exercise",
        "workout", "training", "session", "work", "shift", "task", "housework", "chores",
        "cooking", "cleaning", "shopping", "childcare", "kids", "children", "meal",
        "breakfast", "lunch", "dinner", "break", "rest", "nap", "sleep", "night",
        "morning", "afternoon", "evening", "day", "early start", "long day", "being up",
        "sitting", "standing", "waiting", "transition", "change", "switch",
        "the company", "being with", "time with", "quiet", "noise", "the outdoors",
        "being outside", "being inside", "the day", "schedule", "the plan",
    }
)

BANNED_ABSOLUTES: frozenset[str] = frozenset(
    {
        # claims the EMA layer must never make about a synthetic participant
        "diagnosed", "diagnosis", "disorder", "disease", "chronic", "clinically",
        "medically", "prescribed", "therapy", "always", "never", "every day",
        "personality", "introvert", "extrovert", "neurotic", "trait",
    }
)

# Activity nouns that may only appear if the packet supports them.
ACTIVITY_NOUNS: dict[str, frozenset[Activity]] = {
    "walk": frozenset({Activity.WALKING}),
    "walking": frozenset({Activity.WALKING}),
    "stroll": frozenset({Activity.WALKING}),
    "hike": frozenset({Activity.WALKING}),
    "run": frozenset({Activity.RUNNING}),
    "running": frozenset({Activity.RUNNING}),
    "jog": frozenset({Activity.RUNNING}),
    "cycle": frozenset({Activity.CYCLING}),
    "cycling": frozenset({Activity.CYCLING}),
    "bike": frozenset({Activity.CYCLING}),
    "biking": frozenset({Activity.CYCLING}),
    "ride": frozenset({Activity.CYCLING}),
    "driving": frozenset({Activity.DRIVING}),
    "drive": frozenset({Activity.DRIVING}),
    "bus": frozenset({Activity.PUBLIC_TRANSPORT}),
    "train": frozenset({Activity.PUBLIC_TRANSPORT}),
    "tram": frozenset({Activity.PUBLIC_TRANSPORT}),
    "gym": frozenset({Activity.OTHER_VIGOROUS}),
    "workout": frozenset({Activity.OTHER_VIGOROUS}),
    "exercise": frozenset({Activity.OTHER_VIGOROUS, Activity.RUNNING, Activity.CYCLING}),
    "training": frozenset({Activity.OTHER_VIGOROUS}),
    "swim": frozenset({Activity.OTHER_VIGOROUS}),
    "sitting": frozenset({Activity.SITTING}),
    "standing": frozenset({Activity.STANDING}),
    "sleep": frozenset({Activity.SLEEPING}),
    "nap": frozenset({Activity.SLEEPING, Activity.LYING_AWAKE}),
}
