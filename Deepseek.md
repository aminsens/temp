# Executive Summary

In the narrow intersection of body‑mounted accelerometry and physical activity/sedentary behaviour research, EMA serves a distinct and irreplaceable role. It does **not** provide ground truth, nor does it directly validate accelerometer‑derived intensity or duration. Instead, its core utility is **contextual annotation**—providing the *where, why, with whom, and what type* of behaviour that raw acceleration signals cannot supply. EMA is used primarily to **disambiguate** accelerometer‑derived bouts, to collect **behavioural domain** (work, leisure, transport, household), **purpose of movement**, **social and environmental context**, and **subjective states** (affect, fatigue, pain) that modify the interpretation of movement data.

The literature shows strong empirical support for EMA’s ability to differentiate **occupational sitting from leisure sitting**, to distinguish **exercise from transport walking**, to identify **intentional versus incidental activity**, and to **label specific activity types** (e.g., sitting, walking, running) for classification algorithm training. However, the field consistently underuses EMA: it is often collected but not integrated into modelling, compliance reporting is poor, temporal alignment is often crude, and EMA’s potential to resolve the most fundamental ambiguity in accelerometer data—*why a person is moving or not moving*—is frequently left untapped.

A well‑designed EMA component should be **minimal, targeted, and temporally well‑aligned**, with a clear modelling or interpretive purpose defined before data collection. The literature’s strongest examples use **event‑triggered (accelerometer‑informed) EMA**, which drastically reduces participant burden while maximising the contextual relevance of each self‑report. The field’s weakest points remain: failure to report missing EMA data, ignoring prompt‑response lag, collecting dozens of EMA items without a clear analytical plan, and treating EMA as a validation source rather than as a complementary data layer that adds *meaning* to accelerometer signals.

---

## Scope Definition and Inclusion Logic

This synthesis includes **only** studies that meet all three criteria:

1. **Primary movement data come from a body‑mounted accelerometer** (ActiGraph, activPAL, Axivity, GENEActiv, Move, Fitbit—with the latter only when used as a dedicated activity monitor rather than as a general‑purpose wearable). Smartphone accelerometers are excluded unless explicitly serving only as a passive complement to a body‑worn device, which the literature rarely does.
2. **The study focuses on physical activity, sedentary behaviour, posture, or free‑living movement behaviour**, and not primarily on physiological monitoring (HR, ECG, PPG, EEG, EMG, respiration, sleep as a main outcome).
3. **EMA or a functionally equivalent momentary self‑report component is used** alongside the accelerometer, with the EMA data intended for contextualisation, labelling, validation, or behaviour interpretation.

The literature that genuinely fits this scope is **smaller than one might expect**. A systematic review of EMA studies on sedentary behaviour found that only 19% of EMA studies used an objective measure (accelerometer) alongside self‑report. A broader systematic review of EMA in physical activity research found that 71% of studies used EMA terminology, but only half used mHealth technology, and while accelerometers were the main built‑in sensor in 69% of those, many studies relied on phone accelerometers rather than body‑worn dedicated devices. The genuinely narrow‑scope literature—body‑mounted accelerometer + EMA for physical activity/sedentary behaviour—is modest in volume but methodologically rich.

---

## What EMA Contributes Beyond Body‑Mounted Accelerometers

Body‑mounted accelerometers provide **excellent** measurement of movement intensity, duration, frequency, and postural transitions (sit‑to‑stand). However, they are **silent on meaning**. A 20‑minute sedentary bout could be work‑related desk sitting, leisure‑time television viewing, or waiting in a car. A walking episode could be exercise, commuting, household errands, or incidental movement. EMA supplies the missing layers.

### Strongly Supported by the Literature

| Contribution | Evidence Quality |
|--------------|------------------|
| Distinguishing occupational sitting from leisure sitting | Strong (Giurgiu et al., 2020) |
| Distinguishing exercise from transport walking | Moderate (Strohacker et al., 2022) |
| Identifying social and environmental context (location, company) | Strong (Giurgiu et al., 2020; Maher et al., 2021) |
| Providing labels for activity classification (sitting, walking, running) | Strong (Sigcha et al., 2025 preprint) |
| Collecting momentary affect, fatigue, pain as behavioural modifiers | Moderate to Strong (Maes et al., 2023; scoping review) |

### Weakly or Inconsistently Supported

- **Explaining why movement occurred** (intent, motivation)—some studies attempt this via EMA items on intention, self‑efficacy, and barriers, but temporal causal inference remains challenging.
- **Identifying intentional versus incidental activity**—rarely measured directly; often inferred from activity type and context.
- **Real‑time detection of behavioural episodes for just‑in‑time intervention**—this is technologically possible (triggered EMA) but remains largely in the development/feasibility stage.

### What EMA Adds That Accelerometry Cannot Provide

1. **Behavioural domain**: Work, leisure, transport, household, self‑care.
2. **Purpose of movement**: Exercise, commuting, occupational, recreational.
3. **Social context**: Alone, with family, with friends, with colleagues, with strangers.
4. **Physical environment**: Indoor/outdoor, specific location types (home, office, gym, park).
5. **Affective state**: Mood, stress, enjoyment, fatigue—critical for understanding behaviour maintenance and adherence.
6. **Cognitive/psychological variables**: Intention, self‑efficacy, barriers, motivation.
7. **Compliance signals**: Self‑reported device removal, non‑wear periods, technical issues.

---

## How EMA Is Used in Physical Activity and Sedentary Behaviour Studies

### Common Practice in the Literature

The most frequent EMA design in this field uses **time‑based (signal‑contingent) prompts** delivered via smartphone apps, typically **3–7 prompts per day** for **7–14 days**. A systematic review found that most studies lasted 1–7 days (57.9%), with 3–7 assessments per day (37%).

| Design Element | Typical Practice | Variability |
|----------------|------------------|--------------|
| Prompt frequency | 4–7 per day | 2–10 per day |
| Prompt schedule | Fixed intervals (e.g., every 2–3 hours) | Random intervals within blocks |
| Monitoring period | 7–14 days | 3–30 days |
| Delivery method | Smartphone app (mEMA) | Paper diary (rare after 2015) |
| EMA items per prompt | 5–15 items | 2–30 items |
| Prompt‑response window | Immediate upon notification | Up to 15 minutes |

### What Is Collected

| EMA Variable | Common? | Useful? | Burdensome? | Notes |
|--------------|---------|---------|-------------|-------|
| Current activity type (e.g., sitting, walking, running) | **Very common** | High | Low | Core variable |
| Location (home, work, other indoor, outdoor) | **Common** | High | Low | Essential for context |
| Social context (alone, with whom) | **Common** | High | Low | Key for SB interpretation |
| Domain (work, leisure, transport) | **Moderate** | Very high | Low | Most valuable for PA/SB |
| Affect/mood (PANAS, SAM) | **Moderate** | High | Low to moderate | Well‑validated |
| Fatigue | **Moderate** | High | Low | Especially in older adults |
| Perceived exertion | Rare | Moderate | Low | Often overlaps with accelerometry |
| Pain | Rare | High (clinical populations) | Low | Condition‑specific |
| Compliance (worn? device on?) | Rare | Very high | Minimal | Shockingly undercollected |
| Intention/self‑efficacy | Rare | Moderate | Low | Temporal ambiguity |
| Diet/eating behaviour | Rare | N/A | Moderate | Outside core scope |

### Rarity Patterns

**What is rare but should be common**:
- Compliance indicators (“Did you wear the accelerometer all day?”)
- Device removal events (“Did you take the device off at any point?”)
- Technical issue reports (“Did the device/app malfunction?”)

**What is rare and likely rightly so**:
- Open‑ended text responses (high burden, hard to analyse at scale)
- Very long item batteries (>20 items per prompt—causes prompt fatigue and drop‑out)
- Highly granular activity type lists (e.g., distinguishing 15 types of walking—exceeds recall accuracy)

---

## Role of EMA in Labelling, Validation, and Algorithm Development

### EMA as a Label Source for Activity Classification

This is arguably the **most methodologically exciting** use of EMA in the field. EMA can provide **sparse but ecologically valid labels** for free‑living accelerometer data, enabling machine learning models to be trained on real‑world behaviour rather than on laboratory‑scripted activities that fail to generalise.

A recent preprint from the WEALTH study (Sigcha et al., 2025) presents a framework integrating thigh‑worn accelerometer data with event‑based EMA surveys to label six physical activity categories in free‑living settings across 589 participants over seven days. EMA responses were synchronised with accelerometer signals to create a sparse labelled dataset, achieving **up to 97% agreement** with ground‑truth labels from the proprietary activPAL CREA algorithm. A machine learning model trained on this dataset achieved classification accuracies of up to **73.6%** .

This demonstrates that EMA can function as a **practical, scalable source of real‑world labels** for activity recognition—an advance over laboratory‑based training data that rarely captures the variability of free‑living movement.

### EMA as Weak vs. Strong Label Source

| Label Type | Description | Evidence in Literature |
|-------------|-------------|------------------------|
| **Direct label** (strong) | EMA response “I am currently walking” → label accelerometer segment as walking | High agreement (97% in WEALTH) |
| **Weak label** (noisy) | EMA response “I walked for exercise in the past 30 minutes” → label retrospectively | Lower agreement (25% alignment in Strohacker et al., 2022) |
| **Contextual feature** | EMA provides location, social context, domain → used as auxiliary input to model, not as label | Common in multilevel modelling studies |
| **Validation source** | EMA labels used to check accelerometer‑derived classification accuracy | Mixed results |

### How Useful Is EMA for Algorithm Development?

| Modelling Task | EMA Utility | Evidence |
|----------------|-------------|----------|
| Binary activity detection (active vs. sedentary) | Moderate—accelerometry alone is good at this | N/A |
| Activity type classification (sitting, standing, walking, running) | **High**—provides sparse but ecologically valid labels | WEALTH framework |
| Behavioural domain detection (work vs. leisure) | **Very high**—accelerometry cannot do this at all | Giurgiu et al., 2020 |
| Affect/PA association modelling | **High**—accelerometry cannot measure affect | Scoping review |
| Context‑aware behaviour analysis | **Very high**—core value proposition | Maher et al., 2021 |
| Personalised activity recommendations | **Moderate**—EMA provides user‑specific context for tailoring | Limited evidence |

### Does the Literature Meaningfully Integrate EMA into Modelling?

**Partial integration at best.** Many studies collect EMA data but use it only for **descriptive characterisation** (e.g., “40% of sedentary bouts occurred at work”) rather than integrating it into predictive models or using it to improve accelerometer‑based inference. A common pattern: EMA is collected, summarised in Table 2, and then **never appears in the modelling section**. This is a significant missed opportunity.

However, the WEALTH studyand the sedentary‑triggered EMA work by Giurgiu et al.represent genuine integration, where EMA is not an afterthought but a **design driver** for the entire data collection and modelling pipeline.

---

## Common EMA Variables Collected in This Literature

### By Frequency (from most to least common)

1. **Current activity** (“What are you doing right now?”)—categorical, often with 5–15 options.
2. **Location** (“Where are you?”)—home, work, other indoor, outdoor.
3. **Social context** (“Who are you with?”)—alone, family, friends, colleagues, strangers.
4. **Affect/mood**—typically Likert scales for valence and arousal.
5. **Domain** (“Is this work, leisure, transport, or household?”)—often embedded within activity options.
6. **Fatigue**—single item or multi‑item.
7. **Pain** (in clinical or older adult populations).
8. **Perceived exertion** (rare).
9. **Intent/self‑efficacy** (rare).
10. **Compliance** (very rare).

### Which Are Most Useful?

| Variable | Utility Justification |
|----------|------------------------|
| **Domain (work/leisure/transport/household)** | Resolves the single largest ambiguity in accelerometer data: *why* movement occurs. A walking bout that is transport has different health and policy implications than one that is exercise. |
| **Social context (alone/with others)** | Critically important for sedentary behaviour interpretation—prolonged sedentary bouts occur 57% of the time with others, which has implications for intervention design. |
| **Location (home/work/other)** | Enables separation of occupational from leisure sitting—a distinction that accelerometry alone cannot make. |
| **Current activity type (sitting/walking/running/standing)** | Provides direct labels for classification algorithms. |

### Which Are Burdensome with Limited Value?

| Variable | Burden | Value | Verdict |
|----------|--------|-------|---------|
| Very fine‑grained activity lists (15+ categories) | High (cognitive load) | Low (recall accuracy degrades) | Avoid |
| Open‑ended text responses | Very high | Low (hard to analyse at scale) | Avoid unless qualitative focus |
| Multi‑item psychological scales (e.g., full PANAS) | Moderate | Moderate (well‑validated but may exceed tolerable length) | Use short forms (e.g., 2‑item affect) |
| Perceived exertion | Low | Low (accelerometer already measures intensity) | Not recommended for general use |

### Scientifically Attractive but Operationally Weak

- **Intention/motivation measures at the moment of behaviour**: Theoretically appealing (e.g., intention‑behaviour gap), but temporal alignment is problematic—EMA asks about *current* intention, but the behaviour of interest may have already occurred or is about to occur. Causal inference is difficult without very precise timing.
- **Barriers to activity**: Similarly attractive, but barriers are often stable across the day, making momentary assessment redundant relative to a single baseline measure.
- **Very high‑frequency EMA (e.g., hourly)** : Provides dense data but causes prompt fatigue, reduced compliance, and potential reactivity (participants change behaviour because they know they will be asked about it).

---

## Methodological Challenges in Linking EMA to Accelerometer Data

### Core Challenges

| Challenge | Description | Frequency in Literature |
|-----------|-------------|-------------------------|
| **Timestamp misalignment** | Clock drift between accelerometer and smartphone; response delay between prompt and actual entry | Very common, rarely addressed |
| **Recall window mismatch** | EMA asks “current activity” but the relevant behaviour may have occurred minutes before | Common |
| **Event duration mismatch** | EMA captures a point in time; behaviours have duration (e.g., 30‑minute walk) | Universal |
| **Sparse vs. dense data** | EMA provides a few labels per day; accelerometer provides millions of samples per day | Universal |
| **Missing EMA responses** | Participants ignore prompts; non‑random missingness (e.g., more likely when active) | Common, poorly handled |
| **Self‑report bias** | Social desirability; recall inaccuracies even with momentary prompts | Inherent to EMA |
| **Prompt reactivity** | Participants change behaviour because they anticipate being asked about it | Understudied in this field |

### Alignment Strategies Used in the Literature

| Strategy | Description | Evidence |
|----------|-------------|----------|
| **Fixed‑window alignment** | Extract accelerometer data from a fixed window around the EMA timestamp (e.g., ±15 minutes) | Most common (e.g., 15‑minute window in SB studies) |
| **Pre‑prompt window** | Extract data from a defined period *before* the EMA prompt (e.g., 15, 30, 60, 120 minutes prior) | Used in Maes et al., 2023 |
| **Post‑prompt window** | Extract data from period *after* EMA prompt (for predicting future behaviour) | Less common |
| **Event‑triggered alignment** | Accelerometer detects a behaviour (e.g., 20 minutes of sitting) and triggers an EMA prompt at that moment | Most accurate; used in Giurgiu et al., 2020 |
| **Point‑based labeling** | Assign a short IMU segment around the exact EMA timestamp (e.g., ±30 seconds) | For acute states |
| **Retrospective labeling** | Label a window that occurs before the EMA entry (e.g., 5–10 minutes leading up) | For gradually developing states |

### Strongest Approaches

1. **Event‑triggered EMA**: The accelerometer detects a specific behavioural state (e.g., 20 minutes of sitting) and triggers a prompt *during* that behaviour. This eliminates recall error and ensures temporal alignment. Giurgiu et al. demonstrated this with a thigh‑worn Move accelerometer and a smartphone app, achieving 82.77% accuracy in capturing prolonged sedentary bouts.

2. **Dual‑timestamp recording**: Record both the **prompt delivery timestamp** and the **response submission timestamp**. The prompt timestamp is more accurate for aligning with the behaviour that triggered the prompt; the response timestamp includes participant delay. Very few studies do this systematically.

3. **Pre‑defined, justified windows**: Studies that explicitly state their alignment rule (e.g., “accelerometer data from 15 minutes before to 5 minutes after the EMA timestamp”) and justify it based on the behaviour under study. The 15‑minute window is the most commonly standardised in SB research.

### Weak Approaches

- **Ignoring the problem entirely**: Many studies do not report any alignment method, implicitly assuming that EMA timestamps perfectly correspond to the behaviour of interest.
- **Using EMA as a “truth” validator without accounting for timing mismatches**: Comparing an EMA report of “sitting” to a 30‑minute accelerometer segment that includes standing transitions is methodologically unsound.
- **No handling of missing EMA data**: Listwise deletion or ignoring missing prompts is common; multiple imputation or missingness modelling is rare.

---

## Common Weaknesses and Blind Spots

### What the Literature Usually Does Not Do

| Omission | Consequence | Severity |
|----------|-------------|----------|
| **Report EMA compliance rates** | Cannot assess data quality or generalisability | High |
| **Handle missing EMA data appropriately** | Biased estimates, reduced power | High |
| **Use temporal alignment methods** | Mis‑labelling of behaviour; model learns wrong patterns | Very high |
| **Integrate EMA into modelling** | EMA collected but not used; wasted participant burden | High |
| **Collect compliance EMA items** | Cannot distinguish non‑wear from sedentary behaviour | Moderate |
| **Use triggered (accelerometer‑informed) EMA** | Missed opportunity to reduce burden and improve accuracy | Moderate |
| **Report prompt‑response lag** | Cannot assess delay effects | Moderate |
| **Validate EMA items against accelerometer data** | Unclear what EMA actually measures | Moderate |
| **Consider prompt reactivity** | Potential bias in behaviour measurement | Low (but important) |

### Critical Blind Spots

1. **EMA collected but not used**: This is perhaps the most damning pattern. Studies invest substantial participant burden in collecting EMA data, then relegate it to a descriptive table and never integrate it into the core analysis or modelling. This is both a scientific waste and an ethical concern regarding participant time.

2. **Poor handling of missingness**: EMA data are missing non‑randomly—participants are less likely to respond when they are active, stressed, or in certain environments. Most studies use complete‑case analysis (listwise deletion) without checking whether missingness is systematic, leading to biased estimates.

3. **Weak temporal alignment**: Many studies treat EMA responses as if they represent the behaviour at a single moment, ignoring that behaviours have duration and that the prompt‑response interval introduces delay. This is particularly problematic for sedentary behaviour, where a 15‑minute window may contain multiple posture transitions.

4. **Failure to use EMA to resolve accelerometer ambiguity**: The field often collects EMA items that are **redundant** with accelerometer data (e.g., “How intense was your activity?”) rather than items that add new information (e.g., “What domain was this activity?”). This reflects a misunderstanding of EMA’s unique value proposition.

5. **No reporting of prompt‑response lag**: Even when both prompt and response timestamps are recorded (rare), they are rarely reported or used in analysis. A participant who responds 15 minutes after a prompt is reporting on a different behavioural window than one who responds immediately.

6. **Neglect of compliance EMA items**: Virtually no studies ask participants “Have you been wearing the accelerometer continuously since the last prompt?” or “Did you take the device off at any point?” This means non‑wear periods are indistinguishable from sedentary behaviour in accelerometer data, and EMA cannot help resolve this.

---

## Best‑Practice Recommendations for Future Studies

### What an Ideal EMA Component Should Look Like

#### For Physical Activity Classification

| Element | Recommendation |
|---------|----------------|
| **Prompt schedule** | Event‑triggered (accelerometer‑detected activity changes) OR random sampling with 4–6 prompts/day |
| **Core EMA items** | Current activity type (categorical, 6–8 options); location (4 options); domain (work/leisure/transport/household) |
| **Alignment method** | Fixed window (±15 minutes) with sensitivity analysis for window size |
| **Compliance tracking** | Record prompt timestamp and response timestamp; calculate lag |
| **Missing data** | Report compliance rate; test for systematic missingness; use multiple imputation or inverse probability weighting |
| **Battery length** | ≤10 items per prompt; <90 seconds to complete |

#### For Sedentary Behaviour Interpretation

| Element | Recommendation |
|---------|----------------|
| **Prompt schedule** | **Sedentary‑triggered EMA** (e.g., after 20–30 minutes of continuous sitting) — this is the gold standard |
| **Core EMA items** | Social context (alone/with whom); location type; primary activity while sedentary (e.g., work, TV, eating, reading) |
| **Alignment method** | Prompt triggered *during* the sedentary bout; alignment is naturally precise |
| **Compliance tracking** | Report accuracy of triggered prompts relative to total eligible bouts |
| **Missing data** | Analyse whether missing prompts are associated with bout characteristics (e.g., length, location) |

#### For Context‑Aware Behaviour Analysis

| Element | Recommendation |
|---------|----------------|
| **Prompt schedule** | Time‑based (5–7 prompts/day) with stratification across waking hours |
| **Core EMA items** | Domain; social context; location; purpose; affect (2‑item: valence + arousal) |
| **Alignment method** | Pre‑prompt window (e.g., 30 minutes before) for association analyses |
| **Compliance tracking** | Day‑level compliance (≥70% of expected prompts) |

#### For Multimodal Algorithm Development

| Element | Recommendation |
|---------|----------------|
| **Prompt schedule** | **Event‑triggered** (accelerometer‑detected transitions) + random prompts for coverage |
| **Core EMA items** | Activity type (specific categories that map to model outputs); location; domain |
| **Alignment method** | Point‑based labeling (±30 seconds) for acute states; retrospective window (1–5 minutes prior) for gradual states |
| **Sample size** | Large (e.g., WEALTH: n=589) to provide sufficient labelled examples across activity types |
| **Validation** | Hold‑out set for model evaluation; comparison to existing algorithms |

### What Should Be Avoided

- **Collecting EMA items that duplicate accelerometer data** (e.g., “How many minutes did you walk?” — accelerometer already measures this more accurately).
- **Very long EMA batteries (>20 items)** — causes prompt fatigue, reduced compliance, and reactive behaviour change.
- **Ambiguous activity categories** — “exercising” is too vague; specify “walking for exercise,” “running,” “cycling,” etc.
- **No alignment strategy** — if you cannot describe how EMA timestamps will link to accelerometer windows, your design is incomplete.
- **Collecting EMA without a clear modelling or interpretive purpose** — every EMA item should have a justified role in the analysis.

### Balance Between Burden and Scientific Value

| Burden Level | Recommended Use | Example |
|--------------|----------------|---------|
| **Very low (1–3 items)** | Large‑scale surveillance; compliance tracking | Domain + location + social context |
| **Low (4–6 items)** | Most general PA/SB studies | Activity type + domain + location + social context + affect |
| **Moderate (7–12 items)** | Focused psychological or mechanistic studies | Add fatigue, self‑efficacy, barriers, pain |
| **High (13+ items)** | Not recommended for general use | — |

**Principle**: Every EMA item should be **minimally sufficient** to answer the research question. If an item does not have a planned role in analysis, remove it.

---

## Representative Studies and Datasets

### 1. Giurgiu et al. (2020) — Accuracy of Sedentary Behavior–Triggered EMA

**Why it matters**: This study introduced and validated the method of **accelerometer‑triggered EMA** for sedentary behaviour—a methodological advance that directly addresses the temporal alignment problem.

**What was collected**: Thigh‑worn Move accelerometer; smartphone‑delivered EMA triggered after 20 minutes of continuous sitting/lie-down; contextual items on location, social context, and primary activity during the sedentary bout.

**How EMA was used**: To collect **in‑bout** contextual information, eliminating recall error and ensuring temporal alignment. The triggered approach captured 82.77% of prolonged sedentary bouts, compared to random sampling which would have captured up to 47.9% fewer bouts.

**Key findings**: 40% of prolonged sedentary bouts occurred during work; 57% occurred while not alone.

**Limitations**: Small sample (n not specified in abstract); technical requirements (Bluetooth Low Energy, real‑time accelerometer processing) may limit scalability.

---

### 2. WEALTH Study — Sigcha et al. (2025 preprint) — Data Labelling for Free‑Living PA Recognition

**Why it matters**: The largest‑scale demonstration of EMA as a **label source for activity recognition algorithms** in free‑living conditions (n=589).

**What was collected**: Thigh‑worn accelerometer (device not specified in abstract but part of WEALTH protocol); event‑based EMA surveys; six PA categories.

**How EMA was used**: EMA responses were synchronised with accelerometer signals to create a sparse labelled dataset, which was used to train a machine learning classifier and compared against activPAL CREA ground truth.

**Key findings**: 97% agreement with ground truth for labelling; trained model achieved 73.6% classification accuracy.

**Limitations**: Preprint—not peer‑reviewed; EMA labels compared against another algorithm rather than direct observation; generalisability to other accelerometer devices unknown.

---

### 3. Monnaatsie et al. (2024) — Validation of EMA Against Accelerometry in Shift Workers

**Why it matters**: Direct criterion validation of EMA‑reported PA and SB against ActiGraph accelerometer data.

**What was collected**: Hip‑worn ActiGraph; 5 EMA prompts/day at 3‑hour intervals via mobile app; self‑reported activity type (PA, sitting, other).

**How EMA was used**: As a **validation target**—associations between EMA‑reported activity and accelerometer counts per minute (CPM) and steps were examined.

**Key findings**: When participants reported PA, accelerometer CPM and steps were significantly higher (β=1184 CPM; β=20.9 steps) than for other EMA activities. Sitting reports corresponded to lower CPM and steps.

**Limitations**: EMA items were broad (PA/sitting/other); no detailed contextual items (domain, social context). Prompts at 3‑hour intervals may miss shorter behavioural episodes.

---

### 4. Maher, Rebar & Dunton (2021) — Context Stability and PA/SB Habit

**Why it matters**: Demonstrates EMA’s value for **theoretically grounded behaviour analysis**—testing whether context stability predicts PA and SB.

**What was collected**: activPAL thigh‑worn monitor; 6 EMA prompts/day assessing current behaviour, social context, and physical context; baseline habit questionnaire.

**How EMA was used**: To assess the **context** (physical, social, temporal) surrounding PA and SB bouts, enabling calculation of context stability scores that were then linked to accelerometer‑derived behaviour.

**Key findings**: More stable physical contexts for PA predicted more MVPA; more stable social contexts for sitting predicted more SB.

**Limitations**: EMA assessed context only at prompt times, not continuously; context stability was derived from sparse EMA samples, which may not fully capture context variability.

---

### 5. Maes et al. (2023) — Within‑Person Associations of PA with Time‑Varying Determinants

**Why it matters**: Demonstrates EMA’s use for **temporal dynamics**—examining how momentary psychological states predict subsequent PA.

**What was collected**: Wrist‑worn Axivity AX3; 6 time‑based EMA prompts/day assessing emotions, fatigue, intention, self‑efficacy; PA measured at 15, 30, 60, and 120 minutes post‑EMA.

**How EMA was used**: As a **predictor** of subsequent accelerometer‑measured PA, with fine‑grained temporal windows.

**Key findings**: Irritation, feeling down, intention, and self‑efficacy were positively associated with subsequent PA at various time lags; relaxation, satisfaction, and fatigue were negatively associated.

**Limitations**: EMA assessed only momentary states, not contextual factors; causal inference limited despite temporal ordering; wrist‑worn accelerometry less accurate for posture than thigh‑worn devices.

---

### 6. Dunton, Dzubur & Intille (2016) — Sensor‑Informed Context‑Sensitive EMA

**Why it matters**: Early demonstration of **motion‑triggered EMA** using phone sensors to prompt context‑sensitive surveys.

**What was collected**: Waist‑worn ActiGraph; phone app triggering CS‑EMA surveys after motion events (activity, no‑activity, no‑data); random EMA prompts (up to 7/day).

**How EMA was used**: To assess activity type and context immediately after sensor‑detected events, augmenting accelerometer data with contextual information.

**Key findings**: More MVPA was recorded in the 30 minutes before CS‑EMA Activity prompts than before No‑Activity or No‑Data prompts; participants were 5 times more likely to report “going somewhere” before CS‑EMA Activity prompts.

**Limitations**: Motion detection relied on phone accelerometer rather than dedicated body‑worn device; phone may not be carried during all activities, potentially missing episodes.

---

### 7. Systematic Review — Liao et al. (2018) — Methodology of EMA Studies on Sedentary Behaviour

**Why it matters**: Provides the most comprehensive methodological snapshot of EMA + accelerometry for SB.

**What was reviewed**: 21 articles using EMA to measure SB in youth and adults.

**Key findings**: Only 19% of EMA studies on SB used objective methods (accelerometer); the most common accelerometer was ActiGraph; the 15‑minute window was the most frequently used for EMA‑accelerometer alignment.

**Limitations**: Published in 2018; smartphone‑based EMA has advanced considerably since; focus on SB only.

---

## Final Synthesis: What Everyone Does, What They Do Not Do, and What They Should Do

### What Everyone Does

1. **Collects basic EMA items**: activity type, location, social context—usually via smartphone apps with 4–7 daily prompts.
2. **Uses time‑based (signal‑contingent) prompts** at fixed or quasi‑random intervals, typically over 7–14 days.
3. **Reports basic associations** between EMA items and accelerometer‑derived PA/SB (e.g., higher activity counts when participants report PA).
4. **Uses a 15‑minute window** for aligning EMA timestamps with accelerometer data—often without justification.
5. **Treats EMA as a “validation” source** for accelerometer data or vice versa, rather than as a complementary layer.

### What Everyone Does Not Do

1. **Does not integrate EMA into modelling** beyond descriptive statistics or basic bivariate associations. EMA is collected, summarised, and then abandoned in most studies.
2. **Does not use event‑triggered (accelerometer‑informed) EMA** despite its clear methodological advantages for temporal alignment and burden reduction.
3. **Does not collect compliance EMA items** (“Was the accelerometer worn continuously?”), leaving non‑wear periods indistinguishable from sedentary behaviour.
4. **Does not report prompt‑response lag** or adjust for it in analysis.
5. **Does not handle missing EMA data appropriately**—listwise deletion remains the norm.
6. **Does not use EMA to resolve accelerometer ambiguity**—the core missed opportunity. EMA items that add domain, purpose, and intent are less common than redundant items (e.g., perceived exertion).
7. **Does not report alignment methods transparently**—many studies omit how EMA timestamps were linked to accelerometer windows.

### What Everyone Should Do

#### For All Studies

- **Define the purpose of EMA before data collection**—every EMA item should have a justified role in analysis, not just “to provide context.”
- **Report EMA compliance rates** (prompt response rate, by day and by participant) and **test for systematic missingness**.
- **Record both prompt timestamp and response timestamp**; report median response lag; consider lag in alignment decisions.
- **Use event‑triggered EMA whenever possible**—it reduces burden, improves temporal alignment, and captures behaviour during the episode of interest rather than retrospectively.
- **Collect minimal compliance items**: “Have you been wearing the accelerometer continuously since the last prompt?” (yes/no).
- **Handle missing EMA data** using multiple imputation, inverse probability weighting, or at minimum, sensitivity analyses assuming different missingness mechanisms.

#### For Physical Activity Classification

- **Use EMA as a label source** for activity recognition models—train on free‑living EMA‑labelled data rather than laboratory scripts.
- **Align EMA to accelerometer windows using point‑based labeling** (±30 seconds) for acute activity transitions.
- **Collect activity type at sufficient granularity** (e.g., sitting, standing, walking, running, cycling, stair climbing) but avoid excessive categories (>10).

#### For Sedentary Behaviour Interpretation

- **Use sedentary‑triggered EMA** (e.g., after 20–30 minutes of continuous sitting)—this is the gold standard.
- **Collect domain (work vs. leisure), social context, and location**—these three items resolve most of the interpretive ambiguity of SB.
- **Report accuracy of triggered prompts** relative to total eligible sedentary bouts.

#### For Context‑Aware Behaviour Analysis

- **Collect domain, purpose, and social context**—these add the most value beyond accelerometry.
- **Use pre‑prompt windows** for association analyses (e.g., 30 minutes before EMA).
- **Stratify prompts across waking hours** to capture contextual variability throughout the day.

#### For Multimodal Algorithm Development

- **Combine triggered and random prompts**—triggered for specific behaviour episodes, random for coverage.
- **Collect a large sample** (hundreds of participants) to provide sufficient labelled examples across activity categories.
- **Validate EMA labels** against a gold standard (e.g., activPAL CREA, direct observation) for a subset of data.
- **Publish the labelled dataset** (anonymised) to advance the field—sparse EMA‑labelled accelerometer data are a valuable public good.

### The Core Recommendation

**Stop treating EMA as a “nice to have” add‑on that is collected and then ignored. Treat EMA as an essential data layer that provides what accelerometry cannot: meaning, context, and purpose. Design EMA around a specific modelling or interpretive question, not as a general‑purpose “context” collection. And for the love of the field, align your timestamps properly, report your compliance, and handle your missing data.**

---

## Compact Summary Table

| EMA Use in Accelerometer Study | What It Adds | Limitations | Burden | Modelling Value | Recommendation |
|--------------------------------|--------------|-------------|--------|-----------------|-----------------|
| Current activity type labelling | Provides direct labels for classification algorithms | Sparse relative to continuous sensor data | Low | High (for supervised learning) | Essential |
| Domain (work/leisure/transport/household) | Resolves behavioural context—accelerometry alone cannot | Requires domain‑specific categories | Low | Very high | Essential |
| Social context | Explains SB patterns; informs intervention targeting | Categorical only | Low | High (for behaviour interpretation) | Essential |
| Location | Separates occupational from leisure sitting | Indoor/outdoor distinction may be coarse | Low | High | Recommended |
| Affect/mood | Links PA to psychological states; explains behaviour maintenance | Subjective; potential recall bias | Low‑moderate | Moderate (for psychological studies) | Recommended when relevant |
| Fatigue/pain | Explains activity limitations; clinically relevant | Condition‑specific | Low | Moderate (in clinical/older adult populations) | Condition‑specific |
| Perceived exertion | Duplicates accelerometer intensity measurement | Poor added value | Low | Low | Not recommended |
| Compliance (device worn?) | Distinguishes non‑wear from sedentary behaviour | Requires self‑report | Minimal | Very high (data quality) | Strongly recommended |
| Intention/self‑efficacy | Explains intention‑behaviour gap | Temporal alignment difficult | Low | Low‑moderate | Only for specific mechanistic studies |
| Open‑ended text | Rich qualitative data | High burden; hard to analyse at scale | Very high | Low | Avoid in quantitative studies |

---


**Final note**: This synthesis has been deliberately narrow. The literature genuinely fitting the scope is limited, and the field has substantial room for methodological improvement. The most promising advances—event‑triggered EMA, EMA‑based labelling for activity recognition, and large‑scale studies like WEALTH—point toward a future where EMA is not an afterthought but an integral component of accelerometer‑based physical behaviour research. That future is not yet the present. But it is within reach, and the field should move decisively toward it.