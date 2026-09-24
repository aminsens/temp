**EMA in Body-Mounted Accelerometer Research**

**Physical Activity & Sedentary Behaviour**

*Definitive Cross-Source Synthesis*

Synthesised from 7 independent AI deep-research runs · April 2026

# **1\. Executive Summary**

Ecological Momentary Assessment (EMA) in body-mounted accelerometer studies of physical activity (PA) and sedentary behaviour (SB) is not a measurement replacement — it is a contextual annotation layer. Seven independent AI deep-research runs, applied to this narrow literature, converge with striking consistency on a set of core findings summarised below.

| CORE FINDING  EMA's irreplaceable contribution is context: the domain, purpose, social setting, and subjective meaning of movement that no accelerometer can supply. Its established value lies in coarse validation, contextualisation, and SB interpretation — not in fine-grained continuous activity recognition. |
| :---- |

The five points of universal consensus across all seven reports:

* EMA is not ground truth. It is near-ground truth, weak labelling, or contextual metadata — never a precise sensor-equivalent.

* EMA's core value is context: domain (work/leisure/transport/household), purpose, social setting, location, and subjective state.

* Temporal alignment (sparse EMA vs. dense accelerometer data) is the hardest unsolved methodological problem.

* EMA is routinely collected but rarely integrated into modelling pipelines — the field's single largest missed opportunity.

* Event-triggered (sensor-informed) EMA is methodologically superior to random prompting but remains uncommon in published practice.

The synthesis also identifies what the field overrates and underrates — findings absent from any single report but revealed by comparing them. These are integrated throughout.

# **2\. Scope Definition**

This document covers only studies meeting all three criteria simultaneously:

* Primary movement data from a dedicated body-mounted accelerometer (ActiGraph, activPAL, Axivity, GENEActiv, SENS Motion, or equivalent). Smartphone accelerometers excluded.

* Research focus on physical activity, sedentary behaviour, posture, activity classification, or free-living physical behaviour assessment.

* A concurrent EMA or equivalent momentary self-report component (experience sampling, ambulatory diary, prompted self-report) collected during the same monitoring period.

Excluded: smartphone sensing, physiological monitoring (HR, PPG, ECG, EEG), general digital phenotyping, rehabilitation biomechanics without PA focus, purely lab-based HAR, generic mobile health studies without accelerometer-based PA focus.

The literature genuinely meeting this strict scope is smaller than expected. There is a solid body of validation and contextualisation work, but the subset directly using EMA for algorithm development is thin. This is stated clearly in each relevant section.

# **3\. What EMA Contributes Beyond Body-Mounted Accelerometers**

## **3.1 The Fundamental Sensor Limitation**

Body-mounted accelerometers measure movement intensity, duration, frequency, and — when thigh-mounted — posture (sit/stand/step). The activPAL achieves ≥95% agreement with direct observation for total sedentary time. ActiGraph and GENEActiv classify activity intensity reliably. But no accelerometer, regardless of placement, can determine:

* What specific activity is occurring (TV watching vs. desk work during the same sedentary bout)

* The behavioural domain: occupational, leisure, transport, or household

* The purpose of movement: exercise, commuting, household necessity, or incidental

* The social context: alone, with family, with colleagues, with strangers

* The physical environment: home, workplace, vehicle, park, indoors, outdoors

* Subjective states: affect, fatigue, perceived exertion, motivation, pain, barriers

* Intentionality: planned exercise vs. incidental movement

## **3.2 How EMA Differs from Other Methods**

| Method | What it provides | Key limitation vs EMA |
| :---- | :---- | :---- |
| Retrospective questionnaires(IPAQ, BRFSS, GPAQ) | Summary estimates of PA/SB over days–weeks | Recall bias; IPAQ overestimates MVPA by \~900 min/week vs. accelerometry; EMA overestimates by only \~71 min/week |
| Time-use diaries (ACT24) | Detailed 24-hr recall of activities and contexts | Completed retrospectively; burdensome; EMA captures data closer to real time |
| Direct observation | Gold standard for activity type and context | Costly, invasive, unscalable for free-living multi-week studies |
| Video annotation | High fidelity labels in lab settings | Severe privacy concerns; enormous coding workload; infeasible for free-living |
| Passive sensing (GPS, light) | Continuous objective environmental data | No subjective or contextual information; no participant voice |
| Controlled lab labelling | Clean, unambiguous activity labels | Fails to generalise to free-living variability |

## **3.3 What EMA Is in This Field — A Taxonomy of Roles**

Based on converging evidence, EMA in body-mounted accelerometer PA/SB studies simultaneously serves these roles:

* Contextual metadata layer — domain, location, social setting, purpose of accelerometer-detected behaviour (ESTABLISHED)

* Behavioural interpretation layer — explaining why a particular pattern of movement or non-movement occurred (ESTABLISHED)

* Near-ground truth for coarse activity categories — participant-reported labels that are the closest feasible approximation to ground truth in free-living conditions (ESTABLISHED for binary states; WEAK for fine-grained)

* Subjective state capture — affect, fatigue, perceived exertion, motivation, barriers that cannot be inferred from accelerometry (ESTABLISHED)

* Compliance and quality-control signal — confirming device wear, identifying non-wear periods (ESTABLISHED in principle; UNDERUSED in practice)

* Weak label source for algorithm development — sparse, noisy but ecologically valid labels for training or validating activity classifiers (EMERGING — thin peer-reviewed evidence)

| ⚠ OVERRATED:  Calling EMA 'ground truth' for classifier training inverts the actual reliability relationship. The accelerometer is usually the more reliable instrument for movement. EMA-as-validator framing implies EMA is the criterion when it is not. Two of seven reports (Gemini, Opus v2) frame EMA's labelling role more optimistically than the evidence supports — the remaining five correctly characterise it as weak supervision at best. |
| :---- |

# **4\. How EMA Is Used in PA/SB Studies**

## **4.1 Criterion/Convergent Validation of Broad Activity States**

This is the most established use. Multiple studies demonstrate that EMA-reported activity categories align with concurrent accelerometer-derived behaviour in windows around prompts (±15 minutes). Evidence is strong for coarse binary distinctions and weak for fine-grained intensity categories.

* Dunton et al. (2012, Frontiers Psych): Adults, ActiGraph (hip), 8 random prompts/day. EMA-reported PA → higher concurrent MVPA; EMA-reported SB → higher sedentary counts. Canonical example of coarse criterion validity.

* Maher et al. (2018, Frontiers Psych): 104 older adults, activPAL (thigh), 6 prompts/day × 10 days, 92% compliance. 'Physical activity/exercising' EMA → higher device-measured activity; sitting EMA → higher sedentary time. Small post-prompt PA reduction (reactivity noted).

* Monnaatsie et al. (2024): Shift workers, ActiGraph \+ EMA at 3-hour intervals. EMA-reported PA → significantly higher CPM (β=1184) and steps (β=20.9) vs. sitting reports.

* devilSPARC / JMIR 2016: Intensity self-classification (light/moderate/vigorous) showed clear mismatch at fine-grained levels — coarser binary classification more reliable.

| EVIDENCE VERDICT:  STRONG for binary (sitting/active) distinctions. WEAK and potentially misleading for fine-grained intensity self-classification. Do not use EMA intensity labels as ML training targets. |
| :---- |

## **4.2 Contextualising Where and With Whom Behaviour Happens**

EMA is used to add location, social, and environmental context that accelerometers cannot provide. Liao et al. (2015) showed home was the dominant context for PA/SB in adults and that setting mattered for MVPA patterns. Kracht et al. (2021, IJBNPA) linked prior sedentary time to being indoors or alone in adolescents. Hancock et al. (2021) showed that identical activity categories carry different experiential meaning depending on context. Without EMA, all these distinctions are invisible to the sensor.

## **4.3 Interpreting Sedentary Behaviour Domains**

EMA is especially valuable for SB because 'sedentary time' is behaviourally heterogeneous. Device-detected sitting could be work, meetings, TV, reading, meals, or transport. Giurgiu et al. (2020) found 40% of prolonged sedentary bouts occurred at work and 57% while not alone — distinctions with different health and intervention implications that accelerometers cannot make. Hevel et al. (2021) demonstrated that affect during sedentary behaviour depended on social and physical context.

Evidence quality: STRONG for the value of domain/context distinctions. INCONSISTENT for specific health-outcome differences between domains.

## **4.4 Capturing Momentary Psychology as Antecedents/Consequences**

A distinct family of studies uses EMA to measure time-varying psychological states, then models accelerometer-derived PA in the minutes/hours after prompts.

* Maher et al. (2020): EMA-measured intentions and self-efficacy predicted subsequent activPAL-measured sedentary behaviour over 2-hour windows.

* Maes et al. (2023, JMIR Aging): Irritation, feeling down, high intention, and self-efficacy positively associated with subsequent PA at 15–120 minutes post-EMA. Axivity AX3 (wrist) \+ 6 time-based prompts/day.

Evidence quality: MODERATE. Temporally ordered but causal direction remains uncertain due to bidirectionality.

# **5\. Role of EMA in Labelling, Validation, and Algorithm Development**

## **5.1 The Label Type Taxonomy**

| Label Type | Description | Evidence in Literature |
| :---- | :---- | :---- |
| Direct label (strong) | EMA response 'I am currently walking' → label accelerometer segment as walking | High agreement (up to 97%) for clear activities like sitting and running (WEALTH study) |
| Weak label (noisy) | EMA 'I walked for exercise in the past 30 min' → label retrospectively | Lower and variable agreement; 32% for standing; \~50% for cycling |
| Contextual feature | EMA provides location, social context, domain → auxiliary input to model, not a label | Common in multilevel modelling; not yet standard in ML pipelines |
| Validation source | EMA labels used to check accelerometer-derived classification accuracy | Mixed results; strongest for binary (active/sedentary) comparisons |
| Error-analysis aid | EMA reveals when sensor misclassifies (e.g., standing reported but sensor shows sedentary) | Used informally; rarely formalised in published workflows |

## **5.2 The WEALTH Study — Current Benchmark**

Sigcha et al. (2025, preprint) — cited by all seven reports as the field's clearest exemplar. 589 participants, 7 days free-living, activPAL (thigh) \+ event-based EMA via HealthReact app, six PA categories.

* Up to 97% agreement with activPAL CREA ground-truth for sitting and running

* Only 32% agreement for standing — cognitively backgrounded, frequently incidental

* \~50% agreement for cycling — sensor placement variability and algorithmic ambiguity

* Machine learning classifier trained on EMA labels: up to 73.6% classification accuracy

| ⚠ CALIBRATE YOUR EXPECTATIONS:  This is a preprint. It is the only rigorous peer-reviewed-equivalent example of EMA-to-classifier integration in free-living PA research. Treat it as a proof-of-concept, not as established consensus. Five of seven AI reports correctly call EMA's labelling role 'promising but thin' or 'weak supervision at best.' Two reports (Gemini, Opus v2) frame it more optimistically — this is the most significant disagreement across the seven sources. |
| :---- |

## **5.3 Standing: The Hardest Activity to Label**

At least five of the seven reports independently flag standing as the most problematic EMA label target. Standing is:

* Cognitively 'backgrounded' — participants do not notice they are standing and frequently report the task instead ('cooking', 'doing dishes')

* Incidental and brief — transitions are short and not salient enough for accurate retrospective recall

* Behaviourally ambiguous — a 10-minute standing bout might span multiple micro-transitions

Agreement rates: 32% (WEALTH) to 44% (related studies). Using EMA standing labels as ML training targets will actively degrade classifier performance.

## **5.4 Does the Literature Integrate EMA into Modelling?**

No — not adequately. The dominant pattern across all seven reports is collection without integration: EMA is gathered, summarised in a descriptive table, and the accelerometer analysis proceeds independently. This is both a scientific waste and, where participant burden is high, an ethical concern.

| UNIVERSAL FINDING (all 7 reports agree):  The 'collected but not used' problem is the field's single most damaging pattern. Studies invest substantial participant burden collecting contextual data, then relegate it to Table 2 and never integrate it into modelling. This is the largest gap between what the field collects and what it produces. |
| :---- |

# **6\. Common EMA Variables — What to Collect, What to Avoid**

## **6.1 Variable Hierarchy**

Six of seven reports agree on this priority ordering of EMA variables for body-mounted accelerometer PA/SB research:

| Tier | Variable | Frequency in Literature | Utility for Accel. Research | Burden | Recommendation |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 1 — Essential | Current activity type (sitting, walking, running, cycling, standing) | Very common | High — core labelling variable | Low | Always collect |
| 1 — Essential | Location (home, work, outdoors, vehicle) | Common | High — domain discrimination | Low | Always collect |
| 1 — Essential | Social context (alone, with whom) | Common | High — SB interpretation | Low | Always collect |
| 1 — Essential | Device wear compliance ('wearing the monitor?') | Very rare — shockingly neglected | Very high — critical data quality | Minimal | Always collect |
| 2 — High value | Activity domain (work/leisure/transport/household) | Moderate — collected less than it should be | Very high — resolves biggest sensor ambiguity | Low | Strongly recommended |
| 2 — High value | Purpose/intentionality of movement | Rare | High — exercise vs incidental distinction | Moderate | Collect when feasible |
| 3 — Moderate | Affect/mood (valence \+ arousal, 2-item) | Moderate — often overcollected | Moderate — antecedents/consequences | Low–moderate | Include when primary RQ |
| 3 — Moderate | Fatigue | Moderate in clinical/older adult studies | High in clinical populations | Low | Include for specific populations |
| 3 — Moderate | Indoor/outdoor | Moderate | Moderate — environmental context | Low | Include when relevant |
| 4 — Low | Perceived exertion | Rare | Low — duplicates accelerometer intensity data | Low | Not recommended |
| 4 — Low | Barriers/motivation | Rare | Low for classification; moderate for intervention | High | Only for intervention studies |
| 4 — Avoid | Fine-grained intensity self-classification (light/moderate/vigorous) | Moderate — too common given unreliability | Negative — actively degrades ML classifiers | Low | Do not use as labels |

## **6.2 The Most Underrated Variable**

| 🔍 UNDERRATED — Device Wear Compliance:  Asking 'Are you wearing the accelerometer right now?' is almost never done, yet it costs almost nothing in burden and provides critical data quality information. It would allow distinguishing non-wear from sedentary behaviour, validating non-wear algorithms, and identifying data corruption. All seven reports note its absence. Called 'shockingly undercollected' in one report. This single item would improve data quality in nearly every study that omits it. |
| :---- |

## **6.3 Scientifically Attractive but Operationally Weak**

* Fine-grained intensity self-classification (light/moderate/vigorous): Accelerometers measure intensity better than humans self-report it. Evidence of clear mismatch at these levels. Do not use as ML labels.

* Intentionality / purpose of movement: Theoretically important (exercise vs. incidental), but difficult to operationalise in brief momentary surveys and suffers from temporal ambiguity. Aspiration exceeds execution.

* Open-ended text responses: Rich but unscalable; demanding; cannot be automatically processed at dataset scale.

* Very long affect batteries (full PANAS etc.): Adds compliance-degrading burden without improving activity classification. Use 2-item valence \+ arousal if affect is needed.

* Barriers/motivation: Items tend to be stable across the day, making momentary assessment redundant relative to a single baseline measure.

# **7\. Methodological Challenges Linking EMA to Accelerometer Data**

## **7.1 The Core Mismatch**

Accelerometers produce dense, continuous numerical vectors at 25–100 Hz — millions of data points per day. EMA produces sparse, discrete, categorical, and temporally fuzzy labels — 4–10 per day. Aligning these modalities is the central unsolved methodological problem in the field.

## **7.2 Specific Challenges and Evidence**

### **Prompt-response lag**

Participants rarely answer EMA prompts at the moment of delivery. A 5-minute average lag is documented (IJBNPA 2021 adolescent study). A sensor-triggered EMA study in older adults found each additional minute of lag decreased the odds of accurate behaviour confirmation by 20%. Clock drift between the accelerometer device and smartphone compounds this. Most studies do not record both prompt delivery and response timestamps — making lag invisible and uncorrectable.

### **Recall window mismatch**

'Right now' vs. 'past 30 minutes' vs. 'since the last prompt' create fundamentally different temporal alignment problems. Studies mixing recall frames within the same protocol create structural disagreements with accelerometer windows. One child study (JMIR mHealth 2018\) created a structural mismatch by inconsistently switching between '2-hour recall' and 'since waking' recall frames.

### **Demarcation uncertainty**

A single EMA label like 'cooking' is mapped onto 15 minutes of highly heterogeneous accelerometer data: 2 minutes walking to the kitchen, 5 minutes static standing, 3 minutes dynamic arm movement, 5 minutes sitting at the table. This confuses classifiers and injects noise that most studies ignore. Addressed in detail by only 2–3 of the seven reports — systematically underappreciated across the field.

### **Sparse labels vs. dense time series**

Even with 8 prompts/day and perfect compliance, \>98% of accelerometer data remains unlabelled. Most studies either discard this data (wasteful) or assume label persistence between prompts (inaccurate). Semi-supervised and self-supervised learning methods that leverage unlabelled data exist but are almost never applied in this field.

### **Non-random missingness**

Participants are significantly less likely to respond during vigorous activity, driving, intense social situations, or when the phone is unavailable. Dunton et al. (2012) found unanswered prompts correlated with higher MVPA for some subgroups. This means the labelled dataset systematically underrepresents high-intensity and context-specific activities — and listwise deletion (the usual response) produces biased estimates.

### **Compliance decay over study duration**

Compliance drops non-trivially after the first 3 days in event-triggered setups. Most reports cite an overall compliance percentage without reporting the temporal trajectory — masking the pattern that data quality degrades over the study period. Underreported in all seven sources.

## **7.3 Alignment Strategies — Strength of Evidence**

| Strategy | Description | Evidence Strength | Best Used For |
| :---- | :---- | :---- | :---- |
| Fixed symmetric window(±15 min around prompt) | Extract accel. data from window centred on response timestamp | STRONG — most common in validation literature | Criterion validity studies; 'right now' EMA items |
| Pre-prompt window(30–60 min before prompt) | Extract data from period before EMA prompt | MODERATE — clear conceptual rationale | Antecedent studies; context preceding reported behaviour |
| Post-prompt window(15–120 min after prompt) | Extract data from period after EMA prompt | MODERATE — conceptually clean for prediction | JITAI targeting; determinant → behaviour modelling |
| Event-triggered alignment | Accel. detects specific state (e.g., 20+ min sitting), triggers EMA during it | STRONGEST for sedentary episodes; eliminates recall error | SB interpretation; activity labelling; JITAI |
| Dual-timestamp recording | Record both prompt delivery time and response time; use prompt time for alignment | STRONGEST in theory — almost never implemented | All studies; should be standard practice |
| Day-level aggregation | Compare daily EMA summaries to daily accelerometer totals | WEAK — loses all temporal resolution | Longitudinal trend studies only; not for bout analysis |

| 🔍 UNDERRATED — Hybrid Sampling Designs:  Random prompts for background coverage \+ event-triggered prompts for episodes of interest. This approach addresses the coverage-vs-precision tradeoff that each pure design handles poorly. Recommended by two of seven reports (ChatGPT Deep Research, Opus v2). Almost never implemented in practice. Represents a significant methodological opportunity. |
| :---- |

# **8\. Common Weaknesses and Blind Spots**

The following weaknesses appear with remarkable consistency across all seven reports. They represent field-level patterns, not individual study failures.

### **Collection without integration**

EMA data are collected, summarised descriptively, and the modelling section proceeds as if EMA were never collected. All seven reports identify this as the most damaging pattern. The field invests participant burden without producing the scientific payoff that burden should justify.

### **No item content validity**

A systematic review (Liao et al. 2018 IJBNPA) found no reviewed study explicitly reported assessing EMA item content validity. Most gave no rationale for prompt design. Only one reported response latency. None reported backfilling. This is a field-level failure that means the items being used as 'labels' often have unknown measurement properties.

### **Poor missing data handling**

Listwise deletion is the default despite missingness being demonstrably non-random. Multiple imputation or inverse probability weighting is feasible but rarely used. When studies do report compliance, they typically report a single overall percentage — masking the temporal decay pattern and activity-type-specific missingness that matter most.

### **Weak temporal alignment reporting**

How EMA timestamps were matched to accelerometer epochs is frequently undescribed. Studies state data were 'collected concurrently' without specifying window sizes, prompt-response lag handling, or conflict-resolution rules. Reproduction of alignment decisions is essentially impossible from most published methods sections.

### **Underuse for sedentary behaviour interpretation**

Despite the well-established limitation that accelerometers cannot distinguish between types of sedentary behaviour, EMA is rarely used systematically to characterise sedentary episodes by domain or type. The field measures sedentary duration well and interprets sedentary meaning poorly.

### **Redundant items that duplicate accelerometer data**

Studies frequently collect EMA items accelerometers already measure better (perceived exertion, duration estimates, step count estimates) while omitting items that would add genuine information (domain, purpose, intentionality). This reflects a systematic misunderstanding of EMA's unique value.

### **Absence of event-triggered EMA implementation**

Six of seven reports recommend event-triggered EMA as superior to random prompting, yet it remains uncommon in practice. The technical barriers (BLE connectivity, real-time accelerometer processing) are real but surmountable. The field's investment in overcoming them has been insufficient relative to the methodological payoff.

### **No public datasets combining accelerometry with timestamped EMA**

All seven reports independently identify the absence of shareable, open datasets combining raw accelerometer data with time-stamped EMA responses as a field-wide gap. Such datasets would accelerate methodological development and enable reproducible research, but they essentially do not exist.

# **9\. Best-Practice Recommendations**

## **9.1 For Physical Activity Classification**

* Use event-triggered EMA: prompts fired when the accelerometer detects an activity transition. Maximises temporal precision and contextual relevance.

* Collect activity type with 6–8 structured options (sitting, standing, walking, running, cycling, stair-climbing, other). Not free text. Not fine-grained intensity categories.

* Record both prompt delivery and response timestamps. Discard or downweight responses with \>10-minute lag.

* Treat EMA labels as weak supervision: use noise-robust ML methods, semi-supervised learning, or confidence-weighted label propagation — not standard supervised learning assuming clean labels.

* Do not use EMA intensity self-classification (light/moderate/vigorous) as training labels. This is demonstrably unreliable and will degrade classifiers.

* For training data, combine event-triggered prompts (specific episodes) with periodic random prompts (background coverage) in a hybrid design.

* Validate EMA labels against a reference algorithm (e.g., activPAL CREA) or direct observation on a subsample before using for classifier training.

## **9.2 For Sedentary Behaviour Interpretation**

* Use a thigh-worn posture-capable monitor (activPAL) as primary SB device. Hip/wrist accelerometers cannot reliably distinguish sitting from standing.

* Use sedentary-triggered EMA: prompt after 20–30 minutes of continuous sitting. This concentrates data collection on the most relevant episodes and eliminates most recall error.

* Collect: social context (alone/with whom), domain (work/leisure/transport/household), primary activity while sedentary (TV, computer, eating, reading, meetings). These three items resolve most interpretive ambiguity.

* Keep the EMA survey very brief (\<5 items, \<30 seconds) since sedentary episodes are frequent and long batteries cause rapid fatigue.

* Report accuracy of triggered prompts relative to total eligible sedentary bouts.

## **9.3 For Context-Aware Behaviour Analysis**

* Use time-based random-within-window prompting (5–6 prompts/day) to support within-person inference across waking hours.

* Core items: domain, social context, location, indoor/outdoor. These four variables capture the highest-value context at minimal burden.

* Add affect (2-item: valence \+ arousal) only when emotional antecedents/consequences are a primary research question.

* Use pre-prompt windows (30 min before) for association analyses; use post-prompt windows (15–120 min after) for prediction/JITAI logic.

* Explicitly specify and pre-register the accelerometer linkage window before data collection.

## **9.4 For Multimodal Algorithm Development**

* Design EMA protocols with algorithm development as an explicit design goal — not a secondary data stream.

* Hybrid sampling: event-triggered prompts for activity episodes of interest \+ random prompts for background coverage.

* Use EMA as contextual features (domain, social, location) and as weak labels for targeted windows, not as a blanket ground-truth stream.

* Invest in larger samples (hundreds of participants) to provide sufficient labelled examples across activity categories.

* Consider publishing anonymised linked datasets. EMA-labelled accelerometer data are a valuable public good and a field-level gap all seven reports identify.

* Bridge the HAR and EMA literatures. The HAR community has sophisticated classifiers trained on laboratory labels that fail in the wild. The EMA community has rigorous real-time assessment methods rarely applied to classification. Their convergence is the most promising direction for free-living physical behaviour science.

## **9.5 Universal Requirements for All Studies**

| Non-negotiable minimum:  Always collect: (1) activity type, (2) domain (work/leisure/transport/household), (3) location, (4) social context, (5) device wear compliance. Limit to 4–6 prompts/day for studies \>7 days. Keep each survey \<3 minutes. Report prompt schedule, compliance rate by day, response latency distribution, missingness pattern, and the exact linkage rule used to connect EMA to accelerometer windows. |
| :---- |

* Pre-specify all linkage windows before data collection. Do not fit windows post-hoc to optimise associations.

* Report compliance by day of study (to capture decay) and by time of day (to capture circadian bias) — not just overall.

* Always assess whether missingness is associated with activity level or context before assuming it is random.

* Do not impose high EMA burden without a corresponding analytic payoff. Every item should have a pre-specified role in the analysis.

# **10\. What Is Overrated and What Is Underrated**

This section captures the cross-source meta-analysis — findings only visible by comparing the seven reports against each other.

## **10.1 What the Field Overrates**

| OVERRATED \#1 — EMA as a primary training label source for HAR classifiers:  The evidence supports EMA labels only for coarse binary classification (sitting/not, active/not) and a handful of clear activities (walking, running). For fine-grained continuous free-living classification, EMA is a complementary weak signal, not a replacement for direct observation. The WEALTH study is the single proof-of-concept; 73.6% accuracy is modest; standing labels achieve only 32% agreement. Two of seven reports (Gemini, Opus v2) frame this more optimistically than the evidence warrants. |
| :---- |

| OVERRATED \#2 — Affect/mood as a major EMA variable for PA research:  While affect is commonly collected, five of seven reports note it adds burden without improving activity classification. The scientific value is primarily for psychological/determinant studies. Yet studies keep collecting extensive mood scales while omitting higher-value items like domain and purpose. The field systematically over-collects affect and under-collects domain. |
| :---- |

| OVERRATED \#3 — EMA 'validating' accelerometer data:  The framing that EMA validates accelerometer output inverts the actual reliability relationship. The accelerometer is usually the more reliable instrument for movement quantity. EMA is a convergent validity check for coarse states, not a criterion measure. Using EMA-accelerometer agreement as evidence of accelerometer quality misunderstands what EMA can and cannot do. |
| :---- |

| OVERRATED \#4 — EMA capturing intentionality of movement:  Distinguishing intentional exercise from incidental movement is a theoretically important goal mentioned in multiple reports, but purpose/intention variables are rarely collected, difficult to operationalise in brief surveys, and suffer from temporal ambiguity. The aspiration consistently outpaces the execution. |
| :---- |

## **10.2 What the Field Underrates**

| UNDERRATED \#1 — Device wear compliance items:  Asking 'are you wearing the accelerometer?' is almost never done despite being close to free. It would distinguish non-wear from sedentary, validate non-wear algorithms, and improve data cleaning. All seven reports note its absence. This is the single highest-return, lowest-cost improvement available to the field right now. |
| :---- |

| UNDERRATED \#2 — Domain (work/leisure/transport/household) as the highest-value variable:  All sources agree domain is the EMA variable that most resolves sensor ambiguity (why is this person sitting/walking?). Yet it is collected only 'moderately' in practice, and one report argues it is genuinely rare. The field systematically undervalues the most productive EMA item it has. |
| :---- |

| UNDERRATED \#3 — Prompt-response latency reporting:  Only a tiny minority of studies record and report the delay between prompt delivery and participant response. One systematic review found only one reviewed study that reported latency, and none that reported backfilling. This is critical information for temporal alignment and is almost universally omitted. |
| :---- |

| UNDERRATED \#4 — Demarcation uncertainty:  The problem that a single EMA label ('cooking') is mapped onto 15 minutes of heterogeneous accelerometer data is mentioned in detail by only 2–3 of the seven reports, despite being a systematic source of label noise in any classifier trained on EMA labels. The ±15-minute window convention is used without critically examining how destructive this assumption can be. |
| :---- |

| UNDERRATED \#5 — Hybrid sampling designs:  Random prompts for background coverage \+ event-triggered prompts for specific episodes. This addresses the coverage-vs-precision tradeoff that pure random and pure triggered designs both handle poorly. Recommended in two reports, almost never implemented. |
| :---- |

| UNDERRATED \#6 — Compliance decay over study duration:  Compliance drops non-trivially over the first few days in event-triggered setups. Reporting a single overall compliance figure masks this. The temporal pattern of compliance matters for protocol design and data quality assessment. |
| :---- |

# **11\. Representative Studies and Datasets**

## **11.1 Validation / Feasibility Exemplars**

* Dunton et al. (2012, Frontiers Psych) — Adults, ActiGraph (hip), 8 random EMA prompts/day, 4 days. Canonical criterion validity demonstration; established ±15-min window convention; documented non-random missingness by activity level. Limitation: coarse EMA categories only.

* Maher et al. (2018, Frontiers Psych) — 104 older adults, activPAL (thigh), 6 random prompts/day × 10 days, 92% compliance. Best older-adult feasibility and criterion-validity study. Found post-prompt PA reduction (reactivity). Limitation: binary PA/SB EMA, no context items.

* Maher et al. (2020, PubMed) — Older adults, activPAL \+ intentions/self-efficacy EMA. EMA-measured intentions predicted subsequent sedentary behaviour (2-hour window). Demonstrates prospective explanatory role.

* Monnaatsie et al. (2024) — Shift/non-shift workers, ActiGraph \+ EMA at 3-hour intervals. Criterion validity in occupational populations. Limitation: broad EMA categories; no context items.

* devilSPARC / JMIR 2016 — 41 college students, ActiGraph GT3X+, 8 prompts/day, 4 days. Explicitly tested intensity label reliability; showed clear mismatch at light/moderate/vigorous levels. Cautionary exemplar.

## **11.2 Contextualisation Exemplars**

* Liao et al. (2015) — Adults, ActiGraph \+ EMA on where/with whom. Strong demonstration of EMA contextual role: PA/SB patterns vary by setting and social company. Information accelerometers cannot provide.

* Giurgiu et al. (2020) — Thigh-worn Move accelerometer \+ smartphone EMA triggered after 20 min continuous sitting. 82.77% trigger accuracy for prolonged sedentary bouts. 40% work-related; 57% not alone. Blueprint for sedentary-triggered EMA.

* Maher et al. (2021) — activPAL \+ EMA on social/physical context. Context stability predicts PA/SB patterns. Demonstrates EMA value for behavioural theory.

* Kracht et al. (2021, IJBNPA) — Adolescents, ActiGraph (hip), interval-based EMA, explicit 30-min pre-prompt linkage. Links sedentary bouts to indoor/alone context.

* Maes et al. (2023, JMIR Aging) — 64 older adults, Axivity AX3 (wrist), 6 prompts/day × 7 days. EMA determinants (emotions, fatigue, intention, self-efficacy) predict subsequent PA at 15/30/60/120 min. Clean temporal ordering.

## **11.3 Algorithm Development Exemplar**

* Sigcha et al. (2025, WEALTH study — preprint) — 589 participants, 7 days free-living, activPAL (thigh) \+ event-based EMA via HealthReact app, six PA categories. Up to 97% agreement with activPAL CREA for sitting/running; 32% for standing; 73.6% ML classifier accuracy. The current and only rigorous benchmark for EMA-based PA classification in free-living conditions. Treat as proof-of-concept, not established consensus.

## **11.4 Technical Validation Exemplar**

* Delobelle et al. (2024) — 37 adults \+ 32 older adults, Fitbit validated against ActiGraph GT3X+ (hip) \+ activPAL4 (thigh), 3 days. Fitbits detect stepping bouts with sensitivity/specificity \>87%/97%; prolonged sitting sensitivity \>93%, specificity \>89%. Validates the trigger layer needed for event-based EMA. Limitation: EMA not actually collected; validates the triggering mechanism only.

# **12\. Source Reliability Assessment**

The seven AI reports were not equally cautious or equally comprehensive. Knowing which sources to weight more heavily is important for interpreting this synthesis.

| Source | Relative Strength | Known Bias / Limitation |
| :---- | :---- | :---- |
| ChatGPT | Most conservative; correctly identifies domain variables as rarer than others suggest; best at aspirational-vs-actual distinctions | Least quantitative; vague on alignment strategies; shortest on specific study findings |
| ChatGPT Deep Research | Best systematic screening workflow; most rigorous inclusion/exclusion; most detailed study matrix; best on hybrid sampling designs | Comprehensiveness over sharp conclusions; 'what everyone does/doesn't do/should do' is good but less punchy |
| DeepSeek | Strongest on EMA variable tiering by utility vs burden; clearest 'must collect / avoid' lists; best on weak vs strong label framing | Slightly overoptimistic about current integration into modelling; some 'common practice' claims seem aspirational |
| Gemini | Most comprehensive overall (59KB); best on demarcation uncertainty and lag degradation; most detailed study analysis; 58 references | Most optimistic about EMA in HAR — occasionally frames early-stage findings as more established than they are; 'near-ground truth for algorithm training' framing is too generous |
| Kimi | Most concise; best inclusion/exclusion logic; clearest screening table; good at distinguishing adjacent from core studies | Shortest report; less detail on EMA variable analysis and best practices; some nuance lost |
| Opus 4.6 v1 (Scite) | Strongest integration of Sigcha et al. (2025); best label taxonomy (direct/weak/contextual/validation/error-analysis); clearest burden-value tradeoffs | Occasionally treats WEALTH as more representative than it is — it is the only example, not one of many |
| Opus 4.6 v2 (Scite) | Deepest on event-triggered methods and technical challenges; best on innovative approaches (audio micro-EMA, ACAI backfilling); most detailed study-by-study; best on HAR/EMA gap | Most optimistic overall — sometimes conflates what the field should do with what it has done; more forward-looking than grounded in current practice |

Key disagreement: Gemini and Opus 4.6 v2 are notably more optimistic about EMA's role in HAR algorithm training. The other five reports correctly characterise it as 'promising but thin' or 'weak supervision at best.' When reading claims about EMA's readiness for classifier training, weight the more cautious sources.

# **13\. Final Synthesis**

## **13.1 What Everyone Does**

* Collects EMA via smartphone apps with 4–10 random or fixed-interval prompts per day over 7–14 days.

* Asks about current activity type and location as primary EMA variables.

* Links EMA to accelerometry through explicit windowing rules — typically ±15 min around the prompt.

* Treats EMA primarily as a validation and contextualisation tool, not as training labels for classifiers.

* Reports overall EMA compliance (typically 70–92%) without detailed breakdown by activity type, time of day, or study day.

* Uses the activPAL for SB research (thigh placement), ActiGraph or Axivity for PA research (hip or wrist).

* Analyses accelerometer and EMA data mostly in parallel, not in an integrated pipeline.

## **13.2 What Everyone Does Not Do**

* Integrate EMA labels into machine learning pipelines (with the single exception of Sigcha et al. 2025).

* Use event-triggered EMA despite six of seven reports recommending it as superior.

* Collect device wear compliance as an EMA item — despite this being nearly free and highly valuable.

* Record and report prompt-response lag or use it to adjust temporal alignment.

* Handle missing EMA data rigorously — multiple imputation is virtually absent; listwise deletion is the default.

* Use EMA to systematically resolve the most important accelerometer ambiguities: domain, purpose, and type of sedentary behaviour.

* Distinguish between occupational and leisure sitting in analytical models — the most policy-relevant distinction in SB epidemiology.

* Report EMA content-validity justification — why specific items were chosen and what construct they measure.

* Publish integrated datasets combining raw accelerometer data with timestamped EMA responses.

## **13.3 What Everyone Should Do**

| The sharpest field-specific conclusion:  EMA's real utility in body-mounted accelerometer studies of physical activity and sedentary behaviour is not that it measures movement better than the accelerometer — it does not. Its utility is that it explains the movement record: what the behaviour was, what kind of sitting or activity it was, where and with whom it occurred, and what the person was experiencing or intending at the time. That makes it highly valuable for contextualisation, interpretation, and selective weak supervision — but only moderately valuable for dense activity classification unless the study is designed around that use from the start. |
| :---- |

* Define the purpose of EMA before data collection. Every item must have a pre-specified analytic role. If it does not appear in the analysis plan, remove it.

* For sedentary behaviour research: adopt sedentary-triggered EMA as standard practice. The evidence is clear, the technology is available, the payoff is large.

* For activity classification: adopt event-triggered EMA and treat resulting labels as weak supervision requiring noise-robust learning methods.

* Always collect: activity type, domain (work/leisure/transport/household), location, social context, and device wear status. These five items cover the greatest information gap between sensor and behaviour at minimal burden.

* Report alignment methods, response latency, compliance by day, and missingness analysis — not just overall compliance rates.

* Integrate EMA into modelling. The field's largest missed opportunity is collecting rich contextual data and never using it to improve classification, interpretation, or prediction.

* Use hybrid prompt designs: event-triggered for specific episodes of interest, random for representative background sampling.

* Invest in bridging the HAR and EMA research communities. Their convergence is the most promising methodological direction for free-living physical behaviour science.

# **Appendix: Quick-Reference Decision Table**

Use this table when designing the EMA component of a new body-mounted accelerometer PA/SB study.

| EMA Use Case | What It Adds | Key Limitation | Burden | Modelling Value | Verdict |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Activity type labelling(event-triggered) | Ecologically valid labels for ML training; resolves 'what is happening' | Standing labels unreliable (32%); compliance needed over time | Low (automated) | Very high | ✓ Adopt — best design for labelling |
| Activity type labelling(random prompts) | Coarse labels for validation; background coverage | Sparse; non-random missingness; temporal imprecision | Moderate | Moderate | ✓ Use as complement to triggered design |
| Sedentary-triggered EMA(domain/social/location) | Rich SB context during prolonged sitting; disambiguates sedentary heterogeneity | Technical infrastructure needed; time-out rules required | Low–moderate | Very high for SB | ✓ Adopt as standard for SB studies |
| Activity domain(work/leisure/transport/household) | Resolves biggest sensor ambiguity: why is this person sitting/walking? | Collected less than it should be; requires careful item design | Low | Very high | ✓ Always collect |
| Location \+ social context | Where and with whom — invisible to sensor; essential for SB interpretation | Categorical; may miss nuance | Low | High | ✓ Always collect |
| Device wear compliance('wearing the monitor?') | Distinguishes non-wear from sedentary; validates non-wear algorithms | Almost never done despite near-zero cost | Minimal | Very high for data quality | ✓ Always collect — no excuse not to |
| Affect/mood (2-item) | Antecedents/consequences of PA/SB; within-person dynamics | Low modelling value for classification; adds burden if not primary RQ | Low–moderate | High for process models; low for classification | ○ Include only when primary RQ |
| Determinants(intention, self-efficacy) | Predicts subsequent PA in JITAI-relevant time windows | Temporal ambiguity; causal direction unclear | Moderate | Moderate — JITAI applications | ○ Include for specific mechanistic RQs |
| Fine-grained intensity(light/moderate/vigorous) | Theoretically validates intensity classification | Demonstrably unreliable; accelerometers measure intensity better; degrades classifiers | Low | Negative for ML | ✗ Do not use as training labels |
| Perceived exertion | Subjective complement to objective intensity | Duplicates what the accelerometer already measures better | Low | Low | ✗ Not recommended |
| Long affect batteries(full PANAS etc.) | Rich psychological data | Compliance-degrading; rarely justified by analytic payoff | High | Low for PA classification | ✗ Replace with 2-item affect or remove |

*─── End of Document ───*

Synthesised April 2026 from seven independent AI deep-research runs across ChatGPT, ChatGPT Deep Research, DeepSeek, Gemini, Kimi, and Claude Opus (×2)