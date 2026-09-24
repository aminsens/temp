**Ecological Momentary Assessment in Body-Mounted Accelerometer Studies**

**Physical Activity and Sedentary Behaviour Research**

*A Definitive Cross-Model Synthesis*

Synthesised from seven independent AI deep-research runs (ChatGPT, ChatGPT Deep Research, DeepSeek, Gemini, Kimi, Claude Opus × 2\) | April 2026

# **1\. Executive Summary**

In body-mounted accelerometer studies of physical activity (PA) and sedentary behaviour (SB), Ecological Momentary Assessment (EMA) is not a measurement replacement but a complementary annotation layer. Its core value is contextual: it supplies what dedicated sensors cannot—the domain, purpose, social setting, and subjective meaning of movement.

Across seven independent AI deep-research runs applied to this narrow literature, the synthesis consistently converges on five conclusions:

* EMA is most valuable for behavioural disambiguation, contextualisation, and selective weak labelling—not as dense ground truth for fine-grained activity recognition.

* The strongest established use is criterion/convergent validation of broad activity categories (sitting vs. active) against concurrent accelerometer windows of ±15 minutes.

* Event-triggered (sensor-informed) EMA is methodologically superior to random prompting for activity labelling but remains uncommon in published literature.

* A persistent and damaging pattern: EMA data are collected, summarised descriptively, and then never integrated into modelling pipelines.

* Best practice requires brief, targeted protocols (4–6 items, 4–6 prompts/day) designed around a specific analytic function—not a general-purpose behavioural questionnaire.

# **2\. Scope Definition and Inclusion Logic**

This synthesis is strictly limited to studies meeting all three criteria simultaneously:

* Primary movement data from a dedicated body-mounted accelerometer device (ActiGraph, activPAL, Axivity, GENEActiv, SENS Motion, or equivalent research-grade wearable). Smartphone accelerometers are excluded.

* Research focus on physical activity, sedentary behaviour, posture/movement behaviour, activity classification, or free-living physical behaviour assessment.

* A concurrent EMA or near-equivalent momentary self-report component (experience sampling, ambulatory diary, prompted self-report) collected during the same monitoring period.

Excluded: smartphone sensing, physiological monitoring (HR, PPG, ECG, EEG), general digital phenotyping, rehabilitation biomechanics without PA focus, purely lab-based HAR without real-world generalisability discussion, generic mobile health studies.

The literature genuinely meeting this strict scope is smaller than one might expect. There is a solid body of behavioural/contextual and validation studies, but the subset that directly uses EMA for accelerometer-based algorithm development is still sparse. Sections below mark this explicitly.

# **3\. What EMA Contributes Beyond Body-Mounted Accelerometers**

## **3.1 The Fundamental Sensor Limitation**

Body-mounted accelerometers measure movement intensity, duration, frequency, and—when thigh-mounted—posture (sit/stand/step). The activPAL achieves ≥95% agreement with direct observation for total sedentary time. ActiGraph and GENEActiv devices classify activity intensity reliably. But no accelerometer, regardless of placement, can determine:

* What specific activity is occurring (TV watching vs. desk work during sitting)

* The behavioural domain (occupational, leisure, transport, household)

* The purpose of movement (exercise vs. commuting vs. household necessity)

* The social context (alone, with family, with colleagues)

* The physical environment (home, workplace, outdoors)

* Subjective states (affect, fatigue, perceived exertion, motivation, barriers)

* Intentionality (planned exercise vs. incidental movement)

## **3.2 How EMA Differs from Other Complementary Methods**

EMA occupies a distinct niche compared to alternative approaches used alongside accelerometers:

**Retrospective questionnaires (IPAQ, BRFSS, GPAQ):** Subject to recall bias and systematic overestimation. The IPAQ overestimates MVPA by \~900 min/week vs. accelerometry; EMA overestimates by only \~71 min/week, demonstrating far superior convergent validity.

**Time-use diaries (ACT24):** Higher temporal granularity but completed retrospectively and burdensome. EMA captures data closer to real time.

**Direct observation:** Gold standard for activity type and context but costly, invasive, and unscalable for long-term free-living studies.

**Video annotation:** High fidelity in laboratory settings but raises severe privacy concerns and generates enormous coding workloads—infeasible for multi-week free-living monitoring.

**Passive sensing:** Provides continuous, objective data but no subjective or contextual information. EMA adds the participant’s voice.

**Controlled labelling protocols:** Provide clean, unambiguous labels but fail to generalise to free-living conditions due to variability in real-world activity patterns.

## **3.3 What EMA Is in This Field**

Based on converging evidence across all seven research runs, EMA in body-mounted accelerometer PA/SB studies is best understood as serving multiple simultaneous roles:

* Contextual metadata: domain, location, social setting, purpose of accelerometer-detected behaviour

* Behavioural interpretation layer: explaining why a particular pattern of movement or non-movement occurred

* Near-ground truth for coarse activity categories: participant-reported labels of current/recent activity that—while imperfect—are the closest feasible approximation to ground truth in free-living conditions

* Subjective state capture: affect, fatigue, perceived exertion, motivation, and barriers that cannot be inferred from accelerometry

* Compliance and quality-control signal: confirming device wear, identifying non-wear periods, supporting data cleaning

* Weak label source for algorithm development: sparse, noisy, but ecologically valid labels for training or validating activity recognition models

EMA is NOT ground truth in the strict machine learning sense. EMA responses are subject to self-report bias, temporal imprecision, and missingness. However, in free-living conditions where direct observation is infeasible, EMA represents the most practical source of contextual and activity-type information.

# **4\. How EMA Is Used in PA/SB Studies**

## **4.1 Validation of Momentary Activity and Sitting Reports**

This is the most established use. Multiple studies demonstrate that EMA-reported activity categories align with concurrent accelerometer-derived behaviour in windows around prompts (±15 minutes). Key findings:

* Dunton et al. (2012): EMA-reported PA corresponded to higher MVPA; EMA-reported SB corresponded to higher sedentary counts in adults.

* Maher et al. (2018): In older adults with activPAL, ‘physical activity/exercising’ EMA reports aligned with higher device-measured activity; sitting reports aligned with higher sedentary time. 92% EMA compliance over 10 days.

* Monnaatsie et al. (2024): In shift workers, EMA-reported PA associated with significantly higher ActiGraph CPM (β=1184) and steps (β=20.9) than sitting reports.

* JMIR 2016 (devilSPARC): Validated intensity self-report vs. ActiGraph windows—found reliable agreement at the coarse binary level (sedentary/not), but clear mismatch at fine-grained intensity levels (light/moderate/vigorous).

Evidence quality: STRONG for coarse (sitting/active) distinctions. WEAK for fine-grained intensity self-classification.

## **4.2 Contextualising Where and With Whom Behaviour Happens**

EMA is used extensively to add location, social, and environmental context to accelerometer-measured behaviour. Liao et al. (2015) showed home was the dominant context for PA/SB in adults; activities frequently occurred alone; setting mattered for MVPA patterns. Kracht et al. (2021) linked prior sedentary time to being indoors or alone in adolescents. Without EMA, these distinctions are invisible to the sensor.

## **4.3 Interpreting Sedentary Behaviour Domains**

EMA is especially valuable for SB because ‘sedentary time’ is behaviourally heterogeneous. Device-detected sitting could be work, meetings, TV, reading, meals, or transport. Maher et al. (2018) showed differences across domain-specific sitting activities. Hevel et al. (2021) demonstrated that affect during sedentary behaviour depended on social and physical context. Giurgiu et al. (2020) found 40% of prolonged sedentary bouts occurred at work, 57% while not alone—invisible to the sensor.

Evidence quality: STRONG for the value of domain/context distinctions. INCONSISTENT for specific health-outcome differences between domains.

## **4.4 Capturing Momentary Psychology as Antecedents/Consequences**

A distinct family of studies uses EMA to measure time-varying determinants (affect, fatigue, intention, self-efficacy), then models accelerometer-derived PA in the minutes/hours after prompts. Maher et al. (2020) showed EMA-measured intentions and self-efficacy predicted subsequent activPAL-measured sedentary behaviour (2-hour window). Maes et al. (2023) found irritation, feeling down, high intention, and self-efficacy positively associated with subsequent PA at 15–120 minutes post-EMA.

Evidence quality: MODERATE. Temporally ordered but causal direction remains uncertain.

# **5\. Role of EMA in Labelling, Validation, and Algorithm Development**

## **5.1 EMA as a Direct Label Source (Emerging, Thin Evidence)**

The WEALTH study (Sigcha et al., 2025 preprint) presents the clearest exemplar: thigh-worn activPAL data integrated with event-based EMA across 589 participants over 7 days. EMA responses synchronised with accelerometer signals created a sparse labelled dataset. Key results:

* Up to 97% agreement with activPAL CREA ground-truth for sitting and running labels

* Only 32% agreement for standing (incidental, frequently unnoticed by participants)

* Machine learning classifier trained on EMA labels achieved up to 73.6% classification accuracy

This demonstrates that event-based EMA can generate ecologically valid labels for activity recognition—an advance over laboratory-only training data. However, this is a preprint and should not yet be treated as field consensus.

## **5.2 EMA as Weak Supervision**

More commonly, EMA provides what should be characterised as ‘weak labels’—self-reported activity types that are temporally imprecise, subject to bias, and available only at discrete time points rather than continuously. Best practice in modelling treats these as probabilistic/uncertain labels rather than gold standard, using:

* Noise-robust loss functions

* Semi-supervised or self-supervised learning leveraging unlabelled accelerometer data

* Confidence-weighted label propagation

* Threshold-based selection (retain only high-agreement EMA-sensor pairs)

## **5.3 Common Modelling Uses**

**Validated/established:** Criterion validity comparison of EMA activity categories against accelerometer windows (±15 min). Context stratification of accelerometer-derived behaviour. Within-person multilevel modelling of antecedents/consequences.

**Common practice:** Descriptive analysis of EMA-reported context alongside accelerometer summary statistics. EMA as a data-cleaning and wear-time validation aid.

**Thin/emerging:** EMA as direct training labels for continuous free-living activity classifiers. Semi-supervised or active learning using sparse EMA labels.

**Essentially absent:** Treating EMA as dense ground truth for fine-grained multi-class HAR. Feedback loops where classifier uncertainty triggers targeted EMA prompts (active learning).

## **5.4 Does the Literature Integrate EMA into Modelling?**

No—not adequately. The dominant pattern across the literature is collection without integration: EMA is gathered, summarised in a descriptive table, and then the accelerometer analysis proceeds independently. This is both a scientific waste and, where participant burden is high, an ethical concern. The field collects EMA as if it were a parallel questionnaire study rather than a structured annotation layer.

# **6\. Common EMA Variables Collected**

## **6.1 Variable Inventory and Assessment**

| Variable | Frequency | Utility for Accel. Research | Burden | Recommendation |
| :---- | :---- | :---- | :---- | :---- |
| Current activity type (sitting, walking, running) | Very common | High – core labelling variable | Low | Essential |
| Location (home, work, outdoors, vehicle) | Common | High – domain discrimination | Low | Essential |
| Social context (alone, with others) | Common | High – SB interpretation | Low | Essential |
| Activity domain (work/leisure/transport/household) | Moderate | Very high – resolves biggest sensor ambiguity | Low | Strongly recommended |
| Affect/mood (valence, arousal) | Moderate | Moderate – antecedents/consequences | Low-moderate | Include when primary RQ |
| Fatigue | Moderate | High in clinical/older populations | Low | Include for specific populations |
| Indoor/outdoor | Moderate | Moderate – environmental context | Low | Include when relevant |
| Perceived exertion | Rare | Low – duplicates accelerometer intensity | Low | Not recommended generally |
| Purpose of movement (exercise/transport/household) | Rare | Very high – intentionality distinction | Moderate | Collect when feasible |
| Barriers/motivation | Rare | Low for classification; moderate for intervention | High | Only for intervention studies |
| Device wear compliance ('Are you wearing it?') | Very rare | Very high – critical for data quality | Minimal | Always include |
| Pain/symptoms | Rare | High in clinical populations only | Moderate | Condition-specific use only |
| Intention/self-efficacy | Rare | Moderate – temporal alignment difficult | Moderate | Only for specific mechanistic RQs |

## **6.2 What Is Scientifically Attractive but Operationally Weak**

* Fine-grained intensity self-classification (light/moderate/vigorous): Theoretically attractive but empirically unreliable. The devilSPARC validation study demonstrated clear mismatch at these levels. Accelerometers measure intensity better than humans self-report it.

* Open-ended text responses: Rich but unscalable for large datasets and demanding for participants.

* Very long batteries (\>15 items): Cause prompt fatigue, reduced compliance, and reactive behaviour change.

* Intention/motivation at moment of behaviour: Temporal alignment between when intention is measured and when the behaviour occurs makes causal inference difficult.

# **7\. Methodological Challenges Linking EMA to Accelerometer Data**

## **7.1 The Core Problem**

Accelerometers produce dense, continuous numerical vectors at high sampling rates (25–100 Hz), generating millions of data points per day. EMA produces sparse, discrete, categorical, and temporally fuzzy labels—4–10 per day. Aligning these modalities is the central methodological challenge of the field.

## **7.2 Specific Challenges**

**Timestamp alignment and prompt-response lag:** When EMA prompts are delivered, participants rarely answer immediately. A 5-minute average response delay is documented (IJBNPA 2021 adolescent study). Each additional minute of lag reduces the probability of accurate behaviour confirmation—one sensor-triggered EMA study in older adults found a 20% decrease in odds of correct confirmation per minute of delay. Many studies fail to record both prompt delivery and response timestamps, making it impossible to correct for this.

**Recall window mismatch:** EMA items asking about ‘right now’ vs. ‘the past 30 minutes’ vs. ‘since the last prompt’ create fundamentally different temporal alignment problems. Studies inconsistently mixing recall frames within the same protocol create structural disagreements with accelerometer data.

**Event duration mismatch:** A prompt captures a snapshot; activities have duration. Linking the label ‘cooking’ to 15 minutes of highly heterogeneous accelerometer data (walking, standing, sitting, arm movement) confuses classifiers and injects noise.

**Sparse labels vs. dense time series:** Even with 8 prompts/day and perfect compliance, \>98% of accelerometer data remains unlabelled. Most studies either discard this unlabelled data (wasteful) or assume label persistence between prompts (inaccurate).

**Non-random missingness:** Participants are significantly less likely to respond during vigorous activity, driving, intense social situations, or when the phone is not carried. This creates systematic bias: the labelled dataset underrepresents high-intensity and context-specific activities. Dunton et al. (2012) found evidence of this in adults; missing EMA correlated with higher MVPA for some subgroups.

**Self-report bias:** Social desirability, difficulty categorising ambiguous activities, and individual differences in activity perception all affect label quality. Light-intensity activities and SB are most susceptible—precisely where accelerometers themselves are weakest.

## **7.3 Alignment Strategies and Evidence for Their Effectiveness**

**Fixed symmetric window (±15 min around prompt):** STRONG evidence. Most common in validation literature. Works well when EMA asks about ‘right now’ or ‘just before the beep’. Most studies use this.

**Pre-prompt window (30–60 min before prompt):** MODERATE evidence. Used when EMA assesses antecedents to concurrent behaviour. Clear conceptual justification; used in Kracht et al. (2021), Maes et al. (2023).

**Post-prompt window (15–120 min after prompt):** MODERATE evidence. Used when EMA measures determinants and accelerometer-derived PA is the subsequent outcome. Conceptually clean for prediction/JITAI but vulnerable to confounding.

**Event-triggered alignment:** STRONGEST for sedentary behaviour and targeted episodes. Accelerometer detects a specific state (e.g., 20+ minutes sitting), triggers EMA during it. Eliminates recall error and improves temporal alignment. Giurgiu et al. (2020) achieved 82.77% accuracy for capturing prolonged sedentary bouts. Not yet mainstream.

**Dual-timestamp recording:** Theoretically strongest. Record both prompt delivery time and response submission time; use the prompt timestamp for alignment. Rarely implemented in published studies.

# **8\. Common Weaknesses and Blind Spots**

Convergent finding across all seven research runs: these weaknesses appear with remarkable consistency.

## **8.1 Collection Without Integration**

The most damning pattern: EMA data are collected, summarised in a descriptive table, and then the accelerometer and EMA analyses proceed in parallel—never integrated. Studies invest substantial participant burden collecting context they never use for modelling or classification.

## **8.2 No Item Content Validity**

A systematic review of EMA studies on PA/SB (IJBNPA content validity review, Liao et al. 2018\) found that no reviewed study explicitly reported assessing EMA item content validity, most gave little rationale for prompt design, only one reported response latency, and no study reported backfilling. This is a field-level failure.

## **8.3 Poor Missing Data Handling**

Most studies use complete-case analysis (listwise deletion) without testing whether missingness is systematic. When it is—and the evidence suggests it often is—biased estimates result. Multiple imputation or inverse probability weighting is feasible but rarely used.

## **8.4 Weak Temporal Alignment Reporting**

How EMA timestamps were matched to accelerometer epochs is frequently undescribed. Studies state data were ‘collected concurrently’ without specifying window sizes, prompt-response lag handling, or conflict-resolution rules for mismatched labels.

## **8.5 Underuse for Sedentary Behaviour Interpretation**

Despite the well-recognised limitation that accelerometers cannot distinguish between types of sedentary behaviour, EMA is rarely used systematically to characterise the context and type of sedentary episodes. The field measures sedentary duration well but interprets sedentary meaning poorly.

## **8.6 Redundant Items That Duplicate Accelerometer Data**

Studies frequently collect EMA items that accelerometers already measure better—perceived exertion, duration estimates, step counts—while omitting items that add genuine information—domain, purpose, intentionality. This reflects a misunderstanding of EMA’s unique value proposition.

## **8.7 Underuse of Event-Triggered EMA**

Random or fixed-interval prompting dominates, despite the clear advantages of sensor-triggered prompting for temporal alignment and contextual relevance. Technical complexity and the lack of established open-source tools remain barriers, but the methodological evidence strongly favours triggered designs for activity labelling and SB interpretation.

## **8.8 Failure to Report Prompt-Response Lag**

Even when both prompt and response timestamps are recorded (rare), they are rarely reported or used in analysis. This silence obscures a systematic source of temporal misalignment.

# **9\. Best-Practice Recommendations**

Based on converging evidence across all seven research runs, the following recommendations represent the current methodological standard for this field.

## **9.1 For Physical Activity Classification**

* Use event-triggered EMA: prompts fired when the accelerometer detects an activity transition. This maximises temporal precision and contextual relevance.

* Collect activity type with 6–8 structured options (sitting, standing, walking, running, cycling, stair-climbing, other)—not free text, not fine-grained intensity categories.

* Record both prompt delivery and response timestamps; discard or downweight responses with \>10-minute lag.

* Treat EMA labels as weak supervision: use noise-robust ML methods, not traditional supervised learning assuming clean labels.

* Do not use EMA intensity self-classification (light/moderate/vigorous) as training labels—this is demonstrably unreliable.

* For training data, combine event-triggered prompts (for specific episodes) with periodic random prompts (for representativeness).

## **9.2 For Sedentary Behaviour Interpretation**

* Use a thigh-worn posture-capable monitor (activPAL) as primary SB device; hip/wrist accelerometers cannot distinguish sitting from standing.

* Use sedentary-triggered EMA: prompt after 20–30 minutes of continuous sitting. This efficiently concentrates data collection on the most relevant episodes.

* Collect: social context (alone/with whom), domain (work/leisure/transport/household), primary activity while sedentary (TV, computer, eating, reading, meetings). These three items resolve most interpretive ambiguity.

* Keep the EMA survey very brief (\<5 items, \<30 seconds) since sitting episodes are frequent and long batteries cause rapid fatigue.

* Report accuracy of triggered prompts relative to total eligible sedentary bouts.

## **9.3 For Context-Aware Behaviour Analysis**

* Use time-based random-within-window prompting (5–6 prompts/day) to support within-person inference across waking hours.

* Core items: domain, social context, location, indoor/outdoor. These four variables capture the highest-value context at minimal burden.

* Add affect (2-item: valence \+ arousal) only when emotional antecedents/consequences are a primary research question.

* Use pre-prompt windows (30 minutes before) for association analyses; use post-prompt windows (15–120 minutes after) for prediction/JITAI logic.

* Explicitly specify and pre-register the accelerometer linkage window before data collection.

## **9.4 For Multimodal Algorithm Development**

* Design EMA protocols with algorithm development as an explicit design goal—not a secondary data source.

* Hybrid sampling: event-triggered prompts for activity episodes of interest \+ random prompts for background coverage.

* Use EMA as contextual features (domain, social, location) and as weak labels for targeted windows, not as a blanket ground-truth stream.

* Invest in larger samples (hundreds of participants) to provide sufficient labelled examples across activity categories.

* Validate EMA labels against a reference algorithm (e.g., activPAL CREA) or direct observation on a subsample before using them for training.

* Consider publishing anonymised linked datasets: EMA-labelled accelerometer data are a valuable public good for the field.

## **9.5 Universal Requirements**

* Always collect a device wear compliance item (‘Are you wearing the accelerometer?’). This single item dramatically improves data quality by enabling valid non-wear identification.

* Limit total EMA to 4–6 prompts/day for studies \>7 days; 6–8 for shorter, intensive protocols.

* Keep each survey to \<3 minutes (typically 5–10 items).

* Report: prompt schedule, compliance rate by day and participant, response latency distribution, missingness pattern analysis, and the exact linkage rule used to connect EMA to accelerometer windows.

* Pre-specify all linkage windows before data collection. Do not fit windows post-hoc to optimise associations.

# **10\. Representative Studies and Datasets**

## **10.1 Validation/Feasibility Exemplars**

**Dunton et al. (2012) – Frontiers in Psychology:** Adults, ActiGraph (hip), 8 random EMA prompts/day for 4 days. One of the clearest demonstrations that EMA-reported broad activity categories map onto concurrent accelerometer behaviour (±15 min window). Established EMA as a feasible coarse momentary activity report. Limitation: coarse categories; non-random missingness by activity level.

**Maher et al. (2018) – Frontiers in Psychology:** 104 older adults, activPAL (thigh), 6 random EMA prompts/day for 10 days. Best older-adult feasibility and criterion-validity study. 92% compliance. Found small post-prompt PA reduction (reactivity). Limitation: binary PA/SB EMA, no context items.

**JMIR 2016 (devilSPARC):** 41 college students, ActiGraph GT3X+, 8 prompts/day for 4 days. Explicitly tested intensity-label reliability—showed clear mismatch for light/moderate self-classifications. Cautionary exemplar: do not use EMA intensity labels as ground truth.

**Monnaatsie et al. (2024):** Shift and non-shift workers, ActiGraph \+ EMA at 3-hour intervals. Recent criterion validity evidence in occupational populations. Supports EMA-accelerometer convergence but reinforces the same conclusions as earlier studies.

## **10.2 Contextualisation Exemplars**

**Liao et al. (2015) – ResearchGate:** Adults, ActiGraph \+ EMA on where/with whom. Strong demonstration of EMA’s contextual role: PA/SB patterns vary meaningfully by setting and social company—information accelerometers cannot provide.

**Giurgiu et al. (2020):** Thigh-worn Move accelerometer \+ smartphone EMA triggered after 20 minutes of continuous sitting. Framework for sedentary-triggered EMA: 82.77% trigger accuracy for prolonged sedentary bouts vs. simulated random sampling capturing up to 47.9% fewer relevant bouts. 40% of prolonged bouts were work-related; 57% occurred while not alone.

**Maher et al. (2021) – PubMed:** activPAL \+ EMA on social/physical context. Tested whether context stability predicts PA/SB—more stable physical contexts for PA predicted more MVPA. Demonstrates EMA’s value for behavioural theory and adaptive interventions.

## **10.3 Algorithm Development Exemplar**

**Sigcha et al. (2025) – WEALTH Study (preprint):** 589 participants, 7 days, activPAL (thigh) \+ event-based EMA via HealthReact app. Most rigorous demonstration of EMA as a free-living PA labelling framework. Six PA categories; up to 97% agreement with activPAL CREA for sitting/running; only 32% for standing. ML classifier trained on EMA labels achieved up to 73.6% accuracy. Limitations: preprint status; activity-dependent label quality; compliance variability across participants. Despite limitations, this is the current benchmark for EMA-based activity classification.

## **10.4 Determinant Modelling Exemplars**

**Maher et al. (2020):** Older adults, activPAL \+ intentions/self-efficacy EMA. EMA-measured intentions predicted sedentary behaviour in the subsequent 2 hours. Demonstrates EMA’s prospective explanatory value—but less directly useful for activity classification.

**Maes et al. (2023):** Older adults, Axivity AX3 (wrist) \+ 6 time-based EMA prompts/day. Emotions, fatigue, intention, self-efficacy as EMA predictors of accelerometer-derived PA at 15/30/60/120 minutes post-prompt. Clean temporal ordering; demonstrates JITAI potential.

# **11\. Final Synthesis**

## **11.1 What Everyone Does**

* Collects EMA via smartphone apps with 4–10 random or fixed-interval prompts per day over 7–14 days.

* Asks about current activity type and location as primary EMA variables.

* Links EMA to accelerometry through explicit windowing rules (typically ±15 min around the prompt).

* Treats EMA primarily as a validation and contextualisation tool, not as training labels for classifiers.

* Reports high overall compliance rates (typically 70–92%) without detailed breakdown by activity type, time of day, or day-of-study.

* Uses the activPAL for SB research (thigh placement), ActiGraph or Axivity for PA research (hip or wrist).

* Analyses accelerometer and EMA data mostly in parallel, not in an integrated pipeline.

## **11.2 What Everyone Does Not Do**

* Integrate EMA labels into machine learning pipelines (with very few exceptions—Sigcha et al. 2025 being the clearest).

* Use event-triggered EMA despite its clear methodological advantages for temporal alignment and contextual targeting.

* Collect device wear compliance as an EMA item, even though it costs almost nothing and dramatically improves data quality.

* Report prompt-response lag or use it to adjust temporal alignment.

* Handle missing EMA data rigorously—multiple imputation is virtually absent; listwise deletion is the default.

* Use EMA to systematically resolve the most important accelerometer ambiguities: domain, purpose, and type of sedentary behaviour.

* Distinguish between occupational and leisure sitting in analytical models, despite this being the most policy-relevant distinction in SB epidemiology.

* Report EMA content-validity justification—why specific items were chosen and what construct they are measuring.

* Publish integrated datasets combining raw accelerometer data with timestamped EMA responses.

## **11.3 What Everyone Should Do**

The sharpest field-specific conclusion from this synthesis:

EMA’s real utility in body-mounted accelerometer studies of physical activity and sedentary behaviour is not that it measures movement better than the accelerometer. It does not. Its utility is that it explains the movement record: what the behaviour was, what kind of sitting or activity it was, where and with whom it occurred, and what the person was experiencing or intending at the time. That makes it highly valuable for contextualisation, interpretation, and selective weak supervision, but only moderately valuable for dense activity classification unless the study is designed around that use from the start.

* Define the purpose of EMA before data collection. Every item should have a pre-specified analytic role. If an item does not appear in the analysis plan, remove it.

* For sedentary behaviour research: adopt sedentary-triggered EMA as standard practice. The evidence base is clear, the technology is available, and the payoff is large.

* For activity classification: adopt event-triggered EMA and treat resulting labels as weak supervision requiring noise-robust learning methods.

* Always collect: activity type, domain (work/leisure/transport/household), location, social context, and device wear status. These five items cover the greatest information gap between sensor and behaviour at minimal burden.

* Report alignment methods, response latency, compliance by day, and missingness analysis—not just overall compliance rates.

* Integrate EMA into modelling. The field’s single largest missed opportunity is the collection of rich contextual data that is then never used to improve classification, interpretation, or prediction.

* Combine triggered and random prompts in a hybrid design: triggered for specific episodes of interest, random for representative background sampling.

* Collaborate across the HAR and EMA literatures. These communities have developed largely in parallel; their convergence is the most promising direction for free-living physical behaviour science.

# **Appendix: Quick-Reference Summary Table**

| EMA Use | What It Adds | Key Limitations | Burden | Modelling Value | Recommendation |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Activity type labelling (current activity) | Direct labels for classification; identifies what participant is doing | Self-report bias; temporal imprecision; sparse vs. dense accel. data | Low | High if event-triggered; moderate if random | Essential – core variable for all studies |
| Domain classification (work/leisure/transport/household) | Resolves the single largest sensor ambiguity: why movement occurs | Subjective; categories may overlap; rarely collected systematically | Low | Very high | Strongly recommended |
| Social context (alone/with others) | Explains SB patterns; informs intervention targeting; invisible to sensor | Categorical only; may be sensitive | Low | Moderate-high | Include as standard |
| Location (home/work/outdoor/vehicle) | Separates occupational from leisure behaviour | Indoor/outdoor GPS unreliable indoors; requires self-report | Low | High | Include as standard |
| Device wear compliance | Distinguishes non-wear from sedentary; critical data quality check | Almost never collected despite minimal cost | Minimal | Very high for data quality | Always include |
| Affect/mood (valence \+ arousal) | Links PA/SB to psychological states; antecedent/consequence modelling | Not useful for activity classification; adds burden if not primary RQ | Low-moderate | High for process models; low for classification | Include only when primary RQ |
| Sedentary-triggered EMA (context during prolonged sitting) | Rich SB context efficiently sampled during relevant episodes | Technical complexity; requires real-time accel. processing | Low-moderate | Very high for SB research | Adopt as standard for SB studies |
| Event-triggered activity labelling (WEALTH framework) | Temporally precise, ecologically valid labels for ML training | Infrastructure needed; compliance drops over time; activity-dependent accuracy | Low (automated) | Very high | Adopt for algorithm development |
| Fine-grained intensity self-report (light/moderate/vigorous) | Theoretically validates accelerometer intensity classification | Demonstrably unreliable; accelerometers measure intensity better | Low | Low to negative (degrades classifiers) | Do not use as labels |
| Fatigue/pain/symptoms | Contextualises limitations on activity; clinically relevant | Condition-specific; adds burden in general samples | Moderate | Moderate in clinical populations | Use in clinical or older adult studies |
| Purpose/intentionality of movement | Separates exercise from incidental activity—theoretically important | Difficult to operationalise momentarily; recall alignment complex | Moderate | Moderate if implemented well | Collect when research question requires it |
| Perceived exertion | Validates intensity classification in theory | Duplicates accelerometer data; difficult to assess mid-activity | Low | Low | Not recommended generally |

*End of Synthesis Document*

Produced April 2026 | Based on seven independent AI deep-research runs across ChatGPT, ChatGPT Deep Research, DeepSeek, Gemini, Kimi, and Claude Opus