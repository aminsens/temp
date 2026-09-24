"""
City Profile Loader.

Loads city profile markdown files and provides them as context
to diary generation agents.

Usage:
    from osm.city_loader import load_city_profile, get_seasonal_context
    
    profile = load_city_profile("trondheim")
    context = get_seasonal_context("trondheim", month="january")
    # Feed context to the diary agent
"""

import os
from pathlib import Path

CITIES_DIR = Path(__file__).parent.parent / "cities"


def load_city_profile(city: str) -> str:
    """Load the full city profile markdown."""
    profile_path = CITIES_DIR / city.lower() / "profile.md"
    if not profile_path.exists():
        raise FileNotFoundError(f"No profile found for city: {city}. Expected: {profile_path}")
    return profile_path.read_text(encoding="utf-8")


def get_seasonal_context(city: str, month: str) -> str:
    """
    Extract seasonally-relevant context from the city profile.
    
    Returns a condensed string suitable for injection into agent prompts.
    """
    profile = load_city_profile(city)
    
    # Determine season
    month_lower = month.lower()[:3]
    season_map = {
        "dec": "winter", "jan": "winter", "feb": "winter",
        "mar": "spring", "apr": "spring", "may": "spring",
        "jun": "summer", "jul": "summer", "aug": "summer",
        "sep": "autumn", "oct": "autumn", "nov": "autumn",
    }
    season = season_map.get(month_lower, "spring")
    
    # Extract key sections by finding headers
    lines = profile.split("\n")
    sections = {}
    current_section = ""
    current_lines = []
    
    for line in lines:
        if line.startswith("## ") or line.startswith("### "):
            if current_section:
                sections[current_section] = "\n".join(current_lines)
            current_section = line.strip("# ").strip()
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_section:
        sections[current_section] = "\n".join(current_lines)
    
    # Build context: overview + geography + matching season + activity notes
    context_parts = []
    
    # Overview (always include)
    if "Overview" in sections:
        context_parts.append(sections["Overview"])
    
    # Geography terrain section
    for key in sections:
        if "terrain" in key.lower() or "topography" in key.lower():
            context_parts.append(sections[key][:500])
            break
    
    # Key neighbourhoods
    for key in sections:
        if "neighbourhood" in key.lower() or "landmark" in key.lower():
            context_parts.append(sections[key][:500])
            break
    
    # Matching season section
    month_names = {
        "jan": "january", "feb": "february", "mar": "march", "apr": "april",
        "may": "may", "jun": "june", "jul": "july", "aug": "august",
        "sep": "september", "oct": "october", "nov": "november", "dec": "december",
    }
    month_full = month_names.get(month_lower, month_lower)
    
    for key in sections:
        key_lower = key.lower()
        if season in key_lower or month_full in key_lower or month_lower in key_lower:
            context_parts.append(sections[key])
            break
    
    # Activity-specific notes
    for key in sections:
        if "activity" in key.lower() and "specific" in key.lower():
            context_parts.append(sections[key][:1000])
            break
    
    # Agent usage notes
    for key in sections:
        if "agent" in key.lower() and "usage" in key.lower():
            context_parts.append(sections[key])
            break
    
    if len(context_parts) >= 3:
        return "\n\n".join(context_parts)
    
    # Fallback: return truncated full profile
    return profile[:3000]


def list_available_cities() -> list[str]:
    """List cities with profiles available."""
    if not CITIES_DIR.exists():
        return []
    return [d.name for d in CITIES_DIR.iterdir() if d.is_dir() and (d / "profile.md").exists()]


def get_agent_prompt_section(city: str, month: str) -> str:
    """
    Get a formatted section for injection into diary agent prompts.
    
    This is what the agent sees as city context.
    """
    context = get_seasonal_context(city, month)
    
    return (
        f"CITY CONTEXT ({city}, {month}):\n"
        f"{'-' * 40}\n"
        f"{context}\n"
        f"{'-' * 40}\n"
        f"Use this context to generate geographically and seasonally accurate diary entries.\n"
        f"Reference real locations from the city. Consider weather and seasonal feasibility.\n"
    )


if __name__ == "__main__":
    print("Available cities:", list_available_cities())
    
    print("\n=== Trondheim, January ===")
    print(get_agent_prompt_section("trondheim", "january")[:800])
    
    print("\n=== Trondheim, July ===")
    print(get_agent_prompt_section("trondheim", "july")[:800])
