## Ecological Momentary Assessment in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour: A Comprehensive Literature Investigation

___

## 1\. Search and Screening Summary

The search strategy employed combinations of terms including "ecological momentary assessment AND accelerometer physical activity," "experience sampling AND body-worn accelerometer," "ambulatory assessment AND sedentary behaviour accelerometer," "activPAL EMA," "ActiGraph EMA physical activity," "Axivity EMA," "body-mounted accelerometer self-report physical activity," "accelerometer activity classification EMA," and adjacent terminology such as "momentary self-report," "prompted self-report," and "real-time self-report." The reference candidates were screened against the strict inclusion criteria requiring: (1) a dedicated body-mounted accelerometer device as the primary movement sensor, (2) a focus on physical activity, sedentary behaviour, or activity classification, and (3) participant-reported EMA or equivalent real-time/near-real-time self-report collected during the same monitoring period.

From the pool of candidate references, the screening process identified a small number of studies that genuinely meet the strict scope, a larger number that provide adjacent or contextual information, and a substantial majority that fall outside scope due to their focus on physiological monitoring, sleep, cardiovascular disease, neurological conditions, or general wearable technology reviews without EMA integration in physical activity research.

___

## 2\. Inclusion/Exclusion Logic

### Included Studies

Studies were included if they combined a dedicated body-mounted accelerometer (e.g., ActiGraph, activPAL, Axivity, GENEActiv, SENS Motion) with EMA or equivalent real-time self-report, with a primary focus on physical activity and/or sedentary behaviour in free-living or partially free-living conditions.

### Excluded Studies

Studies were excluded if they: focused primarily on physiological monitoring (heart rate, ECG, EEG, EDA, sleep staging); used only smartphones or smartwatches as the primary movement sensor; addressed rehabilitation biomechanics, seizure detection, stress detection, eating disorders, or substance use without a clear physical activity/sedentary behaviour focus; were purely lab-based HAR studies without EMA; or were general mHealth/digital phenotyping reviews without specific accelerometer + EMA physical activity content.

### Adjacent/Context-Only Studies

Studies were classified as adjacent if they discussed relevant methodological concepts (e.g., combining objective and subjective sedentary behaviour measurement, accelerometer data processing methods, ambulatory assessment frameworks) but did not themselves implement the specific combination of body-mounted accelerometer + EMA for physical activity/sedentary behaviour research.

___

## 3\. Included Study Matrix

Given the strict scope restrictions, the following studies from the reference pool and the broader literature they reference are identified as included or near-included:

# Ecological Momentary Assessment in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour: A Comprehensive Literature Investigation

| # |                       Study                       |                  Population                  |                    Device & Placement                    |             Free-living?             |                   PA/SB Focus                    |                      EMA Terminology                      |             EMA Delivery             |                     Prompt Schedule                     |        Recall Frame        |                               EMA Variables                               |                          EMA-Accelerometer Linkage                           |                            EMA Use                            |                        Algorithm Contribution                        |                                     Limitations                                     |
|-----|---------------------------------------------------|----------------------------------------------|----------------------------------------------------------|--------------------------------------|--------------------------------------------------|-----------------------------------------------------------|--------------------------------------|---------------------------------------------------------|----------------------------|---------------------------------------------------------------------------|------------------------------------------------------------------------------|---------------------------------------------------------------|----------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| 1 |               Sigcha et al. (2025)                |          589 adults (WEALTH study)           |           activPAL (thigh), ActiGraph, Fitbit            |         Free-living (7 days)         |              PA classification, SB               |              EMA (event-based & time-based)               |     Smartphone app (HealthReact)     | Event-triggered (sensor-detected activity) + time-based | Immediate/current activity |    Activity type (sitting, standing, walking, running, cycling, lying)    |    Timestamp synchronization of EMA responses with accelerometer windows     |         Labelling, validation, algorithm development          | Yes—ML classifier trained on EMA-labelled data; up to 73.6% accuracy |      Sparse labels; compliance variability; agreement varies by activity type       |
| 2 |   (Brannon et al., 2016; (Brannon et al., 2016;   |                20 adolescents                |             ActiGraph wActiSleep-BT (wrist)              |        Free-living (20 days)         |          PA, sleep, sedentary behaviour          |                            EMA                            |              Mobile app              |                      4 surveys/day                      |       Current/recent       |        Psychosocial variables, affect, context, PA-related states         |               Temporal co-occurrence during monitoring period                |       Context, feasibility, dynamical systems modelling       |       Aspirational—data intended for dynamical systems models        |          Low physiological monitor compliance; limited modelling reported           |
| 3 |                Kratz et al. (2024)                |              260 adults with MS              |                ActiGraph wGT3X-BT (wrist)                | Free-living (14 days per assessment) | PA, sedentary behaviour (secondary to cognition) |                            EMA                            |            Smartphone app            |    4×/day (wake, midday, afternoon/evening, bedtime)    |     Current/momentary      |         Somatic symptoms, mood, functioning, behaviours, context          |        Concurrent monitoring; accelerometry continuous alongside EMA         |          Context, interpretation, temporal dynamics           |                  Not directly for PA classification                  | PA is secondary to cognitive focus; EMA not directly linked to accelerometer epochs |
| 4 | (Delobelle et al., 2024; (Delobelle et al., 2024; |         37 adults + 32 older adults          | ActiGraph GT3X+ (hip), activPAL4 (thigh), Fitbit (wrist) |         Free-living (3 days)         |                PA (stepping), SB                 | EMA (referenced in context of JITAIs and event-based EMA) |                  —                   |                            —                            |             —              |                                     —                                     | Fitbit validated against ActiGraph/activPAL for triggering EMA/JITAI prompts |            Validation of trigger accuracy for EMA             |       Indirect—validates sensor thresholds for EMA triggering        |             Validation study; EMA not directly collected in this study              |
| 5 |        (Le et al., 2024; (Le et al., 2024;        | Adults (usability + free-living feasibility) |       Smartwatch (with accelerometer) + reference        |       Free-living (6–21 days)        |                   PA, posture                    |                     μEMA, audio-μEMA                      | Smartwatch + bone-conduction headset |                    Every 2–5 minutes                    |  Current activity/posture  | Physical activity type, posture (sitting, standing, walking, lying, etc.) |             Real-time self-report synchronized with sensor data              | Labelling (high-density self-report for activity recognition) |         Yes—designed to provide dense labels for HAR systems         |        Smartwatch-based (borderline scope); high burden; 67.7% response rate        |
| 6 |       (Kim et al., 2022) (Kim et al., 2022)       |                 Older adults                 |              activPAL (thigh) + smartwatch               |             Free-living              |                   PA, posture                    |                  ESM/EMA (speech-based)                   |      Smartwatch (speech input)       |                    Periodic prompts                     |      Current activity      |            Activity labels (walking, sitting, household, etc.)            |       activPAL walking cadence compared with smartwatch-derived labels       |                       Labelling for HAR                       |        Yes—in-situ labels collected for activity recognition         |       Small sample; smartwatch as EMA delivery device; activPAL as reference        |

**Note:** The literature that strictly meets all inclusion criteria is remarkably thin. Many studies referenced in the candidates discuss EMA and accelerometers separately or use EMA for psychological/clinical outcomes while accelerometers measure PA as a covariate rather than as the primary integrated focus.

___

## 4\. Executive Summary

The intersection of Ecological Momentary Assessment (EMA) and body-mounted accelerometer-based physical activity (PA) and sedentary behaviour (SB) research represents a methodologically promising but empirically underdeveloped field. While accelerometers such as the activPAL, ActiGraph, Axivity, and GENEActiv have become standard tools for objectively measuring movement, posture, and activity intensity in free-living conditions (Aunger & Wagnild, 2020; , Pavey et al., 2017; , Gao et al. (2021), and while EMA has been established as a powerful method for capturing real-time subjective experiences and contextual information Intille, 2007), Russell & Gajos, 2020), the systematic integration of these two approaches specifically for PA/SB research remains surprisingly sparse.

The most directly relevant study identified is Sigcha et al. (2025), which presents a novel framework integrating thigh-worn activPAL accelerometer data with event-based EMA surveys to label different types of physical activity in free-living settings, achieving up to 97% agreement with ground-truth labels for certain activities and training machine learning classifiers on the resulting dataset. This study represents the clearest exemplar of EMA being used as a labelling tool for accelerometer-based PA classification in free-living conditions.

Beyond this, the literature reveals that EMA in accelerometer-based PA/SB studies is most commonly used for: (a) contextualisation of objectively measured activity patterns, (b) feasibility assessment of intensive monitoring protocols, (c) capturing psychological and social correlates of movement behaviour, and (d) aspirationally, for providing labels for activity recognition algorithms. However, the actual integration of EMA data into accelerometer-based modelling pipelines remains rare and methodologically underdeveloped.

___

## 5\. What EMA Contributes Beyond Body-Mounted Accelerometers

### 5.1 The Fundamental Limitation of Accelerometers Alone

Body-mounted accelerometers, regardless of placement, provide objective data on movement intensity, duration, frequency, and—when placed on the thigh—posture (sitting/lying vs. standing vs. stepping) (Aunger & Wagnild, 2020; , Pavey et al., 2017; , Gao et al. (2021), Atkin et al., 2012). The activPAL, for instance, has been validated against direct observation for total sedentary time with ≥95% agreement in both laboratory and free-living contexts (Aunger & Wagnild, 2020; . ActiGraph devices, when worn on the hip or wrist, can classify activity intensity using count-based cut-points or machine learning approaches (Boudet et al., 2019; , Gao et al. (2021). However, as (Aunger & Wagnild, 2020; emphasise, "objective measures such as inclinometers are the gold-standard for measuring total sedentary time but they typically cannot capture contextual information or determine which specific behaviors are taking place" (Aunger & Wagnild, 2020; .

This fundamental limitation—the inability of accelerometers to capture the _meaning_, _purpose_, _domain_, and _context_ of movement or stillness—is precisely where EMA offers its primary added value. An accelerometer can detect that a person is sitting, but cannot distinguish between sitting at a desk working, sitting in a car commuting, sitting watching television, or sitting in a social gathering. Similarly, walking detected by an accelerometer could represent purposeful exercise, occupational movement, transportation, or household activity (Aunger & Wagnild, 2020; , Atkin et al., 2012).

### 5.2 How EMA Differs from Other Complementary Methods

EMA occupies a distinct methodological niche compared to other approaches used alongside accelerometers:

**Versus retrospective questionnaires:** Retrospective self-report instruments are subject to recall bias and measurement error (Aunger & Wagnild, 2020; , Gao et al. (2021), Bussmann et al., 2009). EMA minimises the time between behaviour occurrence and reporting, reducing memory decay and social desirability bias Intille, 2007), Russell & Gajos, 2020). As Spruijt-Metz et al. (2018) note, "EMA, an active real-time self-reported data collection technique... is thought to minimize errors of self-report because it minimizes the time between the occurrence of a behavior and reporting of it" Spruijt‐Metz et al., 2018; .

**Versus time-use diaries:** While 24-hour recall methods can provide detailed activity logs, they are burdensome and still rely on retrospective recall (Aunger & Wagnild, 2020; . EMA captures information closer to real-time and can be prompted at specific moments of interest.

**Versus direct observation:** Direct observation is the gold standard for activity classification but is "typically too costly and invasive for long-term, large-sample-size studies of people in their natural environments" Intille, 2007). EMA provides a scalable alternative that, while less precise, can operate over extended free-living periods.

**Versus video annotation:** Wearable cameras have been used alongside accelerometers to assess context and intensity of daily physical activity (Aunger & Wagnild, 2020; , but raise significant privacy concerns and generate enormous data volumes requiring manual coding. EMA is less invasive and more scalable, though it provides less granular information.

**Versus controlled labelling protocols:** Laboratory-based activity protocols provide clean, unambiguous labels but "often fail to generalize to free-living conditions due to variability in activity patterns and data acquisition" Sigcha et al. (2025). EMA enables labelling in naturalistic settings, albeit with greater noise and sparsity.

### 5.3 What EMA Actually Is in This Field

Based on the included literature, EMA in body-mounted accelerometer PA/SB research is best understood as serving multiple roles simultaneously:

-   **Contextual metadata:** Most commonly, EMA provides information about the behavioural domain, purpose, location, and social context of objectively measured activity or inactivity (Aunger & Wagnild, 2020; , Spruijt‐Metz et al., 2018; , Russell & Gajos, 2020).
-   **Weak supervision / sparse labelling:** In the most methodologically advanced applications, EMA serves as a source of sparse but ecologically valid labels for training or validating activity classification algorithms Sigcha et al. (2025), (Le et al., 2024; , (Kim et al., 2022).
-   **Subjective state capture:** EMA captures psychological states (affect, fatigue, motivation, perceived exertion) that co-occur with objectively measured movement patterns Kratz et al. (2024), (Brannon et al., 2016; .
-   **Near-ground truth (for certain variables):** For activity type and purpose, EMA provides the closest approximation to ground truth achievable at scale in free-living conditions, though it is clearly not equivalent to direct observation or video annotation Sigcha et al. (2025).
-   **Compliance and quality-control signal:** EMA responses can indicate whether participants are wearing devices and engaging with the study protocol (Brannon et al., 2016; .

Critically, EMA should _not_ be understood as ground truth in the traditional sense. As Sigcha et al. (2025) demonstrate, EMA-derived labels achieve up to 97% agreement with algorithmic ground truth for some activities (e.g., sitting) but substantially lower agreement for others, reflecting the inherent limitations of self-report even when collected in real-time Sigcha et al. (2025).

___

## 6\. How EMA Is Used in PA/SB Studies

### 6.1 Contextualisation of Accelerometer-Measured Behaviour

The most common use of EMA in this field is to provide contextual information that accelerometers cannot capture. This includes the behavioural domain (occupational vs. leisure vs. transport), the social context (alone vs. with others), the physical environment (indoor vs. outdoor, home vs. workplace), and the purpose of activity or inactivity (Aunger & Wagnild, 2020; , Spruijt‐Metz et al., 2018; , Russell & Gajos, 2020). (Aunger & Wagnild, 2020; recommend that "researchers use the method(s) that suit the research question; inclinometers are recommended for the measurement of total sedentary time, while self-report methods are recommended for measuring time spent in particular contexts of sedentary behavior" (Aunger & Wagnild, 2020; . This recommendation implicitly supports the use of EMA as a contextualisation layer atop objective accelerometer measurement.

### 6.2 Labelling for Activity Classification

The most methodologically innovative use of EMA in this field is as a labelling tool for machine learning-based activity classification. Sigcha et al. (2025) present the most explicit framework for this purpose, integrating thigh-worn accelerometer data with event-based EMA surveys to create a sparsely labelled dataset for training PA classifiers Sigcha et al. (2025). Their framework "combines accelerometer data collected from activPAL thigh-worn sensors with participant-reported information obtained through time-stamped (event-based) EMA prompts" Sigcha et al. (2025). The event-based EMA approach is particularly noteworthy: rather than prompting at fixed intervals, the system automatically triggers self-report prompts in response to sensor-detected activities such as walking or prolonged sedentary periods Sigcha et al. (2025).

(Le et al., 2024; explore an alternative approach using audio-based micro-EMA (audio-μEMA) to collect high-density self-reported physical activity and posture labels, prompting participants every 2–5 minutes (Le et al., 2024; . Despite the high interruption frequency (12–20 times per hour), participants maintained an average response rate of 67.7% for up to 14 days (Le et al., 2024; . This approach is explicitly designed to provide temporally dense labels for real-time activity recognition systems.

(Kim et al., 2022) developed MyMove, a smartwatch-based system enabling older adults to collect in-situ activity labels using speech input, with activPAL serving as a reference measure for walking cadence (Kim et al., 2022). This study demonstrates the feasibility of using EMA-style self-report to generate activity labels that can be compared against objective accelerometer measures.

### 6.3 Validation of Accelerometer-Derived Measures

EMA can serve as a validation tool for accelerometer-derived activity classifications. (Delobelle et al., 2024; validated Fitbit devices' accuracy for detecting short bouts of stepping and sedentary behaviour against ActiGraph and activPAL, specifically in the context of determining whether Fitbit could reliably trigger EMA prompts or just-in-time adaptive intervention (JITAI) content (Delobelle et al., 2024; . Their finding that "Fitbits' reasonable accuracy in detecting short bouts of stepping and SB makes them suitable for triggering JITAI prompts or EMA questionnaires following a PA or SB event of interest" (Delobelle et al., 2024; highlights the bidirectional relationship between accelerometer measurement and EMA delivery.

### 6.4 (Brannon et al., 2016; explicitly assessed the feasibility and acceptability of combining wearable accelerometers with intensive EMA protocols in adolescents (Brannon et al., 2016; . Their finding that "participants provided approximately 81% of the expected survey data" and were "compliant to the wrist-worn accelerometer (75.3%)" (Brannon et al., 2016; provides important benchmarks for the field. The study demonstrates that intensive multi-modal assessment combining accelerometers and EMA is feasible, though compliance varies across modalities.

### 6.5 Temporal Dynamics and Behaviour Interpretation

Kratz et al. (2024) describe a protocol combining continuous wrist-worn ActiGraph accelerometry with four-times-daily EMA to examine temporal dynamics of cognitive function, somatic symptoms, mood, and physical activity in people with multiple sclerosis Kratz et al. (2024). While the primary focus is cognitive, the study illustrates how EMA can be used to interpret accelerometer-measured activity patterns in the context of fluctuating symptoms and daily experiences. The concurrent collection of accelerometry and EMA enables examination of "temporal dynamics of cognitive function, somatic and mood symptoms, sleep, physical activity, and physical and social function" Kratz et al. (2024).

___

## 7\. Role of EMA in Labelling, Validation, and Algorithm Development

### 7.1 EMA as a Direct Label Source

The most explicit use of EMA as a direct label source for activity classification is found in Sigcha et al. (2025). Their framework demonstrates that event-based EMA can generate labels with up to 97% agreement with ground-truth data from the proprietary activPAL CREA algorithm for certain activity categories Sigcha et al. (2025). A machine learning algorithm trained on the resulting EMA-labelled dataset achieved classification accuracies of up to 73.6% Sigcha et al. (2025). This represents a significant proof-of-concept for using EMA as a labelling strategy in free-living PA research.

However, the study also reveals important limitations: labelling accuracy varies substantially across activity types, with sitting and running showing high agreement but other activities showing lower concordance Sigcha et al. (2025). The sparsity of EMA labels—inherent to any self-report method that interrupts participants—means that only a fraction of the accelerometer time series receives labels, creating challenges for training data-hungry machine learning models.

### 7.2 EMA as a Weak Label Source

More commonly in the broader literature, EMA functions as a source of weak or noisy labels rather than precise ground truth. The concept of "weak supervision" is particularly relevant here: EMA provides labels that are approximately correct, temporally imprecise, and subject to self-report biases, but that nonetheless contain useful signal for training or evaluating classifiers. Sigcha et al. (2025) explicitly characterise their approach as generating "sparsely labelled datasets, which are characterized by limited but strategically timed and contextually relevant annotations" Sigcha et al. (2025).

### 7.3 EMA as a Contextual Feature Source

In principle, EMA-reported context (location, social setting, activity purpose) could serve as input features for context-aware activity classification models. However, the included literature provides limited evidence of this being implemented in practice. The aspiration is clearly present—Intille, 2007) envisioned systems where "software on the PDA can then respond to the person's physical activity with a targeted question during or just after the behavior of interest" Intille, 2007)—but the actual implementation in published accelerometer-based PA/SB studies remains rare.

### 7.4 EMA as a Validation Source

EMA can validate accelerometer-derived classifications by providing independent confirmation of activity type. For instance, if an accelerometer algorithm classifies a period as "walking," an EMA prompt during or shortly after that period can confirm or disconfirm this classification. (Delobelle et al., 2024; demonstrate this principle by validating Fitbit's ability to detect stepping and sedentary bouts against research-grade accelerometers, with the explicit goal of ensuring accurate EMA triggering (Delobelle et al., 2024; .

### 7.5 Current State of Algorithm Development

**The literature is thin.** Despite the clear potential for EMA to contribute to accelerometer-based activity classification, the number of studies that actually implement this integration in a rigorous modelling pipeline is very small. Sigcha et al. (2025) is the most complete exemplar. Most other studies either collect EMA and accelerometer data concurrently but analyse them separately, or use EMA for contextual interpretation rather than algorithmic training.

The field of HAR has extensively developed classification algorithms using accelerometer data (Vijayan et al., 2021; , Gao et al. (2021), Zhang et al., 2022), but these typically rely on laboratory-collected labels, direct observation, or video annotation rather than EMA. The gap between the HAR literature and the EMA literature in PA/SB research is substantial and represents a major missed opportunity.

___

## 8\. Common EMA Variables Collected

Based on the included and adjacent literature, the following EMA variables are collected in accelerometer-based PA/SB studies, categorised by frequency and utility:

### 8.1 Common Variables

-   **Current/recent activity type** (e.g., sitting, standing, walking, running, cycling, lying down): This is the most directly relevant variable for PA/SB research and the most commonly collected in studies that integrate EMA with accelerometers Sigcha et al. (2025), (Le et al., 2024; , (Kim et al., 2022). It provides the closest approximation to activity labels.
-   **Affect/mood** (e.g., positive affect, negative affect, stress, anxiety): Frequently collected in EMA studies that include accelerometry, though often as a psychological outcome rather than a PA-specific variable Kratz et al. (2024), (Brannon et al., 2016; , Russell & Gajos, 2020).
-   **Location** (e.g., home, work, outdoors, transit): Collected to contextualise where activity or inactivity occurs Spruijt‐Metz et al., 2018; , Russell & Gajos, 2020).
-   **Social context** (e.g., alone, with family, with friends, with colleagues): Provides information about the social environment of activity Kratz et al. (2024), Russell & Gajos, 2020).

### 8.2 Less Common but Scientifically Valuable Variables

-   **Purpose/domain of movement** (e.g., exercise, transport, occupational, household, leisure): This is arguably the most scientifically valuable contextual variable that EMA can provide, as it directly addresses the inability of accelerometers to distinguish between behavioural domains (Aunger & Wagnild, 2020; . However, it is collected less frequently than might be expected.
-   **Indoor/outdoor status:** Relevant for understanding environmental influences on activity but not consistently collected.
-   **Perceived exertion:** Provides subjective intensity information that complements objective accelerometer-derived intensity measures.
-   **Fatigue/energy levels:** Particularly relevant in clinical populations (e.g., MS) where fatigue is a major determinant of activity patterns Kratz et al. (2024), Block et al., 2022).
-   **Posture** (self-reported): Can validate accelerometer-derived posture classifications, particularly for devices not worn on the thigh (Le et al., 2024; .

### 8.3 Rare or Aspirational Variables

-   **Barriers to activity / motivation:** Collected in some intervention-focused studies but rarely integrated with accelerometer data analysis.
-   **Specific sedentary behaviour type** (e.g., TV watching, computer use, reading, socialising): Highly relevant for SB research but operationally challenging to collect with sufficient granularity.
-   **Intentionality of activity** (planned vs. incidental): Scientifically attractive but rarely operationalised in EMA protocols.
-   **Compliance/wear-time self-report:** Occasionally used to verify accelerometer wear but not systematically collected.

### 8.4 Assessment of Variable Utility

|         Variable         |      Frequency      | Scientific Value  | Operational Burden |       Modelling Value       |
|--------------------------|---------------------|-------------------|--------------------|-----------------------------|
|  Current activity type   |       Common        |       High        |    Low-moderate    |      High (labelling)       |
|       Affect/mood        |       Common        | Moderate (for PA) |        Low         | Low (for PA classification) |
|         Location         |      Moderate       |       High        |        Low         | Moderate (context feature)  |
|      Social context      |      Moderate       |   Moderate-high   |        Low         |        Low-moderate         |
| Activity purpose/domain  |        Rare         |     Very high     |      Moderate      |     High (if collected)     |
|    Perceived exertion    |        Rare         |     Moderate      |        Low         |             Low             |
|         Fatigue          | Moderate (clinical) |  High (clinical)  |        Low         |  Low (for classification)   |
| Sedentary behaviour type |        Rare         |     Very high     |   Moderate-high    |     High (if collected)     |
|      Intentionality      |      Very rare      |       High        |      Moderate      |           Unknown           |

___

## 9\. Methodological Challenges Linking EMA to Accelerometer Data

### 9.1 Timestamp Alignment

The most fundamental challenge in integrating EMA with accelerometer data is temporal alignment. Accelerometers record continuously at high sampling rates (typically 10–100 Hz), while EMA responses are sparse, delayed, and temporally imprecise Sigcha et al. (2025), Intille, 2007). Sigcha et al. (2025) address this by synchronizing EMA responses with accelerometer signals using timestamps, but acknowledge that the resulting dataset is "sparse" Sigcha et al. (2025). The challenge is compounded by the fact that EMA responses may be delayed relative to the prompt (prompt-response lag), and the activity being reported may have changed between the prompt and the response.

### 9.2 Prompt-Response Lag

When an EMA prompt is delivered, participants may not respond immediately. The delay between prompt delivery and response completion introduces temporal uncertainty about which accelerometer epoch the EMA response actually describes. This is particularly problematic for event-based EMA, where the triggering event may have ended by the time the participant responds Sigcha et al. (2025).

### 9.3 Recall Window Mismatch

EMA items may ask about "current" activity, "recent" activity (e.g., "in the last 15 minutes"), or activity "since the last prompt." Each of these recall frames maps differently onto the continuous accelerometer time series. A question about "current" activity maps to a narrow window around the response time, while "since the last prompt" maps to a potentially long and heterogeneous period. The mismatch between the EMA recall window and the accelerometer analysis window (epoch) is a persistent source of alignment error.

### 9.4 Sparse EMA vs. Dense Accelerometer Time Series

Even with intensive EMA protocols (e.g., 4 prompts/day), the vast majority of the accelerometer time series remains unlabelled. (Brannon et al., 2016; collected 4 surveys per day over 20 days (Brannon et al., 2016; , yielding approximately 80 EMA data points per participant against continuous accelerometer data. (Le et al., 2024; achieved much higher density (every 2–5 minutes) but at the cost of substantial participant burden and a response rate of 67.7% (Le et al., 2024; . The fundamental tension between EMA density and participant burden remains unresolved.

### 9.5 Missing Responses and Compliance

EMA compliance is never 100%. (Brannon et al., 2016; report 81% survey completion and 75.3% accelerometer compliance (Brannon et al., 2016; . Missing EMA responses create gaps in the label stream that are not random—they are more likely during certain activities (e.g., vigorous exercise, driving, social situations) and at certain times of day. This non-random missingness can bias the labelled dataset and the models trained on it.

### 9.6 Self-Report Bias

Even when collected in real-time, self-report is subject to biases including social desirability, difficulty in categorising ambiguous activities, and individual differences in activity perception. As noted in the broader literature, "people were likely to accurately estimate the past duration of intensive physical activities, whereas they were likely to underestimate or omit light and sedentary activities" (Kim et al., 2022). This suggests that EMA labels may be more reliable for vigorous activities than for light or sedentary behaviours—precisely the categories where accelerometer classification is already most accurate.

### 9.7 Event Duration Mismatch

Activities vary enormously in duration. A brief standing transition may last seconds, while a prolonged sitting bout may last hours. EMA prompts capture a snapshot that may not represent the dominant activity within a given analysis window. Conversely, a single EMA response may span multiple accelerometer-defined activity bouts.

### 9.8 Alignment Strategies Used

The strategies employed in the literature include:

-   **Timestamp-based synchronization:** Matching EMA response timestamps to the nearest accelerometer epoch Sigcha et al. (2025), Kratz et al. (2024).
-   **Event-triggered prompting:** Delivering EMA prompts in response to sensor-detected events, ensuring temporal proximity between the measured event and the self-report Sigcha et al. (2025), (Delobelle et al., 2024; .
-   **Fixed-window matching:** Assigning EMA responses to a fixed time window (e.g., ±5 minutes) around the response timestamp.
-   **Activity-bout matching:** Matching EMA responses to the accelerometer-defined activity bout that was occurring at the time of the prompt.

Event-triggered prompting, as implemented by Sigcha et al. (2025) and validated by (Delobelle et al., 2024; (Delobelle et al., 2024; , appears to be the strongest alignment strategy, as it ensures that the EMA prompt is temporally and contextually linked to a specific sensor-detected event.

___

## 10\. Common Weaknesses and Blind Spots

### 10.1 EMA Collected but Not Integrated into Modelling

The most pervasive weakness in this literature is the collection of EMA data alongside accelerometer data without meaningful integration. Many studies collect both data streams but analyse them separately—using accelerometers for objective PA/SB measurement and EMA for psychological or contextual outcomes—without leveraging EMA to improve accelerometer-based classification or using accelerometer data to validate EMA responses (Brannon et al., 2016; , Kratz et al. (2024). This represents a significant missed opportunity.

### 10.2 Poor Compliance Reporting

Many studies fail to report EMA compliance in sufficient detail. When compliance is reported, it is often presented as an overall percentage without breakdown by time of day, activity type, or participant characteristics. Given that non-random missingness can substantially bias results, detailed compliance reporting is essential but frequently absent.

### 10.3 Vague Temporal Alignment

The methods used to link EMA responses to accelerometer epochs are often poorly described. Studies may state that EMA and accelerometer data were "collected concurrently" without specifying how temporal alignment was achieved, what time windows were used for matching, or how prompt-response delays were handled.

### 10.4 Overbroad EMA Item Sets

Some studies collect extensive EMA batteries covering mood, symptoms, social context, and multiple behavioural domains, resulting in high participant burden but low modelling value for PA/SB classification. The inclusion of items that are scientifically interesting but operationally irrelevant to the accelerometer-based research question dilutes the protocol's effectiveness.

### 10.5 Failure to Resolve Behavioural Ambiguity

Despite EMA's potential to disambiguate accelerometer-measured behaviour, many studies fail to ask the specific questions that would resolve the most important ambiguities. For instance, distinguishing occupational from leisure sitting, or exercise from transport walking, requires targeted EMA items that are often absent from generic EMA batteries.

### 10.6 Weak Treatment of Domain/Purpose/Social/Environmental Context

The variables that would add the most value to accelerometer data—activity domain, purpose, and environmental context—are precisely those that are least consistently collected and least well-integrated into analysis pipelines (Aunger & Wagnild, 2020; .

### 10.7 High Burden with Low Modelling Value

Intensive EMA protocols (multiple prompts per day over multiple days) impose substantial participant burden. When the resulting data are not used for modelling or classification, this burden is difficult to justify. The field needs a clearer articulation of the minimum EMA data required to achieve specific analytical goals.

___

## 11\. Best-Practice Recommendations

### 11.1 For Physical Activity Classification

If the goal is to use EMA to support accelerometer-based PA classification:

-   **Use event-triggered EMA** that prompts participants when the accelerometer detects a change in activity state Sigcha et al. (2025), (Delobelle et al., 2024; . This ensures temporal alignment and contextual relevance.
-   **Ask about current activity type** using a concise, mutually exclusive category set (e.g., sitting, standing, walking, running, cycling, lying down, other) Sigcha et al. (2025), (Le et al., 2024; .
-   **Minimise prompt-response lag** by using simple, single-item questions that can be answered in seconds (Le et al., 2024; .
-   **Report and model compliance** as a function of activity type, time of day, and participant characteristics.
-   **Treat EMA labels as weak supervision** rather than ground truth, and use appropriate machine learning methods (e.g., noise-robust loss functions, semi-supervised learning) that can handle label noise and sparsity Sigcha et al. (2025).

### 11.2 For Sedentary Behaviour Interpretation

If the goal is to interpret accelerometer-measured sedentary time:

-   **Ask about the type of sedentary behaviour** (e.g., TV watching, computer use, reading, socialising, eating, transport) (Aunger & Wagnild, 2020; .
-   **Ask about the domain** (occupational vs. leisure vs. transport) (Aunger & Wagnild, 2020; , Atkin et al., 2012).
-   **Ask about location** (home, workplace, vehicle, other).
-   **Use time-based prompts during detected sedentary bouts** to capture the context of prolonged sitting.
-   **Combine with activPAL** for objective posture classification, using EMA to provide the contextual layer that the activPAL cannot (Aunger & Wagnild, 2020; .

### 11.3 For Context-Aware Behaviour Analysis

If the goal is comprehensive context-aware analysis:

-   **Collect a focused set of contextual variables:** activity type, domain/purpose, location, social context, indoor/outdoor Spruijt‐Metz et al., 2018; , Russell & Gajos, 2020).
-   **Avoid collecting variables that do not serve the research question** (e.g., detailed mood scales in a study focused on activity classification).
-   **Use a mixed prompting strategy:** combine event-triggered prompts (for activity transitions) with periodic random prompts (for representative sampling of the day) Sigcha et al. (2025).
-   **Ensure that EMA items are designed to resolve specific accelerometer ambiguities** rather than serving as a generic psychological assessment.

### 11.4 For Multimodal Algorithm Development

If the goal is to develop multimodal models that integrate accelerometer and EMA data:

-   **Design the EMA protocol specifically for modelling purposes,** with items that provide information not available from the accelerometer alone.
-   **Maximise temporal density** within acceptable burden limits. (Le et al., 2024; demonstrate that prompting every 2–5 minutes is feasible for short periods (Le et al., 2024; , while (Brannon et al., 2016; show that 4 prompts/day is sustainable over 20 days (Brannon et al., 2016; .
-   **Pre-register the analysis plan** specifying how EMA data will be integrated with accelerometer data.
-   **Use EMA for both training and validation,** holding out a subset of EMA-labelled data for independent model evaluation Sigcha et al. (2025).
-   **Explore semi-supervised and self-supervised learning approaches** that can leverage the large volume of unlabelled accelerometer data alongside the sparse EMA labels.

### 11.5 What to Avoid

-   **Do not collect EMA without a clear plan for integration** with accelerometer data.
-   **Do not use generic EMA batteries** designed for psychological research when the goal is PA/SB classification.
-   **Do not assume EMA is ground truth**—it is a noisy, sparse, and biased signal that requires careful handling Sigcha et al. (2025).
-   **Do not ignore prompt-response lag** and temporal alignment issues.
-   **Do not impose excessive burden** without commensurate analytical value.

### 11.6 Optimal Burden-Value Tradeoff

Based on the available evidence, the optimal burden-value tradeoff depends on the research goal:

|           Goal           |           Recommended Frequency            |                       Recommended Items                        | Expected Burden |  Expected Value   |
|--------------------------|--------------------------------------------|----------------------------------------------------------------|-----------------|-------------------|
| Activity classification  |         Event-triggered (5–15/day)         |             1–2 items (activity type, confidence)              |    Moderate     |       High        |
|    SB interpretation     |    Time-based during SB bouts (3–6/day)    |             2–3 items (SB type, domain, location)              |  Low-moderate   |       High        |
|  Context-aware analysis  | Mixed (random + event-triggered, 6–10/day) | 3–5 items (activity, domain, location, social, indoor/outdoor) |  Moderate-high  |       High        |
| Psychological correlates |              Random (4–6/day)              |       5–10 items (affect, fatigue, motivation, context)        |    Moderate     | Moderate (for PA) |

___

## 12\. Representative Studies and Datasets

### 12.1 Sigcha et al. (2025) — WEALTH Study Sigcha et al. (2025)

**Why it matters:** This is the most complete exemplar of EMA being used as a labelling tool for accelerometer-based PA classification in free-living conditions. It presents a novel framework that directly addresses the challenge of obtaining labelled data for training machine learning models outside the laboratory.

**What it collected:** Data from 589 participants over seven days, combining thigh-worn activPAL accelerometer data with event-based EMA surveys delivered via the HealthReact smartphone app. EMA captured time-stamped self-reported PA behaviours including activity type immediately following automatically detected activities through a Fitbit device Sigcha et al. (2025).

**How EMA was used:** EMA responses were synchronized with accelerometer signals to create a sparsely labelled dataset. This dataset was compared against ground-truth labels generated by the proprietary activPAL CREA algorithm. The framework labelled six PA categories (sitting, standing, walking, running, cycling, lying) with up to 97% agreement with ground-truth data Sigcha et al. (2025).

**Scientific consequence:** A machine learning algorithm trained on the EMA-labelled dataset achieved classification accuracies of up to 73.6%, demonstrating that EMA-derived labels can support meaningful activity classification in free-living conditions Sigcha et al. (2025).

**Limitations:** Labelling accuracy varies by activity type; the dataset is inherently sparse; compliance with EMA prompts varies across participants and activities; the framework relies on a commercial device (Fitbit) for event triggering, introducing an additional source of error Sigcha et al. (2025).

### 12.2 (Brannon et al., 2016; — Adolescent Feasibility Study (Brannon et al., 2016;

**Why it matters:** This study provides one of the earliest and most detailed assessments of the feasibility of combining intensive EMA with wearable accelerometry in a young population, establishing benchmarks for compliance and data yield.

**What it collected:** Twenty adolescents participated in a 20-day protocol wearing an ActiGraph wActiSleep-BT accelerometer and completing four EMA surveys per day on a mobile app, alongside a physiological monitor (Brannon et al., 2016; .

**How EMA was used:** EMA captured psychosocial variables, affect, and context. The study was designed to support dynamical systems modelling of relationships between biopsychosocial variables and health behaviours including physical activity and sedentary behaviour (Brannon et al., 2016; .

**Scientific consequence:** The study demonstrated that intensive multi-modal assessment is feasible in adolescents, with 81% survey completion and 75.3% accelerometer compliance. However, the physiological monitor showed lower compliance (47.8% data capture), highlighting the importance of device acceptability (Brannon et al., 2016; .

**Limitations:** Small sample size (n=20); limited modelling results reported; EMA data were not directly integrated with accelerometer data for activity classification; the study is primarily a feasibility demonstration rather than a substantive analytical contribution (Brannon et al., 2016; .

### 12.3 (Le et al., 2024; — Audio-μEMA for Activity Labelling (Le et al., 2024;

**Why it matters:** This study pushes the boundaries of EMA density for activity labelling, demonstrating that participants can sustain very high-frequency self-report (every 2–5 minutes) using novel audio-based interaction modalities.

**What it collected:** Participants self-reported their physical activities and postures using speech input via smartwatch or bone-conduction headset, with prompts every 2–5 minutes during waking hours over 6–21 days (Le et al., 2024; .

**How EMA was used:** EMA was explicitly designed to provide dense labels for human activity recognition systems. The audio-based approach allowed open-ended responses, capturing more nuanced activity descriptions than multiple-choice formats (Le et al., 2024; .

**Scientific consequence:** Despite being interrupted 12–20 times per hour, participants achieved an average response rate of 67.7% for up to 14 days, demonstrating the feasibility of high-density self-report for activity labelling (Le et al., 2024; .

**Limitations:** The primary sensor was a smartwatch rather than a dedicated research-grade accelerometer (borderline scope); the high prompt frequency may not be sustainable in all populations; the study focused on feasibility rather than classification accuracy; audio processing introduces additional complexity (Le et al., 2024; .

### 12.4 (Kim et al., 2022) — MyMove for Older Adults (Kim et al., 2022)

**Why it matters:** This study demonstrates a practical approach to collecting in-situ activity labels from older adults using speech input on a smartwatch, with activPAL as a reference measure.

**What it collected:** Older adults used the MyMove smartwatch app to verbally report their activities, while wearing an activPAL on the thigh for objective measurement of walking cadence and posture (Kim et al., 2022).

**How EMA was used:** Speech-based ESM/EMA was used to collect activity labels that could be compared against activPAL-derived measures. The study found that "people were likely to accurately estimate the past duration of intensive physical activities, whereas they were likely to underestimate or omit light and sedentary activities" (Kim et al., 2022).

**Scientific consequence:** The study validates the feasibility of speech-based in-situ labelling for older adults and provides evidence on the accuracy of self-reported activity labels compared to objective accelerometer measures (Kim et al., 2022).

**Limitations:** Small sample; smartwatch as both EMA delivery device and secondary sensor; limited to older adult population; classification accuracy not formally evaluated (Kim et al., 2022).

### 12.5 (Delobelle et al., 2024; — Fitbit Validation for EMA Triggering (Delobelle et al., 2024;

**Why it matters:** While not an EMA study per se, this study directly addresses the technical prerequisite for event-based EMA in PA/SB research: the ability of a wearable device to accurately detect activity events that should trigger EMA prompts.

**What it collected:** Thirty-seven adults and 32 older adults wore Fitbit devices alongside ActiGraph GT3X+ (hip) and activPAL4 (thigh) for three days (Delobelle et al., 2024; .

**How EMA was used:** The study validated Fitbit's sensitivity and specificity for detecting stepping and sedentary events, with the explicit goal of determining suitability for triggering JITAI prompts or EMA questionnaires (Delobelle et al., 2024; .

**Scientific consequence:** Both Fitbit models detected stepping bouts with sensitivities and specificities exceeding 87% and 97%, respectively, and optimal cut-off values for prolonged sitting achieved sensitivities >93% and specificities >89% (Delobelle et al., 2024; . This provides confidence that consumer-grade devices can reliably trigger event-based EMA in PA/SB studies.

**Limitations:** EMA was not actually collected in this study; the validation is for the triggering mechanism only; free-living conditions were limited to three days (Delobelle et al., 2024; .

___

## 13\. Final Synthesis: What Everyone Does, Does Not Do, and Should Do

### 13.1 What Everyone Does

-   **Collects accelerometer data and EMA data concurrently** but often analyses them in parallel rather than in an integrated fashion.
-   **Uses EMA primarily for contextualisation and psychological correlates** rather than for activity labelling or classification.
-   **Employs time-based EMA prompting** (typically 3–6 times per day) delivered via smartphone app.
-   **Collects affect, mood, and general context** as the primary EMA variables, with activity type as a secondary or incidental item.
-   **Reports overall EMA compliance** as a single percentage without detailed breakdown.
-   **Uses established accelerometer devices** (ActiGraph, activPAL) as the objective movement measure (Aunger & Wagnild, 2020; , Gao et al. (2021).
-   **Acknowledges the complementarity** of objective and subjective measurement but does not fully exploit it (Aunger & Wagnild, 2020; , Spruijt‐Metz et al., 2018; .

### 13.2 What Everyone Does Not Do

-   **Integrate EMA data into accelerometer-based classification pipelines.** With the notable exception of Sigcha et al. (2025), the use of EMA as a labelling source for machine learning models is virtually absent from the published literature.
-   **Design EMA protocols specifically for resolving accelerometer ambiguities.** Most EMA batteries are designed for psychological research and include items that are irrelevant to PA/SB classification.
-   **Report temporal alignment methods in detail.** How EMA responses are matched to accelerometer epochs is rarely described with sufficient precision.
-   **Use event-triggered EMA.** Most studies use time-based or random prompting rather than sensor-triggered prompting, despite the clear advantages of the latter for temporal alignment Sigcha et al. (2025), (Delobelle et al., 2024; .
-   **Assess the modelling value of EMA variables.** No study systematically evaluates which EMA items provide the greatest incremental value for accelerometer-based classification.
-   **Handle missing EMA data rigorously.** Non-random missingness is acknowledged but rarely modelled or corrected.
-   **Collect activity domain/purpose consistently.** The most scientifically valuable contextual variable—why a person is active or sedentary—is rarely collected with sufficient specificity (Aunger & Wagnild, 2020; .
-   **Publish integrated datasets.** Publicly available datasets combining body-mounted accelerometer data with time-stamped EMA responses for PA/SB research are essentially non-existent.

### 13.3 What Everyone Should Do

1.  **Design EMA protocols that serve the accelerometer analysis.** If the research question involves PA/SB classification, the EMA items should be designed to provide labels and context that the accelerometer cannot capture. Generic psychological batteries should be replaced or supplemented with targeted PA/SB items.
    
2.  **Use event-triggered EMA for labelling.** Following the approach of Sigcha et al. (2025), EMA prompts should be triggered by sensor-detected activity transitions to ensure temporal alignment and contextual relevance. This can be supplemented with periodic random prompts for representative sampling.
    
3.  **Prioritise activity type, domain, and purpose.** The three most valuable EMA variables for PA/SB research are: (a) what the person is doing (activity type), (b) why they are doing it (purpose/domain), and (c) where they are doing it (location/setting). These should be collected using concise, mutually exclusive response options.
    
4.  **Treat EMA as weak supervision.** EMA labels should not be treated as ground truth but as noisy, sparse annotations that require appropriate statistical and machine learning methods. Semi-supervised learning, noise-robust training, and multi-instance learning are promising approaches that the field should adopt.
    
5.  **Report alignment methods and compliance in detail.** Studies should specify: (a) how EMA timestamps were matched to accelerometer epochs, (b) the distribution of prompt-response lags, (c) compliance rates by time of day and activity type, and (d) how missing EMA responses were handled.
    
6.  **Validate EMA labels against objective measures.** Where possible, EMA-reported activity should be compared against accelerometer-derived classifications (e.g., activPAL posture classification) to assess label quality Sigcha et al. (2025), (Kim et al., 2022).
    
7.  **Publish integrated datasets.** The field urgently needs publicly available datasets combining raw accelerometer data with time-stamped EMA responses, collected under well-documented free-living protocols. Such datasets would accelerate methodological development and enable reproducible research.
    
8.  **Optimise the burden-value tradeoff.** Every EMA item should be justified in terms of its expected contribution to the research question. Items that do not serve the accelerometer-based analysis should be removed or relegated to less frequent assessment occasions.
    
9.  **Develop and validate event-based EMA triggering algorithms.** Following (Delobelle et al., 2024; (Delobelle et al., 2024; , the accuracy of sensor-based EMA triggers should be validated against research-grade accelerometers before deployment in studies.
    
10.  **Bridge the gap between HAR and EMA literatures.** The HAR community has developed sophisticated classification algorithms Gao et al. (2021), Zhang et al., 2022) but relies on laboratory labels. The EMA community has developed rigorous real-time assessment methods Intille, 2007), Russell & Gajos, 2020) but rarely applies them to activity classification. Bridging these two literatures would yield substantial methodological advances.
    

### 13.4 Concluding Assessment

The integration of EMA with body-mounted accelerometer measurement for PA/SB research is a field of enormous potential but limited realisation. The conceptual case for combining objective movement measurement with real-time self-reported context is compelling and well-articulated (Aunger & Wagnild, 2020; , Spruijt‐Metz et al., 2018; , Intille, 2007). The technical infrastructure—smartphone-delivered EMA, research-grade accelerometers, event-triggered prompting—is mature and available Sigcha et al. (2025), (Delobelle et al., 2024; . Yet the actual published literature that rigorously implements this integration, particularly for classification and modelling purposes, is remarkably thin.

The WEALTH study by Sigcha et al. (2025) represents a watershed contribution that demonstrates what is possible when EMA is purposefully designed to serve accelerometer-based PA classification. The field needs more studies of this kind—studies that treat EMA not as an afterthought or a parallel data stream, but as an integral component of the measurement and modelling pipeline. Until this integration becomes standard practice, the field will continue to underexploit the complementary strengths of objective and subjective measurement in understanding human physical behaviour.

___

## Summary Table

|                       Study                       |                          Device                          |                  EMA Use                  |                       What It Adds                       |                              Limitations                               |           Burden           | Modelling Value |                Recommendation                |
|---------------------------------------------------|----------------------------------------------------------|-------------------------------------------|----------------------------------------------------------|------------------------------------------------------------------------|----------------------------|-----------------|----------------------------------------------|
|               Sigcha et al. (2025)                |           activPAL (thigh), ActiGraph, Fitbit            |    Labelling, validation, ML training     | Activity labels for 6 PA categories; up to 97% agreement |    Sparse labels; variable compliance; activity-dependent accuracy     | Moderate (event-triggered) |      **High**       |         Exemplar for future studies          |
|   (Brannon et al., 2016; (Brannon et al., 2016;   |             ActiGraph wActiSleep-BT (wrist)              | Feasibility, context, dynamical modelling |       Compliance benchmarks; psychosocial context        | Small sample; limited modelling; EMA not integrated with accelerometer | Moderate (4×/day, 20 days) |       Low       |          Good feasibility reference          |
|                Kratz et al. (2024)                |                ActiGraph wGT3X-BT (wrist)                |        Context, temporal dynamics         |         Symptom-activity temporal relationships          |   PA secondary to cognition; EMA not linked to accelerometer epochs    | Moderate (4×/day, 14 days) |  Low (for PA)   |           Useful protocol template           |
|        (Le et al., 2024; (Le et al., 2024;        |                Smartwatch (accelerometer)                |          High-density labelling           |          Dense activity labels (every 2–5 min)           |           Smartwatch-based; high burden; 67.7% response rate           | **High** (12–20 prompts/hour)  |  Moderate-high  | Innovative but needs dedicated accelerometer |
|       (Kim et al., 2022) (Kim et al., 2022)       |              activPAL (thigh) + smartwatch               |        In-situ labelling (speech)         |            Activity labels from older adults             |            Small sample; limited classification evaluation             |          Moderate          |    Moderate     |    Promising for older adult populations     |
| (Delobelle et al., 2024; (Delobelle et al., 2024; | ActiGraph GT3X+ (hip), activPAL4 (thigh), Fitbit (wrist) |    Validation of EMA trigger accuracy     |  Confirms Fitbit can trigger EMA/JITAI for PA/SB events  |               EMA not actually collected; 3-day protocol               |   Low (validation only)    | **High** (enabling) |         Essential prerequisite study         |


---

[1]
Objective and subjective measurement of sedentary behavior in human adults: A toolkit
Directly discusses objective and subjective measurement of sedentary behaviour, including activPAL, ActiGraph, and the complementarity of device-based and self-report methods for capturing context of sedentary behaviour in free-living conditions.

[3]
How to Measure Sedentary Behavior at Work?
Systematic review of methods to measure sedentary behaviour at work, including discussion of accelerometer cut-points and the complementary use of questionnaires and wearable devices.

[14]
Field evaluation of a random forest activity classifier for wrist-worn accelerometer data
Field evaluation of a random forest activity classifier for wrist-worn GENEActiv accelerometer data validated against activPAL, directly relevant to accelerometer-based PA classification methodology.

[17]
Data Labelling for Free-Living Physical Activity Recognition using Thigh-Worn Wearables and Event-based Ecological Momentary Assessment
Core included study: presents a novel framework integrating thigh-worn activPAL accelerometer data with event-based EMA for labelling free-living PA data and training ML classifiers. Most directly relevant study to the review scope.

[20]
Advances and Controversies in Diet and Physical Activity Measurement in Youth
Discusses advances in PA measurement in youth including EMA as a real-time self-report method alongside accelerometers, and the role of EMA in minimising recall bias for PA and SB assessment.

[22]
Optimizing Detection and Prediction of Cognitive Function in Multiple Sclerosis With Ambulatory Cognitive Tests: Protocol for the Longitudinal Observational CogDetect-MS Study
Describes the CogDetect-MS study protocol combining continuous wrist-worn ActiGraph accelerometry with 4×/day EMA for assessing physical activity, sleep, and symptoms in people with MS.

[27]
The Role of Remote Monitoring in Evaluating Fatigue in Multiple Sclerosis: A Review
Discusses EMA for fatigue monitoring in MS alongside wearable accelerometry for physical activity assessment, illustrating the combination of subjective momentary assessment with objective activity monitoring.

[35]
Collecting Self-reported Physical Activity and Posture Data Using Audio-based Ecological Momentary Assessment
Presents audio-based micro-EMA for collecting high-density self-reported physical activity and posture labels, directly relevant to EMA-based activity labelling for HAR systems.

[42]
The Dilemma of Analyzing Physical Activity and Sedentary Behavior with Wrist Accelerometer Data: Challenges and Opportunities
Comprehensive review of wrist-worn accelerometer data analysis methods for PA and SB, providing essential context on accelerometer data processing challenges that EMA could help address.

[43]
MyMove: Facilitating Older Adults to Collect In-Situ Activity Labels on a Smartwatch with Speech
Describes MyMove system for collecting in-situ activity labels from older adults using speech input on a smartwatch, with activPAL as reference measure for walking cadence.

[45]
Technological Innovations Enabling Automatic, Context-Sensitive Ecological Momentary Assessment
Foundational work on context-sensitive EMA using automatic activity detection from body-worn accelerometers, directly relevant to the conceptual framework of integrating EMA with accelerometer-based PA monitoring.

[51]
The promise of wearable sensors and ecological momentary assessment measures for dynamical systems modeling in adolescents: a feasibility and acceptability study
Directly assesses feasibility and acceptability of combining ActiGraph accelerometer with intensive EMA in adolescents for studying PA, sleep, and psychosocial variables.

[53]
Fitbit's accuracy to measure short bouts of stepping and sedentary behaviour: validation, sensitivity and specificity study
Validates Fitbit accuracy for detecting stepping and sedentary bouts against ActiGraph and activPAL, specifically in the context of triggering EMA/JITAI prompts for PA/SB studies.

[57]
Annual Research Review: Ecological momentary assessment studies in child psychology and psychiatry
Reviews EMA studies in child psychology including those combining EMA with wearable accelerometers for PA assessment, providing context on how EMA captures PA contexts and validates self-reported activity.

[67]
Methods of Measurement in epidemiology: Sedentary Behaviour
Foundational epidemiological review of sedentary behaviour measurement methods including accelerometers and the limitations of objective measures in capturing behavioural context.

[85]
Ambulatory Activity Monitoring
Discusses ambulatory activity monitoring methodology including the combination of objective activity measurement with simultaneous assessment of emotions, mood, and context.

[88]
Deep Learning in Human Activity Recognition with Wearable Sensors: A Review on Advances
Comprehensive review of deep learning methods for wearable-based HAR, providing context on the state of activity classification algorithms that EMA could support through labelling.