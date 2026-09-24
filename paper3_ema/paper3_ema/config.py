"""Protocol configuration loading for the Paper 3 EMA module.

Policy lives in ``config/paper3_ema_v1.yaml`` — never in source constants.
PyYAML is used when available; otherwise a small built-in parser handles the
shipped file (a strict YAML subset: block mappings, block sequences, flow
sequences/mappings, quoted and plain scalars, ``>``/``|`` block scalars and
``#`` comments).  The loader validates that every required key is present and
fails loudly rather than silently applying a default policy.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Iterable, Optional

PROTOCOL_NAME = "paper3_ema_v1"
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "config" / f"{PROTOCOL_NAME}.yaml"

REQUIRED_KEYS: tuple[str, ...] = (
    "meta.protocol_name",
    "meta.protocol_version",
    "meta.schema_version",
    "scales.points",
    "scales.items.valence.anchors",
    "scales.items.energy.anchors",
    "scales.items.stress.anchors",
    "sampling.opportunities_per_day",
    "sampling.min_background",
    "sampling.max_event_enriched",
    "sampling.force_event_diversity",
    "sampling.waking_windows.default_start",
    "sampling.waking_windows.default_end",
    "sampling.waking_windows.default_count",
    "sampling.min_gap_minutes",
    "sampling.stability_margin_minutes",
    "sampling.max_minutes_after_event",
    "eligibility.exclude_activities",
    "eligibility.exclude_unresolved_intervals",
    "eligibility.exclude_non_realised_movements",
    "eligibility.exclude_unstable_micro_transitions",
    "events.priority",
    "events.post_active_episode.min_duration_minutes",
    "events.context_transition.min_stable_minutes_before",
    "state_generator.version",
    "state_generator.baseline",
    "state_generator.noise_sd",
    "state_generator.modifiers",
    "state_generator.sampling.sd",
    "persona.allowed_facts",
    "persona.forbidden_facts",
    "persona.strict",
    "missingness.model",
    "missingness.force_one_miss_per_day",
    "missingness.base_response_probability",
    "missingness.calibration_target_response_rate",
    "latency.distribution",
    "latency.expiry_minutes",
    "latency.expired_policy",
    "latency.context_reference_time",
    "note.enabled",
    "note.max_sentences",
    "note.max_words",
    "llm.provider",
    "llm.model",
    "llm.template_version",
    "llm.role",
    "llm.allowed_to_select_subjective_values",
    "validation.expected_opportunities",
    "provenance.record_field_origin",
)


class ConfigError(RuntimeError):
    """Raised when the protocol configuration is missing or malformed."""


# ==========================================================================
# minimal YAML subset parser
# ==========================================================================

_FLOW_SEQ = re.compile(r"^\[(?P<body>.*)\]$", re.DOTALL)
_FLOW_MAP = re.compile(r"^\{(?P<body>.*)\}$", re.DOTALL)
_BLOCK_SCALAR = re.compile(r"^(?P<key>[^:]+):\s*(?P<style>>-?|\|-?)$")


_NUMERIC_KEY = re.compile(r"^(-?\d+)\s*:(.*)$")


def _normalise_numeric_keys(content: str) -> str:
    """Quote integer mapping keys so they survive as ints (scale anchors, horizons)."""
    match = _NUMERIC_KEY.match(content)
    if match:
        return f'"{match.group(1)}":{match.group(2)}'
    return content


def _coerce_key(key: str) -> Any:
    """Integer mapping keys are coerced to ``int`` (matches PyYAML behaviour)."""
    if re.fullmatch(r"-?\d+", key):
        return int(key)
    return key

def _strip_comment(line: str) -> str:
    out, quote = [], None
    for ch in line:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            out.append(ch)
            continue
        if ch == "#":
            break
        out.append(ch)
    return "".join(out).rstrip()


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return None
    if text.startswith(("\"", "'")) and text.endswith(text[0]) and len(text) >= 2:
        return text[1:-1]
    low = text.lower()
    if low in {"null", "none", "~"}:
        return None
    if low in {"true", "yes", "on"}:
        return True
    if low in {"false", "no", "off"}:
        return False
    seq = _FLOW_SEQ.match(text)
    if seq:
        body = seq.group("body").strip()
        return [_parse_scalar(part) for part in _split_flow(body)] if body else []
    fmap = _FLOW_MAP.match(text)
    if fmap:
        body = fmap.group("body").strip()
        result: dict[str, Any] = {}
        for part in _split_flow(body):
            if not part.strip():
                continue
            key, _, value = part.partition(":")
            result[_coerce_key(str(_parse_scalar(key)))] = _parse_scalar(value)
        return result
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def _split_flow(body: str) -> list[str]:
    """Split a flow body on top-level commas (respecting nesting and quotes)."""
    parts, depth, quote, current = [], 0, None, []
    for ch in body:
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            current.append(ch)
            continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def _tokenize(text: str) -> list[tuple[int, str, str]]:
    """Return ``(indent, kind, content)`` for each significant line."""
    tokens: list[tuple[int, str, str]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        raw = lines[index]
        stripped = _strip_comment(raw)
        if not stripped.strip():
            index += 1
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        content = _normalise_numeric_keys(stripped.strip())
        block = _BLOCK_SCALAR.match(content)
        if block:
            # block scalar: "key: >", "key: >-", "key: |", "key: |-"
            key = block.group("key").strip()
            folded = block.group("style").startswith(">")
            collected: list[str] = []
            index += 1
            block_indent: Optional[int] = None
            while index < len(lines):
                line = lines[index]
                if not line.strip():
                    collected.append("")
                    index += 1
                    continue
                cur_indent = len(line) - len(line.lstrip(" "))
                if cur_indent <= indent:
                    break
                if block_indent is None:
                    block_indent = cur_indent
                collected.append(line[block_indent:])
                index += 1
            while collected and not collected[-1].strip():
                collected.pop()
            if folded:
                value = " ".join(part.strip() for part in collected if part.strip())
            else:
                value = "\n".join(collected)
            tokens.append((indent, "kv", f"{key}: {json.dumps(value)}"))
            continue
        if content.startswith("- "):
            tokens.append((indent, "item", _normalise_numeric_keys(content[2:].strip())))
        elif content == "-":
            tokens.append((indent, "item", ""))
        else:
            tokens.append((indent, "kv", content))
        index += 1
    return tokens


def _build(tokens: list[tuple[int, str, str]], pos: int, indent: int) -> tuple[Any, int]:
    """Recursive descent over the token list."""
    if pos >= len(tokens):
        return None, pos
    kind = tokens[pos][1]
    if kind == "item":
        result_list: list[Any] = []
        while pos < len(tokens) and tokens[pos][0] == indent and tokens[pos][1] == "item":
            content = tokens[pos][2]
            pos += 1
            if not content:
                child, pos = _build(tokens, pos, _next_indent(tokens, pos, indent))
                result_list.append(child)
            elif ":" in content and not content.startswith(("[", "{", "\"", "'")):
                key, _, value = content.partition(":")
                key = _coerce_key(key.strip().strip("\"'"))
                item_map: dict[str, Any] = {}
                if value.strip():
                    item_map[key] = _parse_scalar(value)
                    pos_after = pos
                else:
                    child_indent = _next_indent(tokens, pos, indent)
                    child, pos = _build(tokens, pos, child_indent)
                    item_map[key] = child
                    pos_after = pos
                # sibling keys of the same inline map are indented deeper than the dash
                while pos_after < len(tokens) and tokens[pos_after][1] == "kv" and tokens[pos_after][0] > indent:
                    sub_indent = tokens[pos_after][0]
                    child_map, pos_after = _build(tokens, pos_after, sub_indent)
                    if isinstance(child_map, dict):
                        item_map.update(child_map)
                    else:  # pragma: no cover - defensive
                        break
                pos = pos_after
                result_list.append(item_map)
            else:
                result_list.append(_parse_scalar(content))
        return result_list, pos
    # mapping
    result_map: dict[str, Any] = {}
    while pos < len(tokens) and tokens[pos][0] == indent and tokens[pos][1] == "kv":
        content = tokens[pos][2]
        key, _, value = content.partition(":")
        key = _coerce_key(key.strip().strip("\"'"))
        pos += 1
        if value.strip():
            result_map[key] = _parse_scalar(value)
            continue
        child_indent = _next_indent(tokens, pos, indent)
        if child_indent is None or pos >= len(tokens):
            result_map[key] = None
            continue
        child, pos = _build(tokens, pos, child_indent)
        result_map[key] = child
    return result_map, pos


def _next_indent(tokens: list[tuple[int, str, str]], pos: int, parent_indent: int) -> Optional[int]:
    if pos < len(tokens) and tokens[pos][0] > parent_indent:
        return tokens[pos][0]
    return None


def parse_simple_yaml(text: str) -> dict[str, Any]:
    tokens = _tokenize(text)
    if not tokens:
        return {}
    value, pos = _build(tokens, 0, tokens[0][0])
    if pos != len(tokens):  # pragma: no cover - defensive
        raise ConfigError(f"could not parse configuration from token {pos}: {tokens[pos]}")
    if not isinstance(value, dict):
        raise ConfigError("top level of the configuration must be a mapping")
    return value


def load_yaml(path: str | os.PathLike[str]) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ConfigError("top level of the configuration must be a mapping")
        return data
    except ImportError:
        return parse_simple_yaml(text)


# ==========================================================================
# typed access
# ==========================================================================

class ConfigSection:
    """Read-only dotted access over a configuration subtree."""

    def __init__(self, data: Any, path: str = "") -> None:
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ConfigError(f"configuration section {path or '<root>'} must be a mapping, got {type(data).__name__}")
        self._data: dict[str, Any] = data
        self._path = path

    def section(self, key: str) -> "ConfigSection":
        value = self.get(key)
        if value is None:
            return ConfigSection({}, f"{self._path}.{key}")
        if isinstance(value, ConfigSection):
            return value
        return ConfigSection(value, f"{self._path}.{key}")

    def get(self, key: str, default: Any = None) -> Any:
        node: Any = self._data
        for part in key.split("."):
            if isinstance(node, ConfigSection):
                node = node._data
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def require(self, key: str) -> Any:
        value = self.get(key)
        if value is None:
            raise ConfigError(f"missing required configuration key: {self._path}.{key}")
        return value

    def as_dict(self) -> dict[str, Any]:
        return dict(self._data)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"ConfigSection({self._path or '<root>'}, keys={sorted(self._data)})"


class ProtocolConfig:
    """The versioned Paper 3 protocol configuration."""

    def __init__(self, data: dict[str, Any], path: Optional[str] = None) -> None:
        self._root = ConfigSection(data, "")
        self.path = path
        self._validate()

    # -- construction ------------------------------------------------------
    @classmethod
    def load(cls, path: Optional[str | os.PathLike[str]] = None) -> "ProtocolConfig":
        target = Path(path) if path else DEFAULT_CONFIG_PATH
        if not target.exists():
            raise ConfigError(f"protocol configuration not found: {target}")
        return cls(load_yaml(target), str(target))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProtocolConfig":
        return cls(data, "<dict>")

    # -- access ------------------------------------------------------------
    @property
    def root(self) -> ConfigSection:
        return self._root

    def get(self, key: str, default: Any = None) -> Any:
        return self._root.get(key, default)

    def require(self, key: str) -> Any:
        return self._root.require(key)

    def section(self, key: str) -> ConfigSection:
        return self._root.section(key)

    @property
    def protocol_name(self) -> str:
        return str(self.get("meta.protocol_name", PROTOCOL_NAME))

    @property
    def protocol_version(self) -> str:
        return str(self.get("meta.protocol_version", "0.0.0"))

    @property
    def schema_version(self) -> str:
        return str(self.get("meta.schema_version", "0.0.0"))

    @property
    def state_generator_version(self) -> str:
        return str(self.get("state_generator.version", "0.0.0"))

    @property
    def note_template_version(self) -> str:
        return str(self.get("note.template_version", "0.0.0"))

    @property
    def llm_template_version(self) -> str:
        return str(self.get("llm.template_version", "0.0.0"))

    def scales(self) -> dict[str, Any]:
        return dict(self.get("scales.items", {}))

    def scale_anchors(self, item: str) -> dict[int, str]:
        anchors = self.get(f"scales.items.{item}.anchors", {})
        return {int(k): str(v) for k, v in dict(anchors).items()}

    def to_dict(self) -> dict[str, Any]:
        return self._root.as_dict()

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)

    def hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()[:16]

    # -- validation --------------------------------------------------------
    def _validate(self) -> None:
        missing = [key for key in REQUIRED_KEYS if self.get(key) is None]
        if missing:
            raise ConfigError(
                "protocol configuration is missing required keys: " + ", ".join(missing)
            )
        opportunities = int(self.get("sampling.opportunities_per_day"))
        minimum_background = int(self.get("sampling.min_background"))
        maximum_event = int(self.get("sampling.max_event_enriched"))
        if minimum_background + maximum_event < opportunities:
            raise ConfigError(
                "min_background + max_event_enriched must cover opportunities_per_day "
                f"({minimum_background} + {maximum_event} < {opportunities})"
            )
        if bool(self.get("sampling.force_event_diversity", False)):
            raise ConfigError(
                "sampling.force_event_diversity must be false: Paper 3 never fabricates "
                "event categories to satisfy diversity"
            )
        if bool(self.get("missingness.force_one_miss_per_day", False)):
            raise ConfigError("missingness.force_one_miss_per_day must be false (historical behaviour rejected)")
        if bool(self.get("llm.allowed_to_select_subjective_values", False)):
            raise ConfigError(
                "llm.allowed_to_select_subjective_values must be false unless a documented "
                "justification and comparative evidence exist (see docs/ARCHITECTURE.md §7)"
            )
        if str(self.get("latency.context_reference_time")) != "prompt_time":
            raise ConfigError("latency.context_reference_time must be 'prompt_time'")
        points = int(self.get("scales.points"))
        for item in ("valence", "energy", "stress"):
            anchors = self.scale_anchors(item)
            if sorted(anchors) != list(range(1, points + 1)):
                raise ConfigError(f"scales.items.{item}.anchors must define exactly 1..{points}")
        expiry = float(self.get("latency.expiry_minutes"))
        if expiry <= 0:
            raise ConfigError("latency.expiry_minutes must be positive")
        base = self.get("missingness.base_response_probability")
        if not isinstance(base, dict) or not base:
            raise ConfigError("missingness.base_response_probability must map triggers to probabilities")
        for trigger, probability in base.items():
            if not 0.0 <= float(probability) <= 1.0:
                raise ConfigError(f"missingness.base_response_probability.{trigger} out of [0,1]")
        target = self.get("missingness.calibration_target_response_rate")
        if not isinstance(target, (list, tuple)) or len(target) != 2:
            raise ConfigError("missingness.calibration_target_response_rate must be [low, high]")


# ==========================================================================
# convenience
# ==========================================================================

_DEFAULT_CONFIG: Optional[ProtocolConfig] = None


def default_config(reload: bool = False) -> ProtocolConfig:
    """Return the shipped ``paper3_ema_v1`` configuration (cached)."""
    global _DEFAULT_CONFIG
    if _DEFAULT_CONFIG is None or reload:
        _DEFAULT_CONFIG = ProtocolConfig.load()
    return _DEFAULT_CONFIG


def config_hash(config: Optional[ProtocolConfig] = None) -> str:
    return (config or default_config()).hash()


def missing_required_keys(data: dict[str, Any]) -> list[str]:
    config = ProtocolConfig.__new__(ProtocolConfig)
    config._root = ConfigSection(data, "")
    return [key for key in REQUIRED_KEYS if config.get(key) is None]


def as_dict(config: ProtocolConfig) -> dict[str, Any]:
    return config.to_dict()


def iter_keys(config: ProtocolConfig, prefix: str = "") -> Iterable[str]:
    """Yield dotted key paths (used by tests and the assumptions register)."""
    for key, value in config.to_dict().items():
        path = f"{prefix}.{key}" if prefix else key
        yield path
        if isinstance(value, dict):
            yield from iter_keys(ConfigSection(value, path), path)
