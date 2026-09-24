# Synthetic EMA Diary Generation Pipeline

A DSPy-based pipeline for generating synthetic Ecological Momentary Assessment (EMA) 
diaries that are temporally coherent, contextually rich, and rooted in memory-consistent 
episodic recall.

## Why This Exists

The EMA literature has documented a decade of gaps:
- Domain/purpose variables are undercollected
- Temporal alignment between EMA and accelerometer data is chaotic
- Missing data patterns are never modeled with ground truth
- Event-triggered EMA is rarely implemented
- No shareable multimodal EMA+accelerometer datasets exist

This pipeline generates synthetic EMA diaries that solve all of these problems by 
construction.

## Architecture

```
PersonaGen → RoutineGen → DailyDiaryGen → EMAProbeGen → CoherenceAudit
    DSPy        DSPy          DSPy            DSPy           DSPy
    CoT         CoT           CoT+Memory      CoT+Recall     Pred+Refine
```

## Key Design Principles (from EMA literature synthesis)

1. **Domain is first-class** - Every episode has work/leisure/transport/household
2. **Purpose is explicit** - Why the person is moving, not just what
3. **Memory roots** - Each day references previous days for consistency
4. **Social context** - Who the person is with, always
5. **Device compliance** - Wear/non-wear patterns simulated
6. **Prompt-response lag** - Configurable latency between prompt and response
7. **Demarcation truth** - Sub-activity breakdown within episodes

## DSPy Optimizers

- **GEPA**: Prompt optimization via reflection on coherence failures
- **GRPO**: Reinforcement learning on temporal/spatial/logical consistency scores
- **CoT**: Chain-of-thought reasoning at every generation step
- **Pred**: Final structured prediction with constrained output schemas
