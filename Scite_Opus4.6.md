## The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

___

## 1\. Executive Summary

Ecological Momentary Assessment (EMA) has emerged as a critical methodological complement to body-mounted accelerometer sensing in physical activity (PA) and sedentary behaviour (SB) research. While accelerometers such as the activPAL, ActiGraph, Axivity, and GENEActiv provide objective, continuous, and temporally dense data on movement intensity, posture, and step counts, they are fundamentally limited in their capacity to capture the _context_, _purpose_, _domain_, and _subjective experience_ of physical behaviours Aunger & Wagnild (2020), Atkin et al., 2012), (Intille, 2007). EMA—defined as the repeated, real-time or near-real-time collection of self-reported data in participants' natural environments Atkin et al., 2012), Maher et al. (2018)—addresses these gaps by providing information on what participants are doing, why, where, with whom, and how they feel during accelerometer-monitored periods.

This synthesis examines the narrow intersection of body-mounted accelerometer sensing and EMA in PA/SB research. It finds that EMA is most commonly used for contextual enrichment (e.g., identifying behavioural domain, social context, location) and for validating or interpreting accelerometer-derived outputs, but is underutilised as a direct labelling source for activity classification algorithms (Sigcha et al., 2025). The literature reveals recurring methodological challenges in aligning sparse, episodic EMA responses with dense, continuous accelerometer streams, and a persistent gap between the collection of EMA data and its meaningful integration into modelling pipelines (Intille, 2007), (Sigcha et al., 2025). Best practice requires careful attention to prompt design, temporal alignment, burden minimisation, and explicit integration of EMA into analytic workflows.

___

## 2\. Scope Definition and Inclusion Logic

This review is strictly limited to studies where:

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

2.  **Primary movement data** come from a **body-mounted accelerometer device** (not a smartphone). Eligible devices include the activPAL, ActiGraph (GT3X, GT3X+, GT9X, wGT3X-BT), Axivity (AX3, AX6), GENEActiv, SENS Motion, DynaPort, and similar dedicated research-grade wearable accelerometer systems Aunger & Wagnild (2020), Giurgiu et al., 2023; , Wullems et al., 2024).
3.  The focus is on **physical activity**, **sedentary behaviour**, **posture/movement behaviour**, **activity classification/human activity recognition**, or **free-living physical behaviour assessment** Aunger & Wagnild (2020), Atkin et al., 2012), Gao et al., 2021).
4.  An **EMA or closely related momentary self-report component** (experience sampling, ambulatory self-report, mobile diary, prompted self-report) is present alongside the accelerometer data collection Atkin et al., 2012), Maher et al. (2018), (Sigcha et al., 2025).

**Excluded** are studies primarily focused on smartphone accelerometry, physiological monitoring (HR, PPG, ECG, EEG, EMG, respiration, skin conductance), general digital phenotyping not centred on accelerometer-based PA, rehabilitation biomechanics without free-living PA focus, and purely lab-based motion recognition without relevance to real-world PA data collection using wearable accelerometers plus EMA.

___

## 3\. What EMA Contributes Beyond Body-Mounted Accelerometers

### 3.1 The Fundamental Limitation of Accelerometers

Body-mounted accelerometers, regardless of placement (hip, wrist, thigh), measure acceleration in one to three orthogonal planes and can derive metrics such as activity counts, step counts, energy expenditure estimates, time in intensity categories (sedentary, light, moderate, vigorous), and—when thigh-mounted—posture (sitting, standing, lying) Aunger & Wagnild (2020), Gao et al., 2021), Atkin et al., 2012). The activPAL, for example, is validated as a gold-standard inclinometer for measuring total sedentary time and postural transitions Aunger & Wagnild (2020), Maher et al. (2018), Delobelle et al. (2024). The ActiGraph and GENEActiv, when worn on the wrist or hip, provide intensity-based classifications but cannot reliably distinguish postures Aunger & Wagnild (2020), Gao et al., 2021), Sheldrick, n.d.).

However, accelerometers—even the most sophisticated—cannot determine:

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   **What activity** is being performed (e.g., watching TV vs. reading vs. working at a desk during sitting) Aunger & Wagnild (2020), Atkin et al., 2012)
-   **The domain** of activity (occupational, leisure, transport, household) Aunger & Wagnild (2020), Edney et al., 2022;
-   **The purpose** of movement (exercise vs. commuting vs. household chores) (Intille, 2007), Edney et al., 2022;
-   **The social context** (alone, with family, with colleagues) Maher et al. (2018), Edney et al., 2022;
-   **The physical environment** (indoor/outdoor, home/workplace/park) Edney et al., 2022; , Knell et al., 2017)
-   **Subjective states** (mood, fatigue, perceived exertion, motivation, barriers) (Maher et al., 2023; , (Brannon et al., 2016;
-   **Intentionality** (planned exercise vs. incidental movement) (Intille, 2007)

As Aunger and Wagnild Aunger & Wagnild (2020) summarise: "Objective measures such as inclinometers are the gold-standard for measuring total sedentary time but they typically cannot capture contextual information or determine which specific behaviors are taking place." This is the fundamental gap that EMA is designed to fill.

### 3.2 How EMA Differs from Other Assessment Methods

EMA is distinct from several related but different assessment approaches:

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   **Passive sensing** (accelerometry, GPS, light sensors): Provides continuous, objective data but no subjective or contextual information. EMA adds the participant's voice Atkin et al., 2012), (Intille, 2007).
-   **Retrospective questionnaires** (IPAQ, GPAQ, BRFSS): Assess PA/SB over days, weeks, or months, but are subject to recall bias and measurement error. EMA minimises recall by assessing current or very recent behaviour Atkin et al., 2012), Knell et al., 2017), Prince et al. (2020). Prince et al. Prince et al. (2020) found that single-item self-report measures generally underestimate sedentary time compared to device measures, while EMAs and logs/diaries with shorter recall periods performed better.
-   **Time-use diaries** (e.g., ACT24): Provide detailed 24-hour recall of activities and contexts, but are completed retrospectively and are burdensome. EMA captures data closer to the moment of occurrence ("The 8th International Conference on Ambulatory Monitoring of Physical Activity and Movement", 2022; , Atkin et al., 2012).
-   **Direct observation**: Considered the gold standard for activity type and context, but is costly, invasive, and impractical for large-scale or long-duration free-living studies ("The 8th International Conference on Ambulatory Monitoring of Physical Activity and Movement", 2022; , (Pavey et al., 2017; , (Intille, 2007).
-   **Video annotation**: Used in laboratory and semi-structured settings as a criterion measure for algorithm development ("The 8th International Conference on Ambulatory Monitoring of Physical Activity and Movement", 2022; , Stewart, n.d.; , Hendry et al., 2023), but not feasible for extended free-living monitoring.
-   **Labelling protocols in controlled studies**: Provide precise, researcher-assigned labels for structured activities, but do not generalise well to the variability of free-living behaviour (Pavey et al., 2017; , (Sigcha et al., 2025).

### 3.3 What EMA Is in This Field

In the narrow context of body-mounted accelerometer studies of PA and SB, EMA is best understood as a **multi-functional tool** that serves several overlapping roles:

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   **Contextual metadata**: Providing information about the domain, location, social setting, and purpose of accelerometer-detected movement or sedentary periods Maher et al. (2018), Edney et al., 2022; , Knell et al., 2017).
-   **Behavioural interpretation layer**: Helping researchers understand _why_ a particular pattern of movement or non-movement occurred (Maher et al., 2023; , Maher et al. (2018).
-   **Near-ground truth for activity type**: Offering participant-reported labels of current or recent activity, which—while imperfect—are the closest feasible approximation to ground truth in free-living conditions Knell et al., 2017), (Sigcha et al., 2025).
-   **Subjective state capture**: Recording affect, fatigue, perceived exertion, motivation, and barriers that cannot be inferred from accelerometry (Maher et al., 2023; , (Brannon et al., 2016; .
-   **Compliance and quality-control signal**: Confirming device wear, identifying non-wear periods, and supporting data cleaning Aunger & Wagnild (2020), Arguello et al., 2023).
-   **Weak label source for algorithm development**: Providing sparse, noisy, but ecologically valid labels that can be used to train or validate activity recognition models (Sigcha et al., 2025).

It is important to note that EMA is **not** ground truth in the strict sense used in machine learning. EMA responses are subject to self-report bias, temporal imprecision, and missingness. However, in free-living conditions where direct observation is infeasible, EMA represents the most practical source of contextual and activity-type information (Intille, 2007), Knell et al., 2017), (Sigcha et al., 2025).

___

## 4\. How EMA Is Used in Physical Activity and Sedentary Behaviour Studies

### 4.1 Contextualising Accelerometer-Derived Behaviour

The most established use of EMA in this literature is to provide context that accelerometers cannot capture. Maher et al. Maher et al. (2018) demonstrated that EMA is a feasible and valid tool for assessing older adults' PA and SB, with EMA-reported PA and SB positively associated with activPAL-measured PA and SB in the ±15 minutes surrounding the EMA prompt. This study exemplifies the use of EMA to validate and contextualise device-based measures.

Edney et al. Edney et al., 2022; describe the COBRA study protocol, which combines wrist-worn Axivity accelerometers and thigh-worn accelerometers with six daily EMA surveys to capture eating behaviours, movement behaviours, and contextual factors (location, social context, indoor/outdoor) in free-living conditions. This represents a comprehensive integration of EMA with body-mounted accelerometry for understanding the environmental and social determinants of PA and SB.

### 4.2 Validating Accelerometer Outputs

EMA has been used to validate accelerometer-derived estimates of PA and SB. Knell et al. Knell et al., 2017) compared EMA-assessed PA with ActiGraph GT3X accelerometer data and found that EMA showed better correlation and agreement with accelerometer estimates than traditional self-report questionnaires (IPAQ, BRFSS). This supports the use of EMA as a more ecologically valid self-report method for PA assessment.

### 4.3 Understanding Motivational and Psychological Processes

Project SMART (Maher et al., 2023; uses ActiGraph GT3X (waist) and activPAL micro4 (thigh) accelerometers alongside 10 randomly prompted EMA questionnaires per day to assess reflective processes (self-efficacy, self-control) and reactive processes (contextual cues) regulating PA and SB in older adults. This study exemplifies the use of EMA to understand the psychological mechanisms underlying accelerometer-measured behaviour.

### 4.4 Labelling Free-Living Data for Algorithm Development

Sigcha et al. (Sigcha et al., 2025) present a novel framework that integrates thigh-worn activPAL accelerometer data with event-based EMA surveys to label different types of PA in free-living settings. EMA responses were synchronised with accelerometer signals to create a sparse labelled dataset, which was compared against ground-truth labels generated by the proprietary activPAL CREA algorithm. The framework achieved up to 97% agreement with ground-truth data for labelling six PA categories, and a machine learning algorithm trained on the resulting dataset achieved classification accuracies of up to 73.6%. This represents the most direct and rigorous use of EMA as a labelling source for activity classification in the body-mounted accelerometer literature.

___

## 5\. Role of EMA in Labelling, Validation, and Algorithm Development

### 5.1 EMA as a Direct Label Source

The use of EMA as a direct label source for activity classification is an emerging but still uncommon practice. Sigcha et al. (Sigcha et al., 2025) demonstrate that event-based EMA—triggered automatically by sensor-detected activities—can generate time-stamped labels that are synchronised with accelerometer data. Their framework shows high labelling accuracy for activities such as sitting and running, but lower accuracy for more ambiguous activities. This approach is promising but faces challenges related to label sparsity, temporal alignment, and participant compliance.

### 5.2 EMA as a Weak Label Source

In most studies, EMA provides what can be characterised as "weak labels"—self-reported activity types or contexts that are temporally imprecise, subject to recall bias, and available only at discrete time points rather than continuously. These weak labels are nonetheless valuable for:

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   Training machine learning models when no other free-living labels are available (Sigcha et al., 2025)
-   Providing contextual features (e.g., location, social setting) that can improve classification accuracy Edney et al., 2022;
-   Identifying periods of specific activity types for targeted analysis Maher et al. (2018), Knell et al., 2017)

### 5.3 EMA as a Validation Source

EMA is frequently used to validate accelerometer-derived classifications. For example, Maher et al. Maher et al. (2018) used EMA-reported PA and SB to assess the criterion validity of activPAL-measured behaviour, finding positive associations between EMA reports and device-based measures. Knell et al. Knell et al., 2017) similarly used EMA to validate ActiGraph-derived PA estimates.

### 5.4 EMA as a Contextual Feature Source

In studies that aim to develop context-aware models of PA and SB, EMA provides features that cannot be derived from accelerometry alone. The COBRA study Edney et al., 2022; collects EMA data on location, social context, and environmental factors alongside Axivity accelerometer data, enabling analyses of how contextual factors influence movement behaviours.

### 5.5 EMA as an Error-Analysis Aid

EMA can help identify sources of error in accelerometer-derived classifications. For example, when an accelerometer classifies a period as sedentary, EMA can reveal whether the participant was sitting at a desk (true sedentary) or standing still (misclassified sedentary) Aunger & Wagnild (2020), Atkin et al., 2012). This is particularly relevant for hip- and wrist-worn accelerometers, which cannot distinguish postures Aunger & Wagnild (2020), Gao et al., 2021).

### 5.6 EMA as a Compliance and Quality-Control Signal

Several studies use EMA to confirm device wear and identify non-wear periods. Maher et al. Maher et al. (2018) excluded occasions when participants indicated via EMA that they were not wearing the activPAL, and used sleep/wake logs to align EMA data with the definition of SB as a waking behaviour. The activPAL study by Arguello et al. Arguello et al., 2023) similarly uses daily logs to self-report time-in-bed and non-wear periods.

### 5.7 Limitations of EMA for Algorithm Development

Despite its potential, EMA has significant limitations as a labelling source for algorithm development:

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   **Sparsity**: EMA provides labels at discrete time points (typically 4–10 per day), while accelerometers generate continuous data at 25–100 Hz (Sigcha et al., 2025), (Maher et al., 2023; .
-   **Temporal imprecision**: There is often a lag between the EMA prompt and the participant's response, and the recall window may not align precisely with the accelerometer segment of interest (Intille, 2007), (Sigcha et al., 2025).
-   **Self-report bias**: Participants may misreport or simplify their activities, particularly for light or ambiguous behaviours Prince et al. (2020), Knell et al., 2017).
-   **Missingness**: EMA compliance rates, while generally acceptable (often 70–92%), mean that a substantial proportion of accelerometer data lacks corresponding EMA labels (Maher et al., 2023; , (Brannon et al., 2016; , Maher et al. (2018).

The literature suggests that EMA is most useful for algorithm development when combined with event-based triggering (which improves temporal alignment) and when used to label broad activity categories rather than fine-grained activity types (Sigcha et al., 2025).

___

## 6\. Common EMA Variables Collected in This Literature

### 6.1 Variables Commonly Collected

Based on the reviewed literature, the following EMA variables are commonly collected in body-mounted accelerometer studies of PA and SB:

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

|                 **EMA Variable**                  |  **Frequency in Literature**   |                           **Example Studies**                           |
|-----------------------------------------------|----------------------------|---------------------------------------------------------------------|
|         Current/recent activity type          |           Common           |   Maher et al. (2018), Knell et al., 2017), (Sigcha et al., 2025)   |
|      Posture (sitting, standing, lying)       |           Common           |               Maher et al. (2018), Kim et al., 2022)                |
|        Location (home, work, outdoors)        |           Common           |              Edney et al., 2022; , Knell et al., 2017)              |
|      Social context (alone, with others)      |          Moderate          |             (Maher et al., 2023; , Edney et al., 2022;              |
|                  Affect/mood                  |          Moderate          | (Maher et al., 2023; , (Brannon et al., 2016; , Edney et al., 2022; |
|                    Fatigue                    |          Moderate          |                        (Maher et al., 2023;                         |
|              Perceived exertion               |            Rare            |                                  —                                  |
| Domain of activity (work, leisure, transport) |          Moderate          |              Edney et al., 2022; , Knell et al., 2017)              |
|                Indoor/outdoor                 |          Moderate          |                         Edney et al., 2022;                         |
|              Purpose of movement              |            Rare            |                                  —                                  |
|              Barriers/motivation              |          Moderate          |                        (Maher et al., 2023;                         |
|                 Pain/symptoms                 | Rare in PA-focused studies |                                  —                                  |
|             Compliance/wear-time              |           Common           |             Maher et al. (2018), Arguello et al., 2023)             |

### 6.2 Assessment of Variable Utility

**Highly useful variables:**

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   **Current activity type**: Directly addresses the primary limitation of accelerometers (inability to identify activity type) and is essential for labelling and validation Maher et al. (2018), Knell et al., 2017), (Sigcha et al., 2025).
-   **Location/setting**: Enables domain-specific analyses (e.g., occupational vs. leisure sedentary time) that are critical for public health research Aunger & Wagnild (2020), Edney et al., 2022; .
-   **Social context**: Provides information on social determinants of PA/SB that cannot be inferred from accelerometry (Maher et al., 2023; , Edney et al., 2022; .

**Moderately useful variables:**

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   **Affect/mood**: Enables investigation of affective antecedents and consequences of PA/SB, but adds burden and is not directly relevant to activity classification (Maher et al., 2023; , (Brannon et al., 2016; .
-   **Fatigue**: Relevant for understanding barriers to PA, particularly in clinical populations, but adds burden (Maher et al., 2023; .
-   **Domain of activity**: Highly valuable for distinguishing occupational from leisure PA/SB, but requires careful question design Edney et al., 2022; .

**Scientifically attractive but operationally weak variables:**

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   **Perceived exertion**: Theoretically valuable for validating intensity classifications, but rarely collected and difficult to assess momentarily without disrupting activity.
-   **Purpose of movement**: Would enable distinction between intentional exercise and incidental activity, but is difficult to operationalise in brief EMA surveys.
-   **Barriers/motivation**: Important for intervention research but adds substantial burden and is not directly useful for activity classification.

### 6.3 Burden Considerations

EMA burden is a critical consideration. Brannon et al. (Brannon et al., 2016; found that adolescents provided approximately 81% of expected survey data in a 20-day protocol with four surveys per day, but compliance with physiological monitors was lower. Maher et al. Maher et al. (2018) reported 92% compliance with six daily EMA prompts over 10 days in older adults. The PHIAT project Hakun et al., 2025) used six assessments per day over 14 days. Project SMART (Maher et al., 2023; used 10 randomly prompted EMAs per day on 4 selected days per data collection period.

The evidence suggests that 4–6 prompts per day is a sustainable frequency for most populations, with compliance declining at higher frequencies and over longer monitoring periods (Brannon et al., 2016; , Maher et al. (2018). Each EMA survey should be brief (typically 1–3 minutes) to minimise disruption to the behaviours being studied Maher et al. (2018).

___

## 7\. Methodological Challenges in Linking EMA to Accelerometer Data

### 7.1 Timestamp Alignment

The most fundamental challenge is aligning sparse, episodic EMA responses with dense, continuous accelerometer time series. Accelerometers typically sample at 25–100 Hz and generate millions of data points per day, while EMA provides 4–10 data points per day (Sigcha et al., 2025), (Maher et al., 2023; . Sigcha et al. (Sigcha et al., 2025) address this by synchronising EMA responses with accelerometer signals using event-based triggers, but this approach requires sophisticated infrastructure and is not yet standard practice.

### 7.2 Prompt-Response Lag

There is typically a delay between the EMA prompt and the participant's response. During this delay, the participant's activity may change, creating a mismatch between the reported activity and the accelerometer data at the time of the prompt. Maher et al. Maher et al. (2018) addressed this by examining accelerometer data in the ±15 minutes surrounding the EMA prompt, finding that PA was lower in the 15 minutes after compared to the 15 minutes before the prompt, suggesting possible reactance or disruption of PA by the EMA prompt itself.

### 7.3 Recall Window Mismatch

EMA questions may ask about "current" activity, "activity in the last 15 minutes," or "activity since the last prompt." Each framing creates different temporal alignment challenges. Questions about current activity provide the most precise temporal linkage but may capture only a snapshot. Questions about recent activity provide broader coverage but introduce recall bias Atkin et al., 2012), Knell et al., 2017).

### 7.4 Sparse Labels versus Continuous Sensor Streams

Even with high EMA compliance, the vast majority of accelerometer data remains unlabelled. Sigcha et al. (Sigcha et al., 2025) explicitly address this challenge, noting that their framework produces a "sparse labelled dataset" that must be compared against algorithmic ground truth. This sparsity limits the utility of EMA for training data-hungry machine learning models and necessitates strategies such as label propagation, semi-supervised learning, or the use of EMA labels for validation rather than training.

### 7.5 Missing EMA Responses

EMA compliance is never 100%. Missing responses create gaps in the labelled dataset that may be non-random—participants may be less likely to respond during vigorous activity, social situations, or sleep transitions Maher et al. (2018), (Brannon et al., 2016; . This non-random missingness can bias analyses and model training.

### 7.6 Self-Report Bias

Participants may misreport activities due to social desirability, cognitive limitations, or difficulty categorising ambiguous behaviours. Prince et al. Prince et al. (2020) found substantial variability in self-reported sedentary time compared to device measures, with up to 6 hours/day of discrepancy within individual studies. Light-intensity activities and sedentary behaviours are particularly difficult to recall accurately Atkin et al., 2012), Prince et al. (2020).

### 7.7 Strategies for Alignment

Studies use several strategies to align EMA with accelerometer data:

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   **Fixed time windows**: Examining accelerometer data in a defined window (e.g., ±15 minutes) around the EMA prompt Maher et al. (2018).
-   **Event-based triggering**: Using sensor-detected events (e.g., transitions from sitting to walking) to trigger EMA prompts, improving temporal alignment (Sigcha et al., 2025).
-   **Day-level aggregation**: Comparing daily summaries of EMA-reported and accelerometer-measured PA/SB Knell et al., 2017).
-   **Bout-level matching**: Aligning EMA responses with accelerometer-derived activity bouts (Sigcha et al., 2025).

Event-based triggering appears to be the strongest approach for temporal alignment, as it ensures that the EMA prompt is temporally proximal to the behaviour of interest (Sigcha et al., 2025). However, this approach requires real-time processing of accelerometer data and sophisticated triggering algorithms, which are not yet widely available.

___

## 8\. Common Weaknesses and Blind Spots

### 8.1 EMA Collected but Not Integrated into Modelling

A recurring weakness in this literature is the collection of EMA data that is not meaningfully integrated into analytic or modelling workflows. Many studies collect EMA alongside accelerometer data but analyse them separately, missing opportunities for multimodal integration (Intille, 2007). Sigcha et al. (Sigcha et al., 2025) represent an exception, explicitly using EMA as a labelling source for machine learning, but this approach remains uncommon.

### 8.2 Poor Reporting of Compliance

Many studies do not adequately report EMA compliance rates, response latencies, or patterns of missingness. Without this information, it is difficult to assess the quality and representativeness of the EMA data (Brannon et al., 2016; , Maher et al. (2018).

### 8.3 Poor Handling of Missingness

When EMA compliance is reported, studies rarely address the implications of missing data for their analyses. Non-random missingness—where participants are less likely to respond during certain activities or states—can bias results but is seldom modelled or corrected Maher et al. (2018).

### 8.4 Weak Temporal Alignment Methods

Many studies use crude temporal alignment methods (e.g., day-level aggregation) that fail to exploit the temporal precision of both EMA and accelerometer data. More sophisticated approaches, such as event-based triggering or bout-level matching, are underutilised (Sigcha et al., 2025).

### 8.5 Limited Use of EMA for Sedentary Behaviour Interpretation

Despite the well-recognised limitation that accelerometers cannot distinguish between different types of sedentary behaviour (e.g., TV watching vs. desk work vs. reading) Aunger & Wagnild (2020), Atkin et al., 2012), EMA is rarely used systematically to characterise the context and type of sedentary episodes. Aunger and Wagnild Aunger & Wagnild (2020) recommend that "self-report methods are recommended for measuring time spent in particular contexts of sedentary behavior," but this recommendation is inconsistently implemented.

### 8.6 Lack of Attention to Domain Context

Few studies use EMA to systematically distinguish between occupational, leisure, transport, and household PA or SB, despite the well-established importance of domain-specific analyses for public health Aunger & Wagnild (2020), Edney et al., 2022; . The COBRA study Edney et al., 2022; is a notable exception.

### 8.7 Collecting Burdensome Items with Little Modelling Value

Some studies include EMA items (e.g., detailed mood scales, extensive symptom checklists) that add participant burden without contributing to the primary research question of PA/SB assessment. This can reduce compliance with the core EMA items that are most relevant to accelerometer data interpretation (Brannon et al., 2016; .

### 8.8 Failure to Use EMA to Resolve Accelerometer Ambiguity

Accelerometers frequently produce ambiguous classifications—for example, a hip-worn ActiGraph may classify standing still as sedentary Aunger & Wagnild (2020), Sheldrick, n.d.), or a wrist-worn device may classify arm movements during seated activities as PA Gao et al., 2021), Sheldrick, n.d.). EMA could be used to resolve these ambiguities, but this application is rarely exploited.

### 8.9 Limited Integration of EMA into Activity Recognition Pipelines

The activity recognition and human activity recognition (HAR) literatures have largely developed independently of the EMA literature. HAR studies typically use laboratory-derived labels or direct observation as ground truth (Pavey et al., 2017; , Hendry et al., 2023), while EMA studies focus on contextual and psychological variables. The integration of EMA into HAR pipelines for free-living data is a significant gap (Sigcha et al., 2025).

___

## 9\. Best-Practice Recommendations for Future Studies

### 9.1 For Physical Activity Classification

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   Use **event-based EMA** triggered by sensor-detected activity transitions to maximise temporal alignment between EMA labels and accelerometer data (Sigcha et al., 2025).
-   Collect **activity type** (e.g., walking, cycling, household chores, exercise) as the primary EMA variable.
-   Use brief, structured response options (e.g., dropdown menus) rather than open-ended questions to facilitate automated label extraction.
-   Report EMA compliance rates, response latencies, and patterns of missingness.
-   Explicitly integrate EMA labels into machine learning pipelines, either as training labels, validation labels, or contextual features (Sigcha et al., 2025).

### 9.2 For Sedentary Behaviour Interpretation

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   Use **thigh-worn accelerometers** (e.g., activPAL) as the primary device for posture classification, supplemented by EMA to identify the type and context of sedentary episodes Aunger & Wagnild (2020), Maher et al. (2018).
-   Collect EMA variables on **what the participant is doing while sedentary** (e.g., watching TV, working at a computer, socialising, eating) and **where** (home, work, transport) Aunger & Wagnild (2020), Edney et al., 2022; .
-   Use EMA to distinguish between **occupational and leisure sedentary time**, which have different health implications Aunger & Wagnild (2020), Boudet et al., 2019).

### 9.3 For Context-Aware Behaviour Analysis

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   Collect EMA variables on **location** (home, work, outdoors, transport), **social context** (alone, with family, with colleagues), and **indoor/outdoor** status Edney et al., 2022; .
-   Combine EMA with GPS data where feasible to provide both subjective and objective context Edney et al., 2022; .
-   Use EMA to capture **purpose of movement** (exercise, commuting, household chores) to enable domain-specific analyses.

### 9.4 For Multimodal Algorithm Development

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   Design EMA protocols with **algorithm development** as an explicit goal, not just as a secondary data source.
-   Use **event-based triggering** to generate temporally precise labels (Sigcha et al., 2025).
-   Develop **semi-supervised or weakly supervised learning** approaches that can leverage sparse EMA labels alongside dense accelerometer data.
-   Use EMA as a **validation source** for algorithm outputs, comparing algorithm-predicted activity types with EMA-reported activity types.
-   Consider **active learning** approaches where the algorithm identifies uncertain classifications and triggers targeted EMA prompts.

### 9.5 Balancing Burden and Scientific Value

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

-   Limit EMA prompts to **4–6 per day** for studies lasting 7–14 days (Maher et al., 2023; , Maher et al. (2018).
-   Keep each EMA survey to **1–3 minutes** maximum.
-   Prioritise **activity type**, **location**, and **social context** as core EMA variables.
-   Add **affect**, **fatigue**, or **motivation** only when these are primary research questions.
-   Use **event-based prompts** where possible to reduce unnecessary prompting during periods of stable behaviour.
-   Monitor compliance in real time and provide reminders or incentives as needed.

___

## 10\. Representative Studies and Datasets

### 10.1 Project SMART (Maher et al., 2023;

**Devices**: ActiGraph GT3X (waist) + activPAL micro4 (thigh) **EMA**: 10 randomly prompted surveys per day on 4 selected days per 14-day data collection period, delivered via smartphone **Population**: Older adults (≥60 years) engaging in ≥30 min MVPA/week **EMA variables**: Reflective processes (self-efficacy, self-control), reactive processes (contextual cues), PA and SB context **Contribution**: Demonstrates the use of dual accelerometer placement (waist + thigh) with intensive EMA to model motivational processes regulating PA and SB adoption and maintenance in older adults (Maher et al., 2023; . **Limitation**: High EMA frequency (10/day) may be burdensome; EMA is used primarily for psychological process modelling rather than activity labelling.

### 10.2 Maher et al. (2018) – EMA Feasibility and Validity in Older Adults

**Device**: activPAL (thigh) **EMA**: 6 randomly prompted surveys per day over 10 days, delivered via smartphone **Population**: 104 older adults (60–98 years) **EMA variables**: Current PA or SB **Contribution**: Established the feasibility and criterion validity of EMA for assessing PA and SB in older adults, with 92% compliance and positive associations between EMA-reported and activPAL-measured behaviour Maher et al. (2018). **Limitation**: EMA assessed only binary PA/SB status, not activity type or context. Possible PA reactance to EMA prompting was observed.

### 10.3 Knell et al., 2017) – EMA Validation Against Accelerometry

**Device**: ActiGraph GT3X (waist) **EMA**: Daily diary EMAs delivered via mobile phone over 7 days **Population**: 238 adults (diverse, low-income) **EMA variables**: Sedentary time, moderate/vigorous PA **Contribution**: Demonstrated that EMA showed better correlation and agreement with accelerometer estimates than traditional self-report questionnaires (IPAQ, BRFSS) Knell et al., 2017). **Limitation**: EMA assessed PA intensity categories rather than activity type or context.

### 10.4 COBRA Study Edney et al., 2022;

**Devices**: Axivity accelerometers (wrist + thigh) **EMA**: 6 surveys per day over 9 consecutive days, GPS-enabled smartphone app **Population**: 1500 adults (21–69 years) in Asia **EMA variables**: Eating behaviours, movement behaviours, location, social context, indoor/outdoor, contextual determinants **Contribution**: Represents one of the most comprehensive integrations of body-mounted accelerometry with EMA for understanding dietary and movement behaviours in free-living conditions Edney et al., 2022; . **Limitation**: Protocol paper; results not yet published. The complexity of the protocol may limit compliance.

### 10.5 WEALTH Study / (Sigcha et al., 2025)

**Devices**: activPAL (thigh), ActiGraph, Fitbit, Skagen Falster smartwatch **EMA**: Event-based EMA triggered by sensor-detected activities, delivered via HealthReact smartphone app **Population**: 589 participants over 7-day monitoring period **EMA variables**: Activity type (immediately following detected activity) **Contribution**: The most direct and rigorous use of EMA as a labelling source for activity classification in free-living conditions. Achieved up to 97% agreement with ground-truth labels and 73.6% classification accuracy with machine learning (Sigcha et al., 2025). **Limitation**: Event-based EMA may miss activities that do not trigger the detection algorithm. Label sparsity remains a challenge.

### 10.6 PHIAT Project Hakun et al., 2025)

**Devices**: ActiGraph (hip), activPAL (thigh), consumer wearable (wrist) **EMA**: 6 assessments per day over 14 days, including ultra-brief ambulatory cognitive assessments **Population**: 221 adults (18–89 years) **EMA variables**: Motivation, intention, stress, built environment, social cognitive factors, diet, hydration, PA, exercise **Contribution**: Demonstrates the integration of multiple body-mounted accelerometers with high-frequency EMA and ambulatory cognitive assessments for studying self-regulation of health-promoting behaviour across the adult lifespan Hakun et al., 2025). **Limitation**: Complex protocol with multiple devices and assessments; burden may limit generalisability.

### 10.7 (Brannon et al., 2016; – Feasibility of EMA with Wearable Sensors in Adolescents

**Device**: ActiGraph (wrist) **EMA**: 4 surveys per day over 20 days, delivered via smartphone app **Population**: 20 adolescents **EMA variables**: Psychosocial variables, behaviour **Contribution**: Demonstrated the feasibility of intensive EMA combined with wrist-worn accelerometry for studying real-time relationships between biopsychosocial variables and health behaviours in adolescents (Brannon et al., 2016; . **Limitation**: Small sample size; physiological monitor compliance was lower than accelerometer compliance.

### 10.8 Delobelle et al. (2024) – Fitbit Accuracy for EMA-Triggered Studies

**Devices**: Fitbit (wrist), ActiGraph GT3X+ (hip), activPAL (thigh) **Population**: 37 adults (18–65) + 32 older adults (65+) **Contribution**: Assessed the suitability of Fitbit devices for real-time PA and SB monitoring in the context of just-in-time adaptive interventions (JITAIs) and event-based EMA studies. Found that Fitbits detected stepping bouts with sensitivities and specificities exceeding 87% and 97%, respectively, and identified optimal cut-off values for prolonged sitting bouts Delobelle et al. (2024). **Limitation**: Focused on device validation rather than EMA content or integration.

___

## 11\. Final Synthesis: What Everyone Does, What They Do Not Do, and What They Should Do

### 11.1 What Everyone Does

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

2.  **Collects EMA alongside accelerometer data**: Most studies in this narrow field use EMA as a complementary data source to body-mounted accelerometers, typically delivering 4–10 prompts per day via smartphone (Maher et al., 2023; , Maher et al. (2018), Edney et al., 2022; , Knell et al., 2017).
3.  **Uses EMA for contextual enrichment**: The primary use of EMA is to provide information about the context of accelerometer-measured behaviour—location, social setting, activity type Maher et al. (2018), Edney et al., 2022; .
4.  **Validates EMA against accelerometer data**: Studies commonly compare EMA-reported PA/SB with accelerometer-derived measures to establish criterion validity Maher et al. (2018), Knell et al., 2017).
5.  **Reports high compliance rates**: EMA compliance in this literature is generally high (70–92%), supporting the feasibility of the approach (Maher et al., 2023; , (Brannon et al., 2016; , Maher et al. (2018).
6.  **Uses random or fixed-time prompts**: Most studies use time-based (random or fixed-schedule) EMA prompts rather than event-based triggers (Maher et al., 2023; , Maher et al. (2018), Knell et al., 2017).
7.  **Employs thigh-worn activPAL for sedentary behaviour**: The activPAL is the most common device for posture-based SB assessment, often paired with EMA for contextual information Aunger & Wagnild (2020), (Maher et al., 2023; , Maher et al. (2018), Arguello et al., 2023).

### 11.2 What Everyone Does Not Do

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

2.  **Integrate EMA into machine learning pipelines**: Despite collecting EMA data, most studies do not use EMA labels as training data, validation data, or contextual features in activity classification models. Sigcha et al. (Sigcha et al., 2025) is a notable exception.
3.  **Use event-based EMA triggering**: Most studies rely on time-based prompts, missing the opportunity to use sensor-detected events to trigger temporally precise EMA prompts (Sigcha et al., 2025).
4.  **Systematically characterise sedentary behaviour context**: Despite the well-recognised limitation that accelerometers cannot distinguish between types of sedentary behaviour, EMA is rarely used to systematically capture what participants are doing while sedentary Aunger & Wagnild (2020), Atkin et al., 2012).
5.  **Address temporal alignment rigorously**: Most studies use crude alignment methods (e.g., day-level aggregation or fixed time windows) rather than sophisticated bout-level or event-level matching (Sigcha et al., 2025).
6.  **Report and model missingness**: EMA compliance is reported inconsistently, and the implications of missing data for analyses are rarely addressed (Brannon et al., 2016; , Maher et al. (2018).
7.  **Distinguish between behavioural domains**: Few studies use EMA to systematically separate occupational, leisure, transport, and household PA or SB, despite the importance of domain-specific analyses Aunger & Wagnild (2020), Edney et al., 2022; .
8.  **Use EMA to resolve accelerometer ambiguity**: The potential of EMA to clarify ambiguous accelerometer classifications (e.g., standing still misclassified as sedentary) is largely unexploited Aunger & Wagnild (2020), Gao et al., 2021).
9.  **Develop semi-supervised or active learning approaches**: The machine learning community has developed methods for learning from sparse labels, but these are rarely applied to EMA-labelled accelerometer data (Sigcha et al., 2025).

### 11.3 What Everyone Should Do

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

2.  **Design EMA protocols with explicit analytic goals**: Before data collection, researchers should specify how EMA data will be used—for labelling, validation, contextual enrichment, or process modelling—and design the protocol accordingly.
3.  **Implement event-based EMA triggering**: Where feasible, use sensor-detected activity transitions to trigger EMA prompts, improving temporal alignment and reducing unnecessary prompting (Sigcha et al., 2025).
4.  **Prioritise activity type, location, and social context**: These are the EMA variables with the highest scientific value and the most direct relevance to accelerometer data interpretation Maher et al. (2018), Edney et al., 2022; , Knell et al., 2017).
5.  **Use EMA to characterise sedentary behaviour context**: Systematically collect information on what participants are doing while sedentary, where, and with whom Aunger & Wagnild (2020).
6.  **Integrate EMA into modelling workflows**: Use EMA labels as training data, validation data, or contextual features in activity classification and behaviour analysis models (Sigcha et al., 2025).
7.  **Report compliance, response latency, and missingness**: Provide detailed information on EMA compliance rates, response times, and patterns of missing data, and address the implications for analyses.
8.  **Develop and validate temporal alignment methods**: Invest in rigorous methods for linking sparse EMA responses to dense accelerometer time series, including bout-level matching and event-level synchronisation (Sigcha et al., 2025).
9.  **Minimise burden while maximising value**: Limit EMA to 4–6 prompts per day, keep surveys brief (1–3 minutes), and focus on variables that directly address the research question (Maher et al., 2023; , Maher et al. (2018).
10.  **Combine thigh-worn and wrist/hip-worn accelerometers**: Use thigh-worn devices (e.g., activPAL) for posture classification and wrist/hip-worn devices (e.g., ActiGraph, Axivity) for intensity classification, with EMA providing the contextual layer that neither device can offer Aunger & Wagnild (2020), (Maher et al., 2023; , Hakun et al., 2025).
11.  **Explore semi-supervised and active learning**: Develop machine learning approaches that can leverage sparse EMA labels alongside dense accelerometer data, and consider active learning strategies where the algorithm requests targeted EMA prompts for uncertain classifications.

___

## Compact Summary Table

# The Role and Utility of Ecological Momentary Assessment (EMA) in Body-Mounted Accelerometer Studies of Physical Activity and Sedentary Behaviour

|             **EMA Use**             |               **What It Adds**                |                     **Limitations**                     |           **Burden**           |                 **Modelling Value**                 |               **Recommendation**                |
|---------------------------------|-------------------------------------------|-----------------------------------------------------|----------------------------|-------------------------------------------------|---------------------------------------------|
|     Activity type labelling     |   Identifies what participant is doing    |       Self-report bias, temporal imprecision        |        Low–Moderate        |              High (if integrated)               |    Prioritise; use event-based triggers     |
|        Location/setting         |     Enables domain-specific analysis      |             Requires GPS or self-report             |            Low             |                  Moderate–High                  |          Include as core variable           |
|         Social context          |       Captures social determinants        |            Subjective, may be sensitive             |            Low             |                    Moderate                     |            Include when relevant            |
|           Affect/mood           |    Links PA/SB to psychological states    | Adds burden, not directly useful for classification |          Moderate          | Low for classification; High for process models | Include only when primary research question |
|        Fatigue/exertion         |    Validates intensity classifications    |     Subjective, difficult to assess momentarily     |          Moderate          |                  Low–Moderate                   |       Include in clinical populations       |
| Domain (work/leisure/transport) | Separates occupational from leisure PA/SB |          Requires careful question design           |            Low             |                      High                       |    Prioritise for public health research    |
|      Compliance/wear-time       | Confirms device wear, identifies non-wear |              Minimal additional burden              |          Very Low          |              High for data quality              |               Always include                |
|       Barriers/motivation       |        Informs intervention design        |               Adds substantial burden               |            High            |             Low for classification              |    Include only in intervention studies     |
|   Event-based activity labels   |     Temporally precise labels for ML      |    Requires real-time processing infrastructure     | Low (automated triggering) |                    Very High                    |          Implement where feasible           |

___

This synthesis reveals that EMA occupies a critical but underexploited niche in body-mounted accelerometer studies of PA and SB. The field has established the feasibility and validity of EMA as a complementary data source, but has not yet fully realised its potential for activity labelling, sedentary behaviour interpretation, and algorithm development. The most promising direction is the integration of event-based EMA with accelerometer data in machine learning pipelines, as demonstrated by Sigcha et al. (Sigcha et al., 2025). Future studies should design EMA protocols with explicit analytic goals, prioritise variables with high modelling value, and invest in rigorous temporal alignment methods.