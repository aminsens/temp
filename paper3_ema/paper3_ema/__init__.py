"""paper3_ema — standalone Paper 3 EMA module.

A clean, standalone, scientifically defensible EMA (ecological momentary
assessment) module that turns an externally supplied **contextual day** into a
complete, provenance-traced EMA bundle.

Architecture::

    any contextual-day generator  ->  EMARequest  ->  paper3_ema  ->  EMABundle

This package has **zero** dependencies on DayForge, Appa or any specific host
system (only stdlib; PyYAML is optional).  It is an *annotation layer*:
inherited contextual facts are copied verbatim and never altered; the synthetic
content is (a) the protocol (schedule, missingness, latency, expiry) and
(b) the bounded subjective state plus optional context note.

Public API
----------
``audit_schedule(day, prompt_times, config)``      read-only schedule auditor
``schedule_prompts(request, config, seed)``        schedule the five opportunities
``generate_responses(request, prompts, config)``   simulate response/latency/state/note
``generate_ema(request, seed, config, ...)``       one full :class:`EMABundle`
``generate_ema_multi_day(requests, seed, ...)``    one bundle per day
``validate_bundle(bundle, config, day)``           bundle contract validation
"""

from __future__ import annotations

from .audit import (
    AUDITOR_VERSION,
    ScheduleAuditIssue,
    ScheduleAuditResult,
    audit_bundle_prompts,
    audit_schedule,
    summarise_audit,
)
from .config import (
    ConfigError,
    DEFAULT_CONFIG_PATH,
    PROTOCOL_NAME,
    ProtocolConfig,
    default_config,
    load_yaml,
)
from .context import build_packet
from .day import (
    ContextualDay,
    DayImportError,
    contextual_day_from_mapping,
    describe_day,
    validate_day_input,
)
from .models import (
    DayEvent,
    EMAContextPacket,
    EMABundle,
    EMAProvenance,
    EMARequest,
    EMAResponse,
    EMARecord,
    EMAPrompt,
    EMAValidationIssue,
    EMAValidationResult,
    FixedCommitmentRef,
    PersonaContextFacts,
    SubjectiveState,
)
from .pipeline import (
    PIPELINE_VERSION,
    InheritedContextMutationError,
    as_request,
    build_context,
    generate_bundle,
    generate_ema,
    generate_ema_multi_day,
    generate_responses,
)
from .provenance import FIELD_PROVENANCE, build_provenance, versions
from .scheduler import SCHEDULER_VERSION, schedule_for_day, schedule_prompts, stable_seed
from .validate import VALIDATOR_VERSION, summarise_validation, validate_bundle

__version__ = "1.0.0"

__all__ = [
    # versions
    "__version__",
    "PIPELINE_VERSION",
    "SCHEDULER_VERSION",
    "AUDITOR_VERSION",
    "VALIDATOR_VERSION",
    "PROTOCOL_NAME",
    # config
    "ConfigError",
    "ProtocolConfig",
    "default_config",
    "load_yaml",
    "DEFAULT_CONFIG_PATH",
    # input models
    "ContextualDay",
    "DayImportError",
    "EMARequest",
    "EMAContextPacket",
    "PersonaContextFacts",
    "contextual_day_from_mapping",
    "describe_day",
    "validate_day_input",
    "as_request",
    # scheduling
    "schedule_prompts",
    "schedule_for_day" ,
    "stable_seed",
    "DayEvent",
    # audit
    "audit_schedule",
    "audit_bundle_prompts",
    "ScheduleAuditResult",
    "ScheduleAuditIssue",
    "summarise_audit",
    # generation
    "generate_ema",
    "generate_ema_multi_day",
    "generate_bundle",
    "generate_responses",
    "build_context",
    "InheritedContextMutationError",
    # outputs
    "EMABundle",
    "EMAPrompt",
    "EMAResponse",
    "EMARecord",
    "EMAProvenance",
    "SubjectiveState",
    # validation
    "validate_bundle",
    "EMAValidationResult",
    "EMAValidationIssue",
    "summarise_validation",
    # provenance
    "FIELD_PROVENANCE",
    "build_provenance",
    "versions",
]
