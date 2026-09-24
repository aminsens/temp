"""Real DeepSeek integration tests (auto-skip when no credential / no route).

These tests activate automatically when ``DEEPSEEK_API_KEY`` is set AND
``api.deepseek.com`` is reachable from the sandbox.  Otherwise they report an
explicit SKIP reason.  A fully offline equivalent of the transport path
(credential handling, HTTP call, JSON extraction, retry, null fallback) is
exercised in :mod:`tests.test_llm_transport_offline` against a local HTTP
server, so the client is covered either way.
"""

from __future__ import annotations

import pytest

from paper3_ema.config import default_config
from paper3_ema.fixtures import build_fixture
from paper3_ema.llm import DeepSeekClient, llm_available
from paper3_ema.notes import validate_note
from paper3_ema.pipeline import generate_ema

_available, _reason = llm_available()


def _skip_or_run():
    if not _available:
        pytest.skip(f"DeepSeek integration skipped: {_reason}")


def test_real_llm_end_to_end_bundle():
    _skip_or_run()
    day = build_fixture("public_transport_commuter_day")
    bundle = generate_ema(day, seed=7, llm_client=DeepSeekClient.from_config())
    assert bundle.validation.valid, [i.message for i in bundle.validation.issues]
    prov = bundle.provenance
    assert prov.llm_provider == "deepseek"
    assert prov.llm_model
    assert prov.llm_calls >= 1
    # every rendered note must satisfy the closed-world contract
    for record in bundle.records:
        note = record.response.context_note
        if note is not None:
            validation = validate_note(note, record.packet, default_config())
            assert validation.valid, f"{note!r} -> {validation.codes}"
            assert record.response.note_source == "llm"
    # decoding settings are recorded
    assert prov.llm_decoding.get("temperature") is not None


def test_real_llm_retries_are_bounded():
    _skip_or_run()
    day = build_fixture("normal_office_day")
    bundle = generate_ema(day, seed=7, llm_client=DeepSeekClient.from_config())
    max_retries = int(default_config().get("note.max_retries", 2))
    for record in bundle.records:
        trace = bundle.provenance.record_provenance[record.prompt_id]
        assert trace["retry_count"] <= max_retries
    assert bundle.provenance.llm_retries <= max_retries * len(bundle.records)


def test_real_llm_never_alters_inherited_context():
    _skip_or_run()
    day = build_fixture("normal_office_day")
    bundle = generate_ema(day, seed=7, llm_client=DeepSeekClient.from_config())
    # inherited facts in every record must still match the day verbatim
    from paper3_ema.validate import validate_bundle

    result = validate_bundle(bundle, default_config(), day=day)
    assert not any(i.code == "inherited_context_altered" for i in result.issues)


def test_real_llm_subjective_values_are_not_model_chosen():
    """The LLM renders notes only; valence/energy/stress come from the generator."""
    _skip_or_run()
    day = build_fixture("normal_office_day")
    bundle = generate_ema(day, seed=7, llm_client=DeepSeekClient.from_config())
    from paper3_ema.pipeline import generate_ema as ge

    reference = ge(day, seed=7, llm_client=None)
    for with_llm, without in zip(bundle.records, reference.records):
        if with_llm.response.subjective and without.response.subjective:
            assert with_llm.response.subjective.items() == without.response.subjective.items(), (
                "subjective values differ with/without the LLM: the LLM must not select them"
            )
