"""Configuration tests: parser fidelity, required keys, hard policy guards."""

from __future__ import annotations

import copy

import pytest

from paper3_ema import config as cfgmod
from paper3_ema.config import (
    ConfigError,
    DEFAULT_CONFIG_PATH,
    ProtocolConfig,
    default_config,
    missing_required_keys,
)


def test_parser_matches_pyyaml():
    text = DEFAULT_CONFIG_PATH.read_text(encoding="utf-8")
    mine = cfgmod.parse_simple_yaml(text)
    try:
        import yaml
    except ImportError:  # pragma: no cover
        pytest.skip("PyYAML not installed")
    theirs = yaml.safe_load(text)
    assert mine == theirs


def test_shipped_config_loads_and_has_stable_hash():
    config = default_config()
    assert config.protocol_name == "paper3_ema_v1"
    assert config.protocol_version == "1.0.0"
    assert len(config.hash()) == 16
    assert default_config().hash() == config.hash()


def test_required_keys_are_present():
    assert missing_required_keys(default_config().to_dict()) == []


def test_missing_key_is_rejected():
    data = copy.deepcopy(default_config().to_dict())
    del data["latency"]["expiry_minutes"]
    with pytest.raises(ConfigError, match="missing required keys"):
        ProtocolConfig.from_dict(data)


def test_policy_guards():
    data = copy.deepcopy(default_config().to_dict())
    data["sampling"]["force_event_diversity"] = True
    with pytest.raises(ConfigError, match="force_event_diversity"):
        ProtocolConfig.from_dict(data)

    data = copy.deepcopy(default_config().to_dict())
    data["missingness"]["force_one_miss_per_day"] = True
    with pytest.raises(ConfigError, match="force_one_miss_per_day"):
        ProtocolConfig.from_dict(data)

    data = copy.deepcopy(default_config().to_dict())
    data["llm"]["allowed_to_select_subjective_values"] = True
    with pytest.raises(ConfigError, match="allowed_to_select_subjective_values"):
        ProtocolConfig.from_dict(data)

    data = copy.deepcopy(default_config().to_dict())
    data["latency"]["context_reference_time"] = "response_time"
    with pytest.raises(ConfigError, match="prompt_time"):
        ProtocolConfig.from_dict(data)


def test_scale_anchors_are_exactly_1_to_5():
    config = default_config()
    for item in ("valence", "energy", "stress"):
        anchors = config.scale_anchors(item)
        assert sorted(anchors) == [1, 2, 3, 4, 5]


def test_scale_labels_match_documented_semantics():
    config = default_config()
    assert config.scale_anchors("valence")[3] == "neutral"
    assert config.scale_anchors("stress")[1] == "none/very low"
    assert config.scale_anchors("energy")[5] == "very high"
