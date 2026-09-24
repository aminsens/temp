I'll conduct a systematic investigation of this specific intersection. Let me begin with targeted literature searches across the key dimensions you've outlined.
Let me search for more specific methodological and technical literature regarding algorithm development, activity classification, and temporal alignment challenges.
Let me search for more specific methodological literature on weaknesses, best practices, and the specific content of EMA assessments in this field.
Let me search for final specific details on best practices, representative datasets, and wear-time compliance issues.
Based on my systematic review of the literature, here is the comprehensive, research-grade investigation you requested.

---

## 1. Executive Summary

In body-mounted accelerometer studies of physical activity (PA) and sedentary behaviour (SB), Ecological Momentary Assessment (EMA) serves a dual function: it provides **contextual metadata** that sensors cannot capture (domain, purpose, social environment) and offers a **pragmatic labelling mechanism** for free-living activity recognition algorithms. However, the field suffers from a critical disconnect—EMA is frequently collected but poorly integrated into analytical workflows, often treated as supplementary rather than structural.

The current state reveals three patterns:
- **What everyone does**: Collects EMA via smartphone prompts (random or event-triggered), asks about current activity type and location, and uses a ±15-minute window to link sparse self-reports to dense accelerometer streams.
- **What everyone does not do**: Rigorously validate EMA labels against sensor data before using them as ground truth, report detailed compliance rates by device wear-time, or leverage EMA to resolve ambiguity in sedentary behaviour classification.
- **What everyone should do**: Adopt event-triggered (sensor-informed) EMA protocols that prompt based on detected activity transitions, use EMA primarily for behavioural domain classification rather than intensity quantification, and implement formal data-selection thresholds to balance label accuracy against data volume.

---

## 2. Scope Definition and Inclusion Logic

This synthesis strictly encompasses studies meeting four criteria:
1. **Body-mounted accelerometers** as primary movement sensors (ActiGraph, activPAL, GENEActiv, Axivity, SENS Motion); explicit exclusion of smartphone accelerometry unless used solely as an EMA delivery platform.
2. **Free-living data collection**; exclusion of purely laboratory-based motion recognition unless directly informing real-world protocol design.
3. **Concurrent EMA/self-report** capturing momentary or near-momentary behavioural states via mobile apps, diaries, or prompted surveys.
4. **Physical activity or sedentary behaviour focus**; exclusion of studies where physiological monitoring (HR, PPG, EEG) is the primary endpoint unless accelerometer-based PA/SB is the context.

The literature spans validation studies (comparing EMA to accelerometer counts), feasibility studies (compliance and burden), and—critically—emerging algorithmic work using EMA as weak labels for machine learning.

---

## 3. What EMA Contributes Beyond Body-Mounted Accelerometers

Body-mounted accelerometers quantify movement magnitude and pattern but remain **contextually blind**. EMA addresses five specific gaps:

**A. Behavioural Domain Classification**  
Accelerometers detect sitting but cannot distinguish occupational sitting from leisure screen-time. EMA captures domain (work, transport, household, leisure) and purpose (productive vs. recreational), which are essential for health-risk stratification given that occupational and leisure sedentary time have differential metabolic associations .

**B. Posture and Activity Type Clarification**  
While thigh-worn devices (activPAL) distinguish sitting/standing/stepping, hip/wrist-worn devices (ActiGraph, GENEActiv) struggle with posture classification. EMA self-reports of "sitting," "standing," or "walking" provide criterion validity checks, particularly for wrist-worn devices where classification accuracy for sedentary behaviour drops substantially compared to thigh-worn monitors .

**C. Social and Environmental Context**  
EMA captures location (home, work, outdoors), indoor/outdoor status, and social context (alone vs. with others/family/friends). This is scientifically critical: adolescents exhibit significantly more sedentary time when alone and indoors compared to when with others or outdoors , a nuance invisible to accelerometer data alone.

**D. Compliance and Wear-Time Validation**  
EMA reports of "not wearing the device" allow researchers to validate non-wear algorithms. Studies show 10–15% of EMA responses occur during confirmed non-wear periods, providing direct validation of accelerometer wear-time classification .

**E. Intentional vs. Incidental Activity Distinction**  
Accelerometers measure movement but not intentionality. EMA items querying "why are you doing this activity" (exercise vs. transport vs. household necessity) enable separation of purposeful exercise from incidental activity, crucial for behaviour-change interventions .

---

## 4. How EMA Is Used in Physical Activity and Sedentary Behaviour Studies

### 4.1 Prompting Strategies

The literature reveals three dominant EMA architectures:

**Random Signal-Contingent Sampling**  
Prompts delivered at random intervals (e.g., every 2 hours during waking time) to sample representatively across contexts. Common in early feasibility studies but prone to missing sporadic high-intensity activities .

**Event-Triggered (Sensor-Informed) Sampling**  
Prompts triggered by accelerometer-detected events (e.g., >30 minutes sedentary time, walking bout detected). This approach concentrates data collection during behaviourally relevant moments, reducing participant burden while maximizing contextual coverage .

**End-of-Day Retrospective**  
Single-item daily queries (e.g., "Did you exercise today?") minimizing burden but sacrificing temporal precision. Valid for detecting exercise days vs. non-exercise days over long periods (mean 323 days in one study), but poor for bout-level analysis .

### 4.2 Temporal Linkage Conventions

The field standardizes accelerometer-EMA linkage using **fixed windows**:
- **±15 minutes** surrounding the EMA prompt is the most common window for concurrent validity analysis .
- **30 minutes prior** to the prompt is frequently used to examine antecedents of behaviour (e.g., affect preceding sedentary bouts) .

### 4.3 Integration with Device Data

Studies typically merge datasets at the **epoch level** (15-second to 60-second epochs) using timestamp matching. Recent work emphasizes the necessity of automated temporal alignment algorithms to correct clock drift between devices, using cross-correlation of acceleration signals to synchronize timestamps before analysis .

---

## 5. Role of EMA in Labelling, Validation, and Algorithm Development

### 5.1 EMA as Ground Truth vs. Weak Labels

The literature reveals a tension: EMA is often treated as **ground truth** for activity type, yet validation studies show only **fair to moderate agreement** with accelerometer-derived classifications.

- **Sitting**: Moderate accuracy (~63.5% agreement with thigh-worn activPAL algorithms) .
- **Walking/Running**: Higher accuracy (~74–83% agreement) due to distinct acceleration signatures .
- **Standing**: Poor accuracy (~44%), frequently confused with walking or sports .
- **Cycling**: Poor accuracy (~50%), problematic due to device placement variability and algorithmic ambiguity in ground truth .

EMA should therefore be conceptualized as **near-ground truth** or **weak labels**—useful for training supervised learning models but requiring threshold-based refinement to exclude low-confidence alignments.

### 5.2 Algorithm Development Workflows

Recent frameworks (e.g., the WEALTH study) propose systematic integration:

1. **Event-Based Triggering**: Fitbit detects walking/sedentary bout → EMA prompt sent → participant reports activity type.
2. **Temporal Alignment**: EMA timestamp matched to accelerometer segment.
3. **Threshold-Based Selection**: Data retained only if EMA report matches accelerometer prediction (e.g., CREA algorithm) with ≥50% confidence.
4. **Sparse Labelling**: Resulting dataset contains high-confidence labels for specific activities (sitting, walking, running) but remains sparse, requiring semi-supervised or transfer learning approaches for model training .

### 5.3 Validation Applications

EMA serves validation through:
- **Concurrent Validity**: Comparing EMA-reported PA/SB against accelerometer counts in ±15-minute windows. Correlations range from r=0.27–0.31 for PA/SB, indicating modest but significant agreement .
- **Criterion Validity**: Using direct observation or video annotation as gold standard, with EMA serving as the intermediate validation layer for free-living studies where direct observation is impossible .

---

## 6. Common EMA Variables Collected in This Literature

| Variable Category | Specific Items | Prevalence | Scientific Utility | Burden |
|-------------------|----------------|------------|-------------------|---------|
| **Current Activity** | "What are you doing now?" (Sitting, Standing, Walking, Running, Sports, Cycling) | Very High | High for classification; moderate for SB interpretation | Low |
| **Activity Domain** | Work, Leisure, Transport, Household | Moderate | High for health-risk stratification | Low |
| **Location Context** | Home, Workplace, Outdoors, Vehicle | Moderate | High for environmental contextualization | Low |
| **Social Context** | Alone vs. With others (family/friends/colleagues) | Moderate | High for understanding social facilitation | Low |
| **Posture** | Sitting, Lying, Standing | High (in SB studies) | Critical for thigh-worn validation | Low |
| **Affect/Mood** | Energetic, Tired, Happy, Stressed | Moderate | High for behavioural prediction; weak for classification | Moderate |
| **Purpose/Intention** | Exercise, Transport, Work, Recreation | Low | High for behaviour-change interventions | Moderate |
| **Device Wear** | "Are you wearing the monitor?" | Low | Critical for compliance validation; rarely collected | Low |
| **Fatigue/Pain** | VAS scales | Low (clinical populations) | Contextual but not generalizable | High |
| **Barriers/Motivation** | Perceived barriers, self-efficacy | Low | Useful for EMI but rare in pure assessment studies | High |

**Key Finding**: Studies consistently over-collect affective variables (mood, stress) and under-collect **device wear validation** and **purpose/intention** data, despite the latter being more valuable for algorithmic discrimination between activity domains .

---

## 7. Methodological Challenges in Linking EMA to Accelerometer Data

### 7.1 Temporal Alignment Issues

**Clock Drift**: Independent device clocks (accelerometer vs. smartphone) drift over days, creating misalignment. Solutions require cross-correlation of acceleration signals to synchronize timestamps, with residuals typically <1 second after correction .

**Prompt-Response Lag**: Participants rarely respond instantly. A 5-minute delay is common, yet studies often treat the response timestamp as ground truth for the preceding window, introducing misclassification .

**Recall Window Mismatch**: Retrospective EMA ("What did you do in the last 30 minutes?") conflicts with the momentary nature of accelerometer epochs. Event-triggered EMA reduces this but introduces selection bias toward longer-duration activities .

### 7.2 Sparse Labels vs. Continuous Streams

EMA provides **sparse, categorical labels** (activity type at specific moments) while accelerometers provide **dense, continuous time series**. The interpolation problem—generalizing from sparse labels to continuous classification—remains largely unresolved. Most studies either:
- Discard unlabelled data (wasteful), or
- Assume label persistence between prompts (inaccurate for dynamic activities).

### 7.3 Missing Data Patterns

Missing EMA responses are **not random**: they correlate with higher physical activity levels (participants skip prompts during exercise) and specific contexts (driving, work meetings) . Standard missing data methods (e.g., EM algorithm) underestimate variance when applied to accelerometer outcomes; multiple imputation is preferred but rarely used .

### 7.4 Self-Report Bias

Social desirability bias persists despite momentary design: participants under-report sedentary time and over-report vigorous activity compared to accelerometer measures, though less severely than with retrospective questionnaires .

---

## 8. Common Weaknesses and Blind Spots

### 8.1 Collection Without Integration
A substantial proportion of studies collect EMA and accelerometer data concurrently but analyse them separately—reporting population means for each rather than integrated bout-level or epoch-level analyses .

### 8.2 Poor Reporting of Compliance
Over one-third of studies fail to report EMA completion rates stratified by accelerometer wear-time. Compliance averages 76% across studies reporting it, but this masks significant variation by time-of-day (higher compliance in evenings) and day-of-study (declining compliance over time) .

### 8.3 Weak Handling of Non-Wear
Studies rarely use EMA data to validate accelerometer non-wear algorithms. When EMA indicates "not wearing" but accelerometer shows zero counts, this provides critical validation data; this validation step is frequently omitted .

### 8.4 Over-Reliance on Random Prompting
Random signal-contingent designs miss sporadic high-intensity activities and capture excessive sedentary data (due to base rates). Event-triggered designs are theoretically superior but methodologically underdeveloped, with optimal trigger thresholds (steps/minute, sedentary bout duration) remaining population-specific .

### 8.5 Limited Use for Sedentary Behaviour Interpretation
While EMA excels at contextualizing SB (distinguishing TV-watching from computer work), most studies use it only to validate total sedentary time rather than to classify SB types or domains .

### 8.6 Neglect of Algorithmic Consequences
Few studies report how EMA label accuracy affects machine learning model performance. The WEALTH study is an exception, demonstrating that thresholding EMA labels at 50% confidence improves classifier accuracy from baseline, but this approach remains rare .

---

## 9. Best-Practice Recommendations for Future Studies

### 9.1 Protocol Design

**Prioritize Event-Triggered Over Random Prompting**  
Trigger EMA based on accelerometer-detected transitions (e.g., >20 min sedentary bout onset, walking bout >3 minutes). This maximizes contextual data capture during behaviourally relevant moments while minimizing participant burden .

**Implement Dual Validation**  
Use EMA to validate accelerometer wear-time (asking "Are you wearing the device?") and use accelerometer data to validate EMA recall (flagging inconsistencies for sensitivity analyses).

### 9.2 Variable Selection

**Mandatory Core Items**:
- Current activity type (sitting, standing, walking, running, cycling, other)
- Activity domain (work, leisure, transport, household)
- Device wear status
- Location (indoor/outdoor, home/work/other)

**Avoid**:
- Complex recall of duration ("How long have you been...?")—accelerometers measure duration better.
- Burdensome psychological scales unless the primary research question involves affect-activity dynamics.

### 9.3 Temporal Alignment

1. Synchronize device clocks daily or use post-hoc cross-correlation alignment .
2. Use ±15-minute windows for concurrent validity, but ±5-minute windows for algorithmic labelling to reduce ambiguity.
3. Record prompt response latency and adjust alignment accordingly.

### 9.4 Algorithm Development

1. **Treat EMA as weak labels**: Use threshold-based selection (retain only high-agreement EMA-sensor pairs) to create training datasets .
2. **Embrace sparsity**: Use semi-supervised or self-supervised learning to leverage unlabelled accelerometer data, rather than discarding it.
3. **Validate labels**: Always report EMA-sensor agreement statistics before using EMA labels as ground truth.

### 9.5 Missing Data

- Report completion rates by wear-time and time-of-day.
- Use multiple imputation rather than single imputation (EM algorithm) to preserve variance estimates .
- Analyse missingness patterns—if MVPA episodes correlate with missing EMA, this indicates carrying issues rather than non-compliance.

---

## 10. Representative Studies / Datasets

### 10.1 WEALTH Study (Wearable Sensor Assessment of Physical and Eating Behaviours)
- **Devices**: activPAL (thigh), Fitbit (wrist), ActiGraph (hip), GENEActiv (wrist)
- **EMA Design**: Event-triggered and time-based via HealthReact app; activity-type reporting triggered by detected bouts
- **Scientific Contribution**: Framework for labelling free-living data using EMA + threshold-based refinement; demonstrated 50–83% labelling accuracy depending on activity
- **Limitation**: Limited activity taxonomy (6 categories); cycling and standing poorly classified 

### 10.2 Dunton et al. (2012) — Momentary Assessment of Adults' PA and SB
- **Devices**: ActiGraph GT2M (hip) + Mobile phone EMA
- **EMA Design**: Random signal-contingent (4 days, ~5 prompts/day)
- **Scientific Contribution**: Established feasibility of mobile EMA in adults; demonstrated criterion validity (higher MVPA counts in ±15 min around PA-reported prompts); identified compliance decline over study duration
- **Limitation**: Weekend-only sampling limits generalizability 

### 10.3 Liao et al. (2019) — Systematic Review of EMA in SB Research
- **Scope**: 21 studies (children, adolescents, adults)
- **Key Finding**: 81% of studies asked about "behaviour of the moment," but only 19% included location/company questions; only 4 studies used objective SB measurement (ActiGraph)
- **Limitation**: Most studies relied on self-report alone; limited integration with thigh-worn inclinometers 

### 10.4 Reifegerste et al. (2020) — Sedentary Behavior-Triggered EMA
- **Devices**: move 3 (thigh-worn) + smartphone
- **EMA Design**: Triggered after 20–30 min sedentary bouts; assessed mood, domain, social context
- **Scientific Contribution**: Demonstrated technical feasibility of SB-triggered EMA; revealed context matters—not all prolonged sitting is equivalent (work vs. leisure)
- **Limitation**: Technical issues with triggering algorithms led to missed prompts and participant frustration 

### 10.5 Knell et al. (2022) — Single-Item Daily EMA
- **Devices**: Fitbit Flex (wrist)
- **EMA Design**: End-of-day single item ("Did you exercise ≥30 min today?") for 12 months
- **Scientific Contribution**: Demonstrated long-term feasibility (mean 323 days); fair agreement with accelerometer (Kappa 0.28–0.37); established utility for detecting exercise habits vs. incidental activity
- **Limitation**: Binary outcome lacks granularity; wrist-worn devices miss cycling/swimming 

---

## 11. Final Synthesis: What Everyone Does, What They Do Not Do, and What They Should Do

### What Everyone Does
- Collects 4–7 days of concurrent EMA and accelerometer data .
- Uses random or semi-random prompting schedules (6–8 prompts/day).
- Asks about current activity type and location.
- Links data using ±15-minute windows around prompts.
- Reports compliance rates averaging 76% .

### What Everyone Does Not Do
- **Validate EMA labels before using them as ground truth** for algorithms. Most studies assume EMA accuracy rather than quantifying EMA-sensor agreement .
- **Report wear-time specific compliance**. Few studies distinguish between "participant did not answer" and "participant was not wearing the device" .
- **Use EMA to classify sedentary behaviour domains**. Despite capability, EMA is rarely used to distinguish occupational from leisure sitting in analytical models .
- **Handle missing EMA appropriately**. Most studies use complete-case analysis or single imputation, underestimating variance .
- **Integrate EMA into algorithmic architectures** beyond simple labelling. The potential for EMA to provide contextual features (domain, social context) in multimodal models remains unrealized.

### What Everyone Should Do
1. **Adopt event-triggered EMA** informed by real-time accelerometer data to reduce burden and increase ecological validity .
2. **Treat EMA as weak labels** and implement threshold-based selection (e.g., 50% confidence cut-off) to improve training data quality for machine learning .
3. **Collect minimal essential variables**: activity type, domain, device wear status, and social/location context; omit burdensome psychological items unless specifically warranted.
4. **Validate non-wear algorithms** using EMA self-reports of device removal .
5. **Analyse missingness mechanistically**: distinguish between "not prompted," "prompted but not answered," and "answered but not wearing device" to identify carrying issues vs. compliance issues .
6. **Use temporal alignment algorithms** to correct clock drift between devices rather than assuming timestamp fidelity .

---

### Summary Table: EMA Utility in Body-Mounted Accelerometer Studies

| EMA Use | What It Adds | Limitations | Burden | Modelling Value | Recommendation |
|---------|--------------|-------------|--------|-----------------|----------------|
| **Activity Type Labelling** | Ground truth for sitting, walking, running | Poor for cycling/standing; temporal misalignment | Low | High (if thresholded) | **Use** with 50% confidence threshold |
| **Domain Classification** | Distinguishes work/leisure/transport | Subjective; social desirability bias | Low | High for health outcomes | **Essential** |
| **Context (Social/Location)** | Indoor/outdoor, alone/others | Recall burden for location | Low | Moderate | **Include** |
| **Device Wear Validation** | Identifies non-wear periods | Rarely collected | Low | High for data quality | **Mandatory** |
| **Affect/Mood** | Predicts future PA intention | Not activity classification; high burden | Moderate | Low for classification; High for prediction | **Optional** (context-dependent) |
| **End-of-Day Exercise Recall** | Long-term adherence tracking | Poor temporal resolution; recall bias | Very Low | Low for bout-level analysis | **Use only** for long-term trend analysis |
| **Event-Triggered SB Context** | Context of prolonged sitting | Technical complexity; false triggers | Moderate | High for JIT interventions | **Adopt** for SB studies |

This synthesis demonstrates that while EMA is methodologically feasible and adds essential contextual dimensions to accelerometer data, the field must shift from treating EMA as a validation afterthought to integrating it as a structured component of data collection architectures—particularly for algorithm development where its role as a source of weak, contextualized labels represents its highest scientific utility.