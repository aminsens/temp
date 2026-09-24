"""Closed-world validation for the optional one-sentence context note.

The note is an *interpretability* device, not a quantitative outcome.  The LLM
(or the offline template renderer) may refer **only** to entities, events,
places, activities and causes supplied in the :class:`EMAContextPacket`.

A generated note is rejected when it introduces any of:

``unsupported_person``, ``unsupported_place``, ``unsupported_activity``,
``unsupported_event``, ``unsupported_delay``, ``unsupported_weather``,
``unsupported_cause``, ``unsupported_journey``, ``medical_condition``,
``psychological_trait_inference``, ``demographic_reference``, ``proper_noun``,
``too_long``, ``multiple_sentences``, ``empty``, ``non_literal_claim``.

Rejected notes are retried by the renderer with the failure reasons attached;
if no safe output can be produced, ``context_note = null``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Sequence

from .config import ProtocolConfig, default_config
from .models import EMAContextPacket
from .vocab import (
    BANNED_ABSOLUTES,
    CAUSAL_MARKERS,
    MEDICAL_TERMS,
    TRANSPORT_DISRUPTION_TERMS,
    UNSUPPORTED_EVENT_TERMS,
    UNSUPPORTED_PERSON_TERMS,
    WEATHER_TERMS,
    Activity,
    Domain,
    PlaceType,
    SocialContext,
)

CAUSAL_SAFE: frozenset[str] = CAUSAL_MARKERS

NOTE_VALIDATOR_VERSION = "1.0.0"

COMPANY_SOCIAL = {
    SocialContext.WITH_PARTNER,
    SocialContext.WITH_FAMILY,
    SocialContext.WITH_CHILDREN,
    SocialContext.WITH_FRIENDS,
    SocialContext.WITH_COLLEAGUES,
    SocialContext.WITH_KNOWN_OTHERS,
    SocialContext.WITH_STRANGERS,
}

PLACE_TERM_TO_TYPES: dict[str, frozenset[PlaceType]] = {
    "home": frozenset({PlaceType.HOME}),
    "house": frozenset({PlaceType.HOME}),
    "flat": frozenset({PlaceType.HOME}),
    "apartment": frozenset({PlaceType.HOME}),
    "kitchen": frozenset({PlaceType.HOME}),
    "sofa": frozenset({PlaceType.HOME}),
    "desk": frozenset({PlaceType.HOME, PlaceType.WORKPLACE, PlaceType.SCHOOL}),
    "work": frozenset({PlaceType.WORKPLACE}),
    "office": frozenset({PlaceType.WORKPLACE}),
    "campus": frozenset({PlaceType.SCHOOL, PlaceType.WORKPLACE}),
    "school": frozenset({PlaceType.SCHOOL}),
    "university": frozenset({PlaceType.SCHOOL}),
    "library": frozenset({PlaceType.SCHOOL, PlaceType.OTHER_BUILDING}),
    "gym": frozenset({PlaceType.GYM}),
    "park": frozenset({PlaceType.PARK}),
    "shop": frozenset({PlaceType.SHOP}),
    "shops": frozenset({PlaceType.SHOP}),
    "store": frozenset({PlaceType.SHOP}),
    "supermarket": frozenset({PlaceType.SHOP}),
    "cafe": frozenset({PlaceType.FOOD_VENUE}),
    "restaurant": frozenset({PlaceType.FOOD_VENUE}),
    "canteen": frozenset({PlaceType.FOOD_VENUE}),

    "street": frozenset({PlaceType.STREET, PlaceType.OUTDOOR_GENERIC}),
    "road": frozenset({PlaceType.STREET, PlaceType.OUTDOOR_GENERIC}),
    "outside": frozenset({PlaceType.OUTDOOR_GENERIC, PlaceType.PARK, PlaceType.STREET}),
    "outdoors": frozenset({PlaceType.OUTDOOR_GENERIC, PlaceType.PARK, PlaceType.STREET}),
    "bus stop": frozenset({PlaceType.TRANSIT_STOP}),
    "stop": frozenset({PlaceType.TRANSIT_STOP}),
    "station": frozenset({PlaceType.TRANSIT_STOP}),
    "car": frozenset({PlaceType.VEHICLE}),
    "clinic": frozenset({PlaceType.HEALTHCARE}),
    "hospital": frozenset({PlaceType.HEALTHCARE}),
}

ACTIVITY_TERMS: dict[str, frozenset[Activity]] = {
    "walk": frozenset({Activity.WALKING}),
    "walks": frozenset({Activity.WALKING}),
    "walking": frozenset({Activity.WALKING}),
    "stroll": frozenset({Activity.WALKING}),
    "hike": frozenset({Activity.WALKING}),
    "run": frozenset({Activity.RUNNING}),
    "runs": frozenset({Activity.RUNNING}),
    "running": frozenset({Activity.RUNNING}),
    "jog": frozenset({Activity.RUNNING}),
    "cycle": frozenset({Activity.CYCLING}),
    "cycling": frozenset({Activity.CYCLING}),
    "bike": frozenset({Activity.CYCLING}),
    "biking": frozenset({Activity.CYCLING}),
    "ride": frozenset({Activity.CYCLING}),
    "driving": frozenset({Activity.DRIVING}),
    "drive": frozenset({Activity.DRIVING}),
    "workout": frozenset({Activity.OTHER_VIGOROUS}),
    "training": frozenset({Activity.OTHER_VIGOROUS}),
    "exercise": frozenset({Activity.OTHER_VIGOROUS, Activity.RUNNING, Activity.CYCLING, Activity.WALKING}),
    "gym session": frozenset({Activity.OTHER_VIGOROUS}),
    "sitting": frozenset({Activity.SITTING}),
    "standing": frozenset({Activity.STANDING}),
    "nap": frozenset({Activity.SLEEPING, Activity.LYING_AWAKE}),
    "sleep": frozenset({Activity.SLEEPING}),
    "commute": frozenset({Activity.WALKING, Activity.CYCLING, Activity.DRIVING, Activity.PUBLIC_TRANSPORT}),
    "commuting": frozenset({Activity.WALKING, Activity.CYCLING, Activity.DRIVING, Activity.PUBLIC_TRANSPORT}),
    "bus": frozenset({Activity.PUBLIC_TRANSPORT}),
    "train": frozenset({Activity.PUBLIC_TRANSPORT}),
    "tram": frozenset({Activity.PUBLIC_TRANSPORT}),
    "metro": frozenset({Activity.PUBLIC_TRANSPORT}),
    "ferry": frozenset({Activity.PUBLIC_TRANSPORT}),
    "trip": frozenset({Activity.WALKING, Activity.CYCLING, Activity.DRIVING, Activity.PUBLIC_TRANSPORT}),
    "journey": frozenset({Activity.WALKING, Activity.CYCLING, Activity.DRIVING, Activity.PUBLIC_TRANSPORT}),
}

DOMAIN_TERMS: dict[str, frozenset[Domain]] = {
    "work": frozenset({Domain.WORK}),
    "working": frozenset({Domain.WORK}),
    "job": frozenset({Domain.WORK}),
    "shift": frozenset({Domain.WORK}),
    "study": frozenset({Domain.STUDY}),
    "studying": frozenset({Domain.STUDY}),
    "class": frozenset({Domain.STUDY}),
    "lecture": frozenset({Domain.STUDY}),
    "homework": frozenset({Domain.STUDY}),
    "commute": frozenset({Domain.TRANSPORT}),
    "commuting": frozenset({Domain.TRANSPORT}),
    "trip": frozenset({Domain.TRANSPORT}),
    "journey": frozenset({Domain.TRANSPORT}),
    "travel": frozenset({Domain.TRANSPORT}),
    "housework": frozenset({Domain.HOUSEHOLD}),
    "chores": frozenset({Domain.HOUSEHOLD}),
    "cooking": frozenset({Domain.HOUSEHOLD}),
    "cleaning": frozenset({Domain.HOUSEHOLD}),
    "laundry": frozenset({Domain.HOUSEHOLD}),
    "childcare": frozenset({Domain.CHILDCARE}),
    "children": frozenset({Domain.CHILDCARE}),
    "kids": frozenset({Domain.CHILDCARE}),
    "exercise": frozenset({Domain.EXERCISE}),
    "workout": frozenset({Domain.EXERCISE}),
    "training": frozenset({Domain.EXERCISE}),
    "leisure": frozenset({Domain.LEISURE}),
    "free time": frozenset({Domain.LEISURE}),
    "hobby": frozenset({Domain.LEISURE}),
    "social": frozenset({Domain.SOCIAL}),
    "shopping": frozenset({Domain.SHOPPING}),
    "errand": frozenset({Domain.SHOPPING}),
    "errands": frozenset({Domain.SHOPPING}),
    "morning routine": frozenset({Domain.SELF_CARE}),
    "shower": frozenset({Domain.SELF_CARE}),
    "breakfast": frozenset({Domain.SELF_CARE, Domain.HOUSEHOLD}),
    "lunch": frozenset({Domain.SELF_CARE, Domain.SOCIAL, Domain.WORK}),
    "dinner": frozenset({Domain.SELF_CARE, Domain.HOUSEHOLD, Domain.SOCIAL}),
    "meal": frozenset({Domain.SELF_CARE, Domain.HOUSEHOLD, Domain.SOCIAL}),
}

APPROVED_STATE_WORDS: frozenset[str] = frozenset(
    {
        # subjective/affective vocabulary — always allowed (it is the point of the item)
        "good", "great", "fine", "okay", "ok", "alright", "nice", "pleasant", "glad", "happy",
        "content", "calm", "relaxed", "refreshed", "energised", "energized", "positive", "cheerful",
        "tired", "sleepy", "drowsy", "drained", "exhausted", "wiped", "fatigued", "weary",
        "low", "flat", "meh", "neutral", "steady", "sluggish", "rested", "awake", "alert",
        "stressed", "stressful", "tense", "pressured", "rushed", "uneasy", "wound", "wired",
        "irritated", "annoyed", "frustrated", "anxious", "worried", "nervous", "upbeat", "motivated",
        "ready", "done", "glad", "grateful", "proud", "satisfied", "bored", "restless", "heavy",
        "light", "bright", "dull", "flat", "mixed", "weird", "odd", "normal", "usual", "typical",
        # generic time / degree words
        "now", "right", "moment", "today", "morning", "afternoon", "evening", "night", "midday",
        "earlier", "before", "after", "just", "already", "still", "again", "soon", "later",
        "day", "start", "starts", "started", "end", "ends", "ended", "finish", "finished",
        "bit", "little", "quite", "very", "really", "pretty", "somewhat", "slightly", "a",
        "lot", "more", "less", "much", "enough", "getting", "feeling", "feel", "feels", "felt",
        "energy", "mood", "stress", "head", "mind", "body", "legs", "legs", "pace", "rhythm",
        "break", "rest", "pause", "quiet", "busy", "calm", "long", "short", "early", "late",
        "first", "next", "last", "another", "same", "different", "overall", "general",
        "glad", "company", "alone", "solo", "together", "with", "without", "about", "into",
        "the", "a", "an", "and", "but", "or", "so", "of", "in", "on", "at", "to", "for", "from",
        "it", "its", "this", "that", "these", "those", "i", "im", "my", "me", "you",
        "was", "were", "is", "am", "are", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "not", "no", "yes", "as", "than", "then", "when", "while",
        "up", "down", "out", "off", "over", "under", "through", "during", "since", "because",
        "some", "any", "all", "both", "each", "few", "many", "most", "other", "such",
        "here", "there", "where", "how", "what", "why", "who",
        "nothing", "anything", "something", "special", "regular", "quiet", "calm",
        "fine", "steady", "normal", "usual", "everyday", "ordinary", "plain",
        "called", "phoned", "texted", "missed", "skipped", "planned", "expected",
        "fairly", "rather", "slightly", "somewhat", "pretty", "quite", "reasonably",
        "average", "plenty", "left", "overall", "fading", "empty", "fresh", "drained",
        "point", "moment", "stage", "stretch", "spell",
    }
)

STOPWORDS: frozenset[str] = frozenset(
    {
        "the", "a", "an", "and", "or", "but", "so", "of", "in", "on", "at", "to", "for", "from",
        "with", "without", "into", "onto", "over", "under", "through", "during", "before",
        "after", "since", "because", "as", "than", "then", "when", "while", "it", "its", "this",
        "that", "these", "those", "i", "im", "my", "me", "we", "our", "us", "you", "your",
        "was", "were", "is", "am", "are", "be", "been", "being", "have", "has", "had", "do",
        "does", "did", "not", "no", "yes", "up", "down", "out", "off", "just", "really", "very",
        "quite", "pretty", "some", "any", "all", "both", "each", "few", "many", "most", "other",
        "such", "here", "there", "where", "how", "what", "why", "who", "right", "now", "today",
        "a bit", "lot", "more", "less", "much", "enough", "still", "already", "again",
    }
)

_WORD = re.compile(r"[a-z']+")
_SENTENCE_END = re.compile(r"[.!?;](?:\s|$)")


@dataclass
class NoteIssue:
    code: str
    message: str
    term: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "term": self.term}


@dataclass
class NoteValidation:
    valid: bool
    issues: list[NoteIssue] = field(default_factory=list)
    normalized: str = ""
    words: int = 0
    sentences: int = 0
    validator_version: str = NOTE_VALIDATOR_VERSION
    checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "issues": [issue.to_dict() for issue in self.issues],
            "codes": sorted({issue.code for issue in self.issues}),
            "normalized": self.normalized,
            "words": self.words,
            "sentences": self.sentences,
            "validator_version": self.validator_version,
            "checks": list(self.checks),
        }

    @property
    def codes(self) -> list[str]:
        return sorted({issue.code for issue in self.issues})


# --------------------------------------------------------------------------
# grounding sets derived from the packet
# --------------------------------------------------------------------------

def grounded_activities(packet: EMAContextPacket) -> set[Activity]:
    activities: set[Activity] = set()
    if packet.activity is not None:
        activities.add(packet.activity)
    if packet.preceding_activity is not None:
        activities.add(packet.preceding_activity)
    if packet.minutes_since_active_episode_end is not None:
        activities |= {Activity.RUNNING, Activity.CYCLING, Activity.OTHER_VIGOROUS, Activity.WALKING}
    if packet.minutes_since_journey_end is not None or packet.preceding_journey_mode:
        activities |= {Activity.WALKING, Activity.CYCLING, Activity.DRIVING, Activity.PUBLIC_TRANSPORT}
    mode = (packet.preceding_journey_mode or packet.current_journey_mode or "").lower()
    if mode in {"walk", "walking", "foot"}:
        activities.add(Activity.WALKING)
    if mode in {"bike", "bicycle", "cycling", "cycle"}:
        activities.add(Activity.CYCLING)
    if mode in {"car", "driving", "drive"}:
        activities.add(Activity.DRIVING)
    if mode in {"bus", "train", "tram", "metro", "subway", "ferry", "public_transport"}:
        activities.add(Activity.PUBLIC_TRANSPORT)
    return activities


def grounded_places(packet: EMAContextPacket) -> set[PlaceType]:
    places: set[PlaceType] = set()
    for value in (packet.place_type, packet.preceding_place_type):
        if value is not None:
            places.add(value)
    return places


def grounded_domains(packet: EMAContextPacket) -> set[Domain]:
    domains: set[Domain] = set()
    for value in (packet.domain, packet.preceding_domain):
        if value is not None:
            domains.add(value)
    if packet.purpose_category:
        for term, mapped in DOMAIN_TERMS.items():
            if term in str(packet.purpose_category).replace("_", " "):
                domains |= mapped
    if packet.minutes_to_next_commitment is not None and packet.next_commitment_kind:
        kind = str(packet.next_commitment_kind).lower()
        if "work" in kind:
            domains.add(Domain.WORK)
        if "care" in kind or "child" in kind:
            domains.add(Domain.CHILDCARE)
        if "study" in kind or "class" in kind:
            domains.add(Domain.STUDY)
        if "appointment" in kind or "medical" in kind:
            domains.add(Domain.OTHER)
        if "social" in kind:
            domains.add(Domain.SOCIAL)
    return domains


def grounded_event_concepts(packet: EMAContextPacket) -> set[str]:
    """Event-ish concepts the packet actually supports."""
    concepts: set[str] = set()
    if packet.minutes_to_next_commitment is not None:
        kind = str(packet.next_commitment_kind or "commitment").lower()
        concepts |= {"commitment", "appointment", "schedule", kind}
        if "work" in kind:
            concepts |= {"meeting", "shift", "work"}
        if "study" in kind or "class" in kind:
            concepts |= {"class", "lecture", "exam"}
    if packet.purpose_category:
        concepts.add(str(packet.purpose_category).replace("_", " "))
    if packet.domain is not None:
        concepts.add(packet.domain.value.replace("_", " "))
    if packet.minutes_since_journey_end is not None:
        concepts |= {"trip", "journey", "commute", "travel"}
    if packet.minutes_since_active_episode_end is not None:
        concepts |= {"exercise", "workout", "training", "session", "run", "ride"}
    if packet.minutes_since_activity_change is not None and packet.minutes_since_activity_change <= 20:
        concepts |= {"transition", "change", "switch"}
    concepts |= _grounded_meal_concepts(packet)
    concepts |= {str(packet.time_of_day).replace("_", " "), "morning", "afternoon", "evening", "night", "day"}
    if packet.minutes_in_current_episode is not None and packet.minutes_in_current_episode >= 20:
        concepts |= {"break", "pause", "rest"}
    return {concept for concept in concepts if concept}


def _grounded_meal_concepts(packet: EMAContextPacket) -> set[str]:
    """Meal references are grounded by clock time plus the current domain/purpose.

    This is a Paper 3 engineering rule (class C): a synthetic participant may
    only mention a meal when the prompt time sits in a conventional meal window
    and the inherited context is compatible with eating.
    """
    concepts: set[str] = set()
    minute = packet.prompt_time_min
    purpose = (packet.purpose_category or "").lower()
    domain = packet.domain.value if packet.domain is not None else ""
    eating_compatible = domain in {"self_care", "household", "social", "work", "study", "leisure", "other"}
    if not eating_compatible:
        return concepts
    if 5 * 60 <= minute < 10 * 60 and ("breakfast" in purpose or "meal" in purpose or domain in {"self_care", "household"}):
        concepts |= {"breakfast", "meal"}
    if 11 * 60 <= minute < 15 * 60 and ("lunch" in purpose or "meal" in purpose or domain in {"self_care", "social", "work", "study"}):
        concepts |= {"lunch", "meal"}
    if 17 * 60 <= minute < 22 * 60 and ("dinner" in purpose or "meal" in purpose or domain in {"self_care", "household", "social"}):
        concepts |= {"dinner", "meal"}
    return concepts


def grounded_weather(packet: EMAContextPacket) -> Optional[str]:
    return None if not packet.weather_available else "documented"


def company_supported(packet: EMAContextPacket) -> bool:
    return packet.social_context is not None and packet.social_context in COMPANY_SOCIAL


# --------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------

def _stem(token: str) -> str:
    """Remove only the unambiguous possessive suffix; plurals are handled
    by matching against pluralised variants of the known vocabulary."""
    if token.endswith("'s"):
        return token[:-2]
    return token


def _variants(word: str) -> set:
    """A word plus its naive plural forms (dictionary-free plural matching)."""
    out = {word}
    if word.endswith("s") or word.endswith("x") or word.endswith("z") or word.endswith("ch") or word.endswith("sh"):
        out.add(word + "es")
    else:
        out.add(word + "s")
    return out


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _phrases(text: str) -> set[str]:
    lowered = text.lower()
    return {phrase for phrase in _MULTIWORD_TERMS if phrase in lowered}


_MULTIWORD_TERMS: frozenset[str] = frozenset(
    {
        "bus stop", "train station", "free time", "morning routine", "gym session",
        "running late", "traffic jam", "road works", "roadworks", "signal failure",
        "blood test", "chest tightness", "recovery from illness", "group of", "public transport",
    }
)


def validate_note(
    note: Optional[str],
    packet: EMAContextPacket,
    config: Optional[ProtocolConfig] = None,
) -> NoteValidation:
    """Validate one candidate note against the closed-world contract."""
    config = config or default_config()
    section = config.section("note")
    max_words = int(section.get("max_words", 24))
    max_chars = int(section.get("max_chars", 160))
    max_sentences = int(section.get("max_sentences", 1))

    issues: list[NoteIssue] = []
    checks = [
        "length", "sentence_count", "proper_nouns", "weather", "medical",
        "transport_disruption", "persons", "activities", "places", "domains",
        "events", "traits", "absolutes", "closed_world_net", "causal_grounding", "format",
    ]

    if note is None:
        return NoteValidation(valid=True, issues=[], normalized="", words=0, sentences=0, checks=checks)
    text = str(note).strip().strip("\"'“”‘’").strip()
    if not text:
        return NoteValidation(valid=False, issues=[NoteIssue("empty", "note is empty")], checks=checks)

    # ---- format / length -------------------------------------------------
    normalized = re.sub(r"\s+", " ", text)
    tokens = _tokens(normalized)
    sentences = len([part for part in _SENTENCE_END.split(normalized) if part.strip()]) or 1
    if len(normalized) > max_chars:
        issues.append(NoteIssue("too_long", f"note exceeds {max_chars} characters ({len(normalized)})", None))
    if len(tokens) > max_words:
        issues.append(NoteIssue("too_long", f"note exceeds {max_words} words ({len(tokens)})", None))
    if sentences > max_sentences:
        issues.append(NoteIssue("multiple_sentences", f"note contains {sentences} sentences; maximum is {max_sentences}", None))
    if normalized.lower() in {"null", "none", "n/a", "unknown", "no comment"}:
        issues.append(NoteIssue("empty", f"note is a placeholder string: {normalized!r}", None))

    lowered = normalized.lower()
    phrases = _phrases(normalized)

    # ---- proper nouns (unsupported people / places) ----------------------
    for match in re.finditer(r"\b([A-Z][a-zA-Z'’-]+)\b", normalized):
        word = match.group(1)
        position = match.start()
        if position == 0:
            continue  # sentence-initial capitalisation is not evidence of a name
        if word.lower() in {"i", "i'm", "im", "ema", "ok", "okay"}:
            continue
        issues.append(NoteIssue("proper_noun", f"proper noun {word!r} is not part of the supplied context", word))

    # ---- weather ---------------------------------------------------------
    weather_terms = _match_terms(lowered, phrases, WEATHER_TERMS)
    if weather_terms and not packet.weather_available:
        for term in weather_terms:
            issues.append(NoteIssue("unsupported_weather", f"weather reference {term!r} is not documented in the context packet", term))

    # ---- medical ---------------------------------------------------------
    for term in _match_terms(lowered, phrases, MEDICAL_TERMS):
        issues.append(NoteIssue("medical_condition", f"medical/health reference {term!r} is not allowed", term))

    # ---- transport disruption -------------------------------------------
    delay_terms = _match_terms(lowered, phrases, TRANSPORT_DISRUPTION_TERMS)
    delay_documented = bool(packet.preceding_journey_delayed) or bool(packet.preceding_journey_crowded)
    if delay_terms and not delay_documented:
        for term in delay_terms:
            issues.append(
                NoteIssue("unsupported_delay", f"delay/disruption reference {term!r} is not documented in the context packet", term)
            )

    # ---- persons ---------------------------------------------------------
    person_terms = _match_terms(lowered, phrases, UNSUPPORTED_PERSON_TERMS)
    if person_terms and not company_supported(packet):
        for term in person_terms:
            social = packet.social_context.value if packet.social_context else "unknown"
            issues.append(
                NoteIssue(
                    "unsupported_person",
                    f"person reference {term!r} is not supported by the social setting ({social})",
                    term,
                )
            )

    # ---- activities ------------------------------------------------------
    allowed_activities = grounded_activities(packet)
    for term, activities in ACTIVITY_TERMS.items():
        if term in phrases or re.search(rf"\b{re.escape(term)}\b", lowered):
            if _idiom_exempt(term, lowered):
                continue
            if not (activities & allowed_activities):
                issues.append(
                    NoteIssue(
                        "unsupported_activity",
                        f"activity reference {term!r} is not in the supplied context "
                        f"(grounded: {sorted(a.value for a in allowed_activities) or 'none'})",
                        term,
                    )
                )

    # ---- places ----------------------------------------------------------
    allowed_places = grounded_places(packet)
    for term, places in PLACE_TERM_TO_TYPES.items():
        if term in phrases or re.search(rf"\b{re.escape(term)}\b", lowered):
            if _idiom_exempt(term, lowered):
                continue
            if not (places & allowed_places):
                issues.append(
                    NoteIssue(
                        "unsupported_place",
                        f"place reference {term!r} is not in the supplied context "
                        f"(grounded: {sorted(p.value for p in allowed_places) or 'none'})",
                        term,
                    )
                )

    # ---- domains ---------------------------------------------------------
    allowed_domains = grounded_domains(packet)
    recent_activity_terms = set()
    if packet.minutes_since_active_episode_end is not None:
        recent_activity_terms |= {"exercise", "workout", "training", "session", "run", "ride", "walk", "bike", "gym"}
    if (
        packet.minutes_since_journey_end is not None
        or packet.preceding_journey_mode
        or packet.current_journey_mode
    ):
        recent_activity_terms |= {"trip", "journey", "commute", "travel"}
    for term, domains in DOMAIN_TERMS.items():
        if term in {"lunch", "dinner", "breakfast", "meal"}:
            continue  # handled as events below; meals are not domain claims
        if term in phrases or re.search(rf"\b{re.escape(term)}\b", lowered):
            if term in recent_activity_terms:
                continue  # a just-finished active episode grounds exercise language
            if not (domains & allowed_domains):
                issues.append(
                    NoteIssue(
                        "unsupported_event",
                        f"domain/activity reference {term!r} is not grounded in the context packet",
                        term,
                    )
                )

    # ---- events ----------------------------------------------------------
    grounded_events = grounded_event_concepts(packet)
    for term in sorted(UNSUPPORTED_EVENT_TERMS):
        if term in phrases or re.search(rf"\b{re.escape(term)}\b", lowered):
            if term in grounded_events or any(term in concept for concept in grounded_events):
                continue
            issues.append(
                NoteIssue("unsupported_event", f"event reference {term!r} is not documented in the context packet", term)
            )
    for term in ("lunch", "dinner", "breakfast", "meal"):
        if re.search(rf"\b{term}\b", lowered) and "meal" not in grounded_events and not any(
            item in grounded_events for item in ("meal", term)
        ):
            issues.append(NoteIssue("unsupported_event", f"meal reference {term!r} is not documented in the context packet", term))

    # ---- journeys --------------------------------------------------------
    journey_terms = {"journey", "trip", "commute", "ride", "drive", "flight"}
    if (journey_terms & set(tokens)) and not (
        packet.minutes_since_journey_end is not None
        or packet.preceding_journey_mode
        or packet.current_journey_mode
        or (packet.domain is Domain.TRANSPORT)
    ):
        issues.append(NoteIssue("unsupported_journey", "journey reference without any journey in the context packet", None))

    # ---- traits / absolutes / demographics -------------------------------
    for term in BANNED_ABSOLUTES:
        if re.search(rf"\b{re.escape(term)}\b", lowered):
            code = "psychological_trait_inference" if term in {"personality", "introvert", "extrovert", "neurotic", "trait"} else "non_literal_claim"
            issues.append(NoteIssue(code, f"banned claim {term!r}: EMA notes must not make trait/diagnostic/absolute claims", term))
    for term in ("years old", "age ", "my age", "as a man", "as a woman", "for my age", "my job as", "my diagnosis"):
        if term in lowered:
            issues.append(NoteIssue("demographic_reference", f"demographic reference {term!r} is not allowed", term.strip()))

    # ---- generic closed-world net (unknown, ungrounded content terms) ----
    lexicon_words: set[str] = set()
    for term in WEATHER_TERMS | MEDICAL_TERMS | TRANSPORT_DISRUPTION_TERMS | UNSUPPORTED_PERSON_TERMS | UNSUPPORTED_EVENT_TERMS:
        for token in _tokens(term):
            lexicon_words.add(token)
    for term in ACTIVITY_TERMS:
        lexicon_words.update(_tokens(term))
    for term in PLACE_TERM_TO_TYPES:
        lexicon_words.update(_tokens(term))
    for term in DOMAIN_TERMS:
        lexicon_words.update(_tokens(term))
    for term in BANNED_ABSOLUTES:
        lexicon_words.update(_tokens(term))
    for term in CAUSAL_SAFE:
        lexicon_words.update(_tokens(term))
    lexicon_variants = set()
    for word in lexicon_words:
        lexicon_variants |= _variants(word)
    packet_variants = set()
    for word in _packet_word_set(packet):
        packet_variants |= _variants(word)
    for token in tokens:
        stem = _stem(token)
        if token in STOPWORDS or stem in STOPWORDS:
            continue
        if token in APPROVED_STATE_WORDS or stem in APPROVED_STATE_WORDS:
            continue
        if _looks_like_state_word(token) or _looks_like_state_word(stem):
            continue
        if token in lexicon_variants:
            continue  # already covered by a specific category check above
        if token in packet_variants:
            continue
        issues.append(
            NoteIssue(
                "unsupported_reference",
                f"term {token!r} is not part of the supplied context packet and is not approved subjective vocabulary",
                token,
            )
        )

    # ---- unsupported causes (causal clauses must be packet-grounded) -----
    for term in _causal_clause_terms(normalized):
        if not _cause_is_grounded(term, packet):
            issues.append(
                NoteIssue(
                    "unsupported_cause",
                    f"causal reference {term!r} is not an entity or event supplied in the context packet",
                    term,
                )
            )

    # de-duplicate while preserving order
    seen: set[tuple[str, Optional[str]]] = set()
    unique: list[NoteIssue] = []
    for issue in issues:
        key = (issue.code, issue.term)
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)

    return NoteValidation(
        valid=not unique,
        issues=unique,
        normalized=normalized,
        words=len(tokens),
        sentences=sentences,
        checks=checks,
    )


_CAUSAL_MARKER_RE = re.compile(
    r"\b(because|cos|cuz|cause|since|due to|thanks to|owing to|as a result of)\b\s*([^.;,!?]*)"
)


def _causal_clause_terms(text: str) -> list[str]:
    """Content words that appear inside an explicit causal clause."""
    terms: list[str] = []
    for _, clause in _CAUSAL_MARKER_RE.findall(text.lower()):
        for token in _tokens(clause):
            stem = _stem(token)
            if token in STOPWORDS or stem in STOPWORDS:
                continue
            if token in APPROVED_STATE_WORDS or stem in APPROVED_STATE_WORDS:
                continue
            if _looks_like_state_word(token) or _looks_like_state_word(stem):
                continue
            terms.append(token)
    return terms


def _cause_is_grounded(term: str, packet: EMAContextPacket) -> bool:
    stem = _stem(term)
    grounded = set()
    for word in _packet_word_set(packet):
        grounded |= _variants(word)
    return term in grounded or stem in grounded


def _packet_word_set(packet: EMAContextPacket) -> set[str]:
    """Strictly packet-derived vocabulary (used for causal-clause grounding)."""
    words: set[str] = set()

    def add(text: Optional[str]) -> None:
        if not text:
            return
        for token in _tokens(str(text).replace("_", " ")):
            if token not in STOPWORDS:
                words.add(token)

    add(packet.time_of_day)
    add(packet.purpose_category)
    add(packet.next_commitment_kind)
    add(packet.activity.value if packet.activity else None)
    add(packet.preceding_activity.value if packet.preceding_activity else None)
    add(packet.domain.value if packet.domain else None)
    add(packet.preceding_domain.value if packet.preceding_domain else None)
    add(packet.place_type.value if packet.place_type else None)
    add(packet.preceding_place_type.value if packet.preceding_place_type else None)
    add(packet.social_context.value if packet.social_context else None)
    add(packet.preceding_journey_mode)
    add(packet.current_journey_mode)
    for entity in packet.allowed_entities:
        add(entity)
    for cause in packet.allowed_causes:
        add(cause)
    for concept in grounded_event_concepts(packet):
        add(concept)
    for term, activities in ACTIVITY_TERMS.items():
        if activities & grounded_activities(packet):
            add(term)
    for term, places in PLACE_TERM_TO_TYPES.items():
        if places & grounded_places(packet):
            add(term)
    for term, domains in DOMAIN_TERMS.items():
        if domains & grounded_domains(packet):
            add(term)
    return words


def _match_terms(lowered: str, phrases: set[str], lexicon: Iterable[str]) -> list[str]:
    found: list[str] = []
    for term in lexicon:
        if " " in term:
            if term in phrases or term in lowered:
                found.append(term)
        elif re.search(rf"\b{re.escape(term)}\b", lowered):
            found.append(term)
    return sorted(set(found))


_STATE_WORD_PATTERN = re.compile(
    r"^(feel|feels|feeling|felt|tired|sleepy|drained|exhausted|stressed|calm|relaxed|happy|glad|"
    r"sad|low|high|good|bad|great|fine|okay|ok|ready|motivated|anxious|worried|irritated|annoyed|"
    r"frustrated|content|upbeat|wiped|sluggish|rested|alert|awake|energised|energized|refreshed|"
    r"positive|negative|neutral|mixed|weird|odd|normal|usual|typical|heavy|light|bright|dull|bored|"
    r"restless|satisfied|proud|grateful|done|wound|wired|tense|pressured|rushed|uneasy|meh|flat|steady)$"
)


def _looks_like_state_word(token: str) -> bool:
    return bool(_STATE_WORD_PATTERN.match(token))


# Words that double as everyday idioms.  When the note contains one of these
# fixed phrases the word is NOT a factual claim (e.g. "running low on energy"
# does not claim a running episode) and is exempt from the specific check.
_IDIOM_EXEMPTIONS: dict[str, re.Pattern] = {
    "flat": re.compile(r"feeling\s+flat|in a flat mood"),
    "running": re.compile(r"running\s+(low|down|out|on empty)|energy\s+(is\s+)?running"),
    "drive": re.compile(r"drive\s+(by|through|past)"),
    "rest": re.compile(r"at rest|come to rest"),
}


def _idiom_exempt(term: str, lowered: str) -> bool:
    pattern = _IDIOM_EXEMPTIONS.get(term)
    return bool(pattern and pattern.search(lowered))


def rejection_feedback(validation: NoteValidation) -> str:
    """Compact correction instruction fed back to the model on retry."""
    if validation.valid:
        return ""
    lines = [f"- {issue.code}: {issue.message}" for issue in validation.issues]
    return (
        "Your previous note was REJECTED. Fix every issue below and reply again with JSON only.\n"
        + "\n".join(lines)
    )


def summarise_validation(validation: NoteValidation) -> str:  # pragma: no cover - debug helper
    return "VALID" if validation.valid else "REJECTED: " + ", ".join(validation.codes)


def null_reason(validation: NoteValidation) -> str:
    return "closed_world_violation:" + ",".join(validation.codes) if not validation.valid else "accepted"
