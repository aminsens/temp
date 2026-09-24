"""
Backstory Generator — Day Context for the Jar of Life.

Before placing rocks, pebbles, and sand, generate the DAY CONTEXT:
- Sleep quality last night
- Energy level today
- Key events (meetings, deadlines, social plans)
- Mood baseline
- Weather influence
- Carry-over from yesterday

This backstory influences every downstream decision:
which pebbles get placed, narrative tone, activity choices, fatigue arc.
"""

import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class DayBackstory:
    """The context that shapes an entire day."""
    day_of_week: str
    month: str
    season: str
    
    # Sleep
    sleep_quality: str          # "good", "okay", "poor"
    sleep_hours: float
    wake_feeling: str           # "refreshed", "groggy", "tired"
    
    # Energy
    energy_level: str           # "high", "moderate", "low"
    energy_curve: str           # "steady", "morning_peak", "afternoon_dip", "declining"
    
    # Mood
    mood_baseline: str          # "positive", "neutral", "slightly_low"
    mood_narrative: str         # "Feeling optimistic about the week"
    
    # Key events today
    has_big_event: bool         # presentation, deadline, interview
    big_event_description: str  # "14:00 architecture presentation to leadership"
    has_social_plan: bool       # dinner with friends, date night
    social_description: str     # "Marie's parents visiting Thursday"
    
    # Carry-over from yesterday
    physical_carryover: str     # "legs sore from yesterday's run", "none"
    mental_carryover: str       # "still thinking about the bug", "none"
    pending_tasks: str          # "need to reply to Morten's email", "none"
    
    # Weather influence
    weather: str                # "sunny", "cloudy", "rainy", "snowy", "windy"
    weather_effect: str         # "motivating for outdoor activity", "prefers indoor"
    temperature_c: int
    
    # Day archetype
    day_archetype: str          # "normal_grind", "deadline_pressure", "relaxed", "social_heavy", "recovery"
    
    # Narrative
    backstory_narrative: str    # Full paragraph summarizing the day's context
    
    def fatigue_modifier(self) -> str:
        """Return fatigue starting point based on backstory."""
        if self.sleep_quality == "poor" or self.energy_level == "low":
            return "moderate"
        elif self.sleep_quality == "okay":
            return "mild"
        else:
            return "low"
    
    def exercise_likelihood(self) -> float:
        """Return 0-1 probability of exercising today."""
        base = 0.7
        if self.energy_level == "low":
            base -= 0.3
        if self.weather == "rainy":
            base -= 0.2
        if self.physical_carryover != "none":
            base -= 0.1
        if self.day_archetype == "deadline_pressure":
            base -= 0.2
        if self.day_archetype == "recovery":
            base -= 0.4
        return max(0.1, min(0.95, base))
    
    def social_likelihood(self) -> float:
        """Return 0-1 probability of social activities."""
        base = 0.5
        if self.has_social_plan:
            base += 0.3
        if self.mood_baseline == "positive":
            base += 0.1
        if self.day_archetype == "social_heavy":
            base += 0.2
        return max(0.1, min(0.95, base))


def generate_backstory(
    persona: dict,
    day_of_week: str,
    month: str = "april",
    previous_day_summary: Optional[dict] = None,
    seed: int = 42,
) -> DayBackstory:
    """
    Generate a day backstory.
    
    Uses programmatic rules + random variation (no LLM needed).
    The backstory is deterministic given the seed.
    """
    rng = random.Random(seed)
    
    # Season from month
    month_lower = month.lower()[:3]
    season_map = {
        "dec": "winter", "jan": "winter", "feb": "winter",
        "mar": "spring", "apr": "spring", "may": "spring",
        "jun": "summer", "jul": "summer", "aug": "summer",
        "sep": "autumn", "oct": "autumn", "nov": "autumn",
    }
    season = season_map.get(month_lower, "spring")
    
    # Weather (season-appropriate)
    weather_options = {
        "spring": [("cloudy", 8), ("rainy", 10), ("sunny", 12), ("partly_cloudy", 10)],
        "summer": [("sunny", 18), ("partly_cloudy", 15), ("rainy", 12), ("warm_sunny", 20)],
        "autumn": [("rainy", 6), ("cloudy", 8), ("windy", 7), ("partly_cloudy", 9)],
        "winter": [("snowy", -2), ("cloudy", -1), ("clear_cold", -5), ("rainy", 2)],
    }
    weather_choices = weather_options.get(season, weather_options["spring"])
    weather, temp_c = rng.choice(weather_choices)
    
    weather_effect = "neutral"
    if weather in ["sunny", "warm_sunny"]:
        weather_effect = "motivating for outdoor activity"
    elif weather in ["rainy", "snowy"]:
        weather_effect = "prefers indoor activities"
    elif weather in ["clear_cold", "windy"]:
        weather_effect = "invigorating if dressed properly"
    
    # Sleep quality
    sleep_rolls = rng.random()
    if sleep_rolls < 0.2:
        sleep_quality = "poor"
        sleep_hours = round(rng.uniform(4.5, 6.0), 1)
        wake_feeling = rng.choice(["groggy", "tired", "exhausted"])
    elif sleep_rolls < 0.5:
        sleep_quality = "okay"
        sleep_hours = round(rng.uniform(6.0, 7.5), 1)
        wake_feeling = rng.choice(["okay", "slightly groggy"])
    else:
        sleep_quality = "good"
        sleep_hours = round(rng.uniform(7.0, 8.5), 1)
        wake_feeling = rng.choice(["refreshed", "well-rested", "good"])
    
    # Carry-over from previous day
    physical_carryover = "none"
    mental_carryover = "none"
    pending_tasks = "none"
    
    if previous_day_summary:
        if previous_day_summary.get("had_exercise"):
            physical_carryover = rng.choice([
                "legs slightly sore from yesterday's workout",
                "muscles feel recovered, light residual soreness",
                "none",
            ])
        if previous_day_summary.get("work_stress"):
            mental_carryover = rng.choice([
                "still thinking about the code review discussion",
                "feeling good about yesterday's progress",
                "slightly anxious about upcoming deadline",
                "none",
            ])
    
    # Day archetype (depends on day of week + random)
    is_weekend = day_of_week in ["Saturday", "Sunday"]
    
    if is_weekend:
        archetype_rolls = rng.random()
        if archetype_rolls < 0.4:
            day_archetype = "relaxed"
        elif archetype_rolls < 0.7:
            day_archetype = "social_heavy"
        else:
            day_archetype = "active_outdoor"
    else:
        archetype_rolls = rng.random()
        if archetype_rolls < 0.5:
            day_archetype = "normal_grind"
        elif archetype_rolls < 0.7:
            day_archetype = "deadline_pressure"
        elif archetype_rolls < 0.85:
            day_archetype = "relaxed"
        else:
            day_archetype = "social_heavy"
    
    # Big events
    has_big_event = False
    big_event_description = ""
    if not is_weekend and rng.random() < 0.25:
        has_big_event = True
        big_event_description = rng.choice([
            "14:00 architecture presentation to team leads",
            "10:00 sprint review with stakeholders",
            "15:00 one-on-one with manager",
            "11:00 code review with senior architect",
            "all-day deadline for feature branch merge",
        ])
    
    # Social plans
    has_social_plan = False
    social_description = ""
    if rng.random() < 0.35:
        has_social_plan = True
        social_description = rng.choice([
            "evening dinner with Marie's friends",
            "after-work drinks with Morten and Kari",
            "video call with parents",
            "gym session with colleague",
            "planned hike with friends this weekend",
        ])
    
    # Energy level
    if sleep_quality == "poor":
        energy_level = "low"
    elif sleep_quality == "okay":
        energy_level = rng.choice(["moderate", "low"])
    else:
        energy_level = rng.choice(["high", "moderate"])
    
    # Energy curve
    if day_archetype == "deadline_pressure":
        energy_curve = "declining"
    elif day_archetype == "relaxed":
        energy_curve = "steady"
    elif energy_level == "high":
        energy_curve = "morning_peak"
    else:
        energy_curve = "afternoon_dip"
    
    # Mood
    if sleep_quality == "poor":
        mood_baseline = rng.choice(["neutral", "slightly_low"])
    elif has_social_plan:
        mood_baseline = rng.choice(["positive", "neutral"])
    else:
        mood_baseline = rng.choice(["positive", "neutral", "neutral"])
    
    mood_narratives = {
        "positive": [
            "Feeling optimistic about the week ahead",
            "Good energy, looking forward to the day",
            "Mood is up — the spring weather helps",
        ],
        "neutral": [
            "Steady mood, nothing special either way",
            "Getting through the day, no strong feelings",
            "Baseline — focused on routine",
        ],
        "slightly_low": [
            "A bit flat today, could be the poor sleep",
            "Low energy, taking things slowly",
            "Not feeling 100%, but managing",
        ],
    }
    mood_narrative = rng.choice(mood_narratives.get(mood_baseline, mood_narratives["neutral"]))
    
    # Build backstory narrative
    parts = []
    parts.append(f"It is {day_of_week} morning in {month}.")
    
    if sleep_quality == "poor":
        parts.append(f"Sleep was poor — only {sleep_hours} hours. {wake_feeling.capitalize()}.")
    elif sleep_quality == "okay":
        parts.append(f"Sleep was okay — {sleep_hours} hours. {wake_feeling.capitalize()}.")
    else:
        parts.append(f"Sleep was good — {sleep_hours} hours. Woke up {wake_feeling}.")
    
    parts.append(f"{mood_narrative}.")
    
    if has_big_event:
        parts.append(f"Key event today: {big_event_description}.")
    
    if has_social_plan:
        parts.append(f"Social plan: {social_description}.")
    
    if physical_carryover != "none":
        parts.append(f"Physical note: {physical_carryover}.")
    
    parts.append(f"Weather: {weather}, {temp_c}°C. {weather_effect.capitalize()}.")
    
    if day_archetype == "deadline_pressure":
        parts.append("Sense of time pressure — need to be efficient today.")
    elif day_archetype == "relaxed":
        parts.append("No urgency today — can take things at a comfortable pace.")
    elif day_archetype == "social_heavy":
        parts.append("Social energy today — looking forward to people time.")
    
    backstory_narrative = " ".join(parts)
    
    return DayBackstory(
        day_of_week=day_of_week,
        month=month,
        season=season,
        sleep_quality=sleep_quality,
        sleep_hours=sleep_hours,
        wake_feeling=wake_feeling,
        energy_level=energy_level,
        energy_curve=energy_curve,
        mood_baseline=mood_baseline,
        mood_narrative=mood_narrative,
        has_big_event=has_big_event,
        big_event_description=big_event_description,
        has_social_plan=has_social_plan,
        social_description=social_description,
        physical_carryover=physical_carryover,
        mental_carryover=mental_carryover,
        pending_tasks=pending_tasks,
        weather=weather,
        weather_effect=weather_effect,
        temperature_c=temp_c,
        day_archetype=day_archetype,
        backstory_narrative=backstory_narrative,
    )


if __name__ == "__main__":
    persona = {"name": "Erik", "age": 32, "occupation": "developer"}
    
    for seed in range(5):
        bs = generate_backstory(persona, "Monday", "april", seed=seed)
        print(f"\n=== Seed {seed} ===")
        print(f"Archetype: {bs.day_archetype}")
        print(f"Sleep: {bs.sleep_quality} ({bs.sleep_hours}h) → {bs.wake_feeling}")
        print(f"Energy: {bs.energy_level} ({bs.energy_curve})")
        print(f"Mood: {bs.mood_baseline} — {bs.mood_narrative}")
        print(f"Weather: {bs.weather}, {bs.temperature_c}°C")
        print(f"Big event: {bs.has_big_event} {bs.big_event_description}")
        print(f"Social: {bs.has_social_plan} {bs.social_description}")
        print(f"Exercise likelihood: {bs.exercise_likelihood():.0%}")
        print(f"Narrative: {bs.backstory_narrative[:150]}...")
