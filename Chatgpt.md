## 1. Executive summary

In the narrow literature you asked for, EMA is **not mainly used as a replacement for body-mounted accelerometers**, and it is **rarely used as dense ground truth for activity-recognition models**. Its main role is to add what the accelerometer cannot reliably tell on its own: **what the person says they are doing, whether they are sitting, where they are, with whom, how they feel, what they intend, and how they interpret the moment**. The strongest evidence supports EMA as a **near-time contextual and interpretive layer**, and as a **coarse validation source** for broad states such as “physical activity/exercise” versus “sitting/sedentary behaviour,” not as a precise second-by-second label stream. ([Frontiers][1])

The best-supported uses are:
(1) **criterion/convergent validation** of EMA-reported activity or sitting against concurrent accelerometer output;
(2) **contextualisation** of physical activity and sedentary behaviour by location, company, and setting;
(3) **behaviour interpretation**, especially for sedentary time, affect, intentions, and pain/stress; and
(4) **short-horizon prediction of subsequent behaviour** using momentary psychological states such as intentions and self-efficacy. ([Frontiers][1])

The weak point is the algorithm side. In the strict body-mounted accelerometer PA/SB literature, EMA is **usually collected for behavioural science questions**, not for training free-living HAR models. It is commonly analysed with multilevel or within-person models, but only rarely turned into a serious weak-labelling framework for continuous classification. The modelling opportunity is real, but the established peer-reviewed literature is still thin. ([Frontiers][1])

The field’s recurring problems are also clear: **sparse EMA against dense time series, vague temporal linkage, incomplete reporting of latency and missingness, little item-level content validation, and frequent collection of EMA that is never meaningfully integrated into modelling**. Broader methodological reviews of PA/SB EMA found that none of the reviewed studies explicitly reported assessing EMA item content validity, most gave little rationale for prompt design, only one reported response latency, and no study reported backfilling. ([Springer][2])

My bottom-line synthesis is this: in this field, **EMA is most valuable when it is used sparingly and deliberately to resolve specific ambiguities that body-mounted accelerometers cannot resolve**—especially **domain, purpose, social/physical context, and subjective meaning**. It is least valuable when it is treated as a vague “extra questionnaire layer” with too many items and no clear analytic role. ([ResearchGate][3])

---

## 2. Scope definition and inclusion logic

I kept the synthesis focused on studies that pair **dedicated body-mounted accelerometer devices** with **momentary or near-momentary self-report during the same monitoring period**. In practice, the core studies I leaned on used devices such as **ActiGraph** and **activPAL**, with EMA delivered through phones or electronic diaries. The inclusion logic was: wearable accelerometer provides the primary movement record; EMA provides in-the-moment or near-in-time self-report; the behavioural target is physical activity, sedentary behaviour, posture/movement behaviour, or free-living behaviour analysis. ([Frontiers][1])

I excluded or de-emphasised work where the primary sensing came from a **smartphone accelerometer**, smartwatch-only consumer sensing, purely physiological ambulatory monitoring, generic digital phenotyping, and lab-only HAR. I also treated some newer or adjacent work as **contextual but not core** when the trigger logic came mainly from phone sensors rather than the dedicated wearable sensor. That matters because your question is about the utility of EMA **within wearable-accelerometer PA/SB research**, not EMA in mobile health generally. ([Springer][2])

One important reality: the literature is **not huge** once your exclusions are enforced. There is a solid body of behavioural/contextual and validation studies, but the subset that directly uses EMA for **accelerometer-based algorithm development** is still sparse. So some sections below are built on a stronger evidence base than others, and I mark that clearly. ([Springer][2])

---

## 3. What EMA contributes beyond body-mounted accelerometers

Body-mounted accelerometers are excellent for **continuous timing, movement intensity, and—depending on device placement and algorithm—posture or upright/sitting time**. But they usually cannot tell **why** the movement happened, whether a low-movement bout was **working, commuting, reading, socialising, or watching TV**, or what the participant’s **affect, intention, self-efficacy, pain, or social context** was at that moment. Dunton’s adult validation paper explicitly framed EMA as a way to assess current physical activity and sedentary behaviour in real time, while older-adult work using activPAL used EMA to capture current activity, sitting, and related contextual meaning rather than total volume alone. ([Frontiers][1])

In this field, EMA differs from **passive sensing** because it contributes **self-interpreted context and subjective state**, not just more sensor channels. It differs from **retrospective questionnaires** because it samples the moment or the very recent past rather than asking people to summarise days or weeks from memory. It differs from **time-use diaries** because it is usually briefer, repeated, and closer to the target moment, though much sparser than a full diary. It differs from **direct observation or video annotation** because it is far less precise as a behavioural label, but far more scalable and practical in free-living research. ([PMC][4])

So, field-specifically, EMA is best understood as three things at once. First, a **near-ground-truth source for coarse current-state labels**, such as “physical activity/exercise” or “I was sitting,” when aligned to a narrow time window. Second, a **contextual metadata layer** that adds place, company, and sometimes domain. Third, a **behavioural interpretation layer** that captures states like affect, intention, self-efficacy, pain, or stress. What it is **not**, in this literature, is a robust substitute for dense, objectively labelled ground truth for fine-grained HAR. ([Frontiers][1])

---

## 4. How EMA is used in physical activity and sedentary behaviour studies

### 4.1 Validation of momentary activity and sitting reports

This is one of the clearest uses. In adults, Dunton et al. tested whether EMA-reported current activity categories aligned with accelerometer-derived movement in the ±15 minutes around the prompt. They found that EMA-reported physical activity corresponded to higher concurrent MVPA, and EMA-reported sedentary behaviours corresponded to higher concurrent sedentary activity. ([Frontiers][1])

The same pattern appears in older adults. In Maher et al., older adults completed six random EMA prompts per day for 10 days while wearing an activPAL. When participants reported “physical activity/exercising,” concurrent device-measured activity was higher; when they reported sitting activities, concurrent sedentary behaviour was higher. That is strong evidence that EMA can serve as a useful **coarse criterion-validity signal** in free-living PA/SB studies. ([PMC][5])

More recent worker data point in the same direction. Monnaatsie et al. reported that when participants said they were physically active, ActiGraph counts and steps were higher, and when they reported sitting, counts and steps were lower, again supporting criterion validity rather than precise behavioural labelling. ([PubMed][6])

### 4.2 Contextualising where and with whom behaviour happens

Another major use is context mapping. Liao et al. used EMA with accelerometry to understand **where** and **with whom** adults’ physical and sedentary activity occurred. The study showed that home was a dominant context, activities often occurred alone, and the physical setting mattered for MVPA patterns. That is exactly the kind of information accelerometers alone do not provide. ([ResearchGate][3])

This context role appears repeatedly in related youth and older-adult work as well. Kracht et al. linked prior sedentary time with EMA-assessed contextual factors such as being indoors or alone. Hancock et al. showed that the same broad activity category can carry different experiential meaning depending on context: for example, some sedentary activities were linked to lower purpose, while social and outdoor activities related differently to happiness and purpose. ([sedentarybehaviour.org][7])

### 4.3 Interpreting sedentary behaviour, not just counting it

EMA is especially useful for sedentary behaviour because “sedentary time” is behaviourally heterogeneous. Device-based sitting can reflect work, meetings, transport, TV, reading, computer use, meals, or socialising. Maher’s older-adult validity study already showed differences across domain-specific sitting activities, with more sedentary time when watching TV/movies than in some other sitting contexts. Hevel et al. further showed that the affective meaning of sedentary behaviour depended on social and physical context. ([PMC][5])

This is where EMA adds real scientific value: not by proving that someone was sedentary, but by helping explain **what kind of sedentary behaviour it was** and **what it meant**. The literature supports this strongly for broad distinctions like socially versus nonsocially situated sedentary behaviour, or leisure versus occupational context. But the literature is still thinner than it should be for the most policy-relevant distinctions, especially **occupational sitting versus leisure sitting**. Gallagher’s worker study is notable precisely because it showed those domains do not relate similarly to mood, pain, or health indicators. ([PubMed][8])

### 4.4 Capturing momentary psychology that predicts later behaviour

A different but important use is to treat EMA as a measure of **antecedents of behaviour**. Maher’s dual-process study in older adults used EMA-measured intentions and self-efficacy to predict sedentary behaviour in the subsequent two hours measured by activPAL. That is not ground truth at all; it is a **prospective explanatory layer**. ([PubMed][9])

A related line of work uses EMA to study affect, stress, pain, or subjective states as temporally proximal predictors or consequences of physical activity and sedentary behaviour. The evidence here is meaningful but less uniform: broader reviews of EMA-plus-accelerometer studies report fairly consistent links between physical activity and increased arousal, but more mixed evidence for valence and negative affect, and inconclusive results for stress in many studies. ([ScienceDirect][10])

---

## 5. Role of EMA in labelling, validation, and algorithm development

### Established

EMA is clearly used as a **validation source**. That is the most mature role. Dunton, Maher, Zink, and Monnaatsie all, in different ways, compare EMA-reported activity/sedentary states with concurrent accelerometer-derived behaviour and show that the broad reports are informative. ([Frontiers][1])

EMA is also clearly used as a **context feature source** and **error-interpretation aid**. Studies use it to explain where activity occurred, with whom, and under what affective or motivational conditions. This is valuable for behaviour analysis and intervention design, even if it is not directly fed into a classifier. ([ResearchGate][3])

### Common practice

What most eligible studies actually do is **not** train activity classifiers from EMA labels. They use EMA to answer questions like:

* When people say they are active, does the accelerometer agree?
* What contexts accompany higher or lower sedentary time?
* Do intentions, affect, or self-efficacy predict movement in the next hour or two?
  That is behavioural and methodological work, not classic supervised HAR. ([Frontiers][1])

### Weak or inconsistent evidence

I found **very little established peer-reviewed evidence** in this strict literature showing EMA being used as a serious **direct training-label source for continuous raw-signal activity classification**. The broader PA/SB EMA reviews focus on sampling, validity, compliance, and correlates, not on classifier training pipelines. Emerging work is starting to push EMA toward free-living weak labelling, but the clearest example I found for that was still a 2025 preprint rather than established peer-reviewed evidence, so it should not be treated as consensus. ([Springer][2])

### My synthesis

For this field, EMA is genuinely useful for modelling when the task is one of these:

* **weak labelling of coarse domains** such as exercise versus sitting, or maybe TV/computer sitting versus non-screen sitting;
* **context-aware modelling** where social or physical setting matters;
* **personalisation** or **short-horizon prediction** of later activity based on intentions, affect, or barriers;
* **error analysis**, such as understanding why the same accelerometer signature means different things in different contexts. ([PubMed][11])

It is only marginally useful when the task is **fine-grained continuous HAR from raw signals**, because EMA is sparse, delayed, subjective, and often refers to a broad “main activity” rather than a cleanly bounded event. For those tasks, EMA should be treated as **weak supervision or stratification metadata**, not as gold-standard labels. ([Frontiers][1])

---

## 6. Common EMA variables collected in this literature

The most common variables are the simplest ones: **current activity**, **what was happening right before the prompt**, and **whether the person was sitting**. Maher’s older-adult activPAL study is a good example: participants were asked what they were doing right before the phone went off, and a branching question asked whether they were sitting if the activity was not exercise. Dunton’s adult work used similar broad current-activity categories. ([PMC][5])

Also common are **location/physical context** and **social context**. Liao’s adult study focused on where and with whom physical and sedentary activity occurred. Kracht’s adolescent sedentary-time study used indoor/outdoor and alone/not-alone context. These variables are common because they answer a major limitation of accelerometers at relatively low burden. ([ResearchGate][3])

A third common cluster is **affect and subjective experience**. Hancock examined happiness and purpose linked to activity and context. Hevel examined affect during sedentary behaviour. Broader scoping work also suggests affect is one of the most common non-behavioural constructs collected in eEMA movement studies. ([PubMed][12])

A fourth cluster is **motivation and behavioural cognitions** such as intentions and self-efficacy. This is not universal, but it is clearly present in older-adult EMA-plus-accelerometer work and is analytically useful when the question is behavioural initiation or interruption rather than classification. ([PubMed][9])

Less consistently collected, and in my reading genuinely less established in this narrow literature, are **purpose/domain variables** in a strong, harmonised way. The field talks about the importance of distinguishing occupational, leisure, transport, and household contexts, and studies like Gallagher show why those distinctions matter, but many EMA protocols still collect only broad current activity and a few context items rather than a rigorous domain ontology. ([PubMed][8])

Relatively rare in the strict literature are **fatigue, pain, symptoms, barriers, and compliance/wear-time issues** as core EMA targets, though they do appear in certain sublines of work. Their scientific value can be high when they are theory-driven, but for general accelerometer-based PA/SB studies they often add burden faster than they add labelling value. Broader reviews also warn that EMA item validity is often poorly justified, which makes long, ambitious item batteries risky. ([PubMed][8])

---

## 7. Methodological challenges in linking EMA to accelerometer data

The hardest problem is that EMA is **sparse and human-timed**, while accelerometer data are **dense and continuous**. A single EMA response may refer to “right now,” “right before the prompt,” or a loosely remembered recent period, whereas the wearable records every second or every epoch. That creates mismatch in **timestamp alignment, recall window, event duration, and behavioural granularity**. ([Springer][2])

The most common strategy in the validation literature is to align the EMA response with a **short symmetric window around the prompt**, especially **±15 minutes**. Dunton used the ±15-minute window in adults; Maher used 15-minute windows in older adults; and broader sedentary-behaviour EMA methodology reviews report that the 15-minute comparison window is common. ([Frontiers][1])

Other studies use **preceding** or **following** windows depending on the question. Kracht examined sedentary time in the **30-minute bout prior** to the survey. Maher’s dual-process work linked EMA-measured intentions and self-efficacy to sedentary behaviour in the **two hours after** the prompt. That is methodologically sensible, but it shows that EMA-to-sensor linkage is not one thing; it depends on whether the target is validation, antecedents, or consequences. ([sedentarybehaviour.org][7])

A second challenge is **prompt-response lag**. If the participant answers late, the nominal prompt time and the effective report time diverge. Broader methodological reviews are blunt here: only one reviewed PA/SB EMA study reported latency, and none reported backfilling. That is a major weakness, because late answering can seriously degrade the meaning of “current activity.” ([Springer][2])

A third challenge is **missing EMA responses**. Dunton found that response likelihood could vary with activity level in some groups. Maher found missingness patterns related to sex, weight status, and time of day in older adults. This means missing EMA is not obviously random, and treating it casually can bias context estimates. ([Frontiers][1])

The strongest alignment approaches in this literature are the ones that do four things:

1. define an explicit recall frame such as “right before the phone went off”;
2. pre-specify the sensor linkage window;
3. limit prompt expiry and reminders so answers stay close to the moment;
4. analyse within-person associations with models that respect repeated measures.
   The literature supports these principles, even if many studies do not report them well enough. ([PMC][5])

---

## 8. Common weaknesses and blind spots

The biggest blind spot is simple: **EMA is often collected, but not used to its full potential**. Many studies use it to show that context or affect correlates with activity or sedentary time, but they do not turn it into a structured annotation layer that could improve free-living classification, domain separation, or ambiguity resolution. ([Springer][2])

A second major weakness is **poor reporting and weak methodological justification**. Broader PA/SB EMA reviews found no explicit item content-validity assessment, frequent failure to report the actual items used, limited participant training, and little rationale for prompt frequency or timing. That matters because EMA quality depends heavily on wording, burden, and timing. ([Springer][2])

A third weakness is **underuse of EMA for the most important behavioural ambiguities**. The field often measures affect, stress, or broad context, but much less consistently captures the specific distinctions that would most help interpret accelerometer data: **occupational versus leisure sitting, intentional exercise versus transport versus household movement, or the purpose of a sedentary bout**. Gallagher’s findings show those distinctions matter, but the field does not operationalise them consistently enough. ([PubMed][8])

A fourth weakness is the limited maturity of **event-triggered EMA**. The methodological review found that time-based sampling dominates, and among event-based studies, only half were device-initiated. Recent work such as WEALTH and Delobelle’s sensor-triggered study suggests the area is advancing, but it is still not mainstream in this literature. ([Springer][2])

A fifth weakness is that **sedentary behaviour interpretation still lags behind its epidemiological importance**. The literature clearly shows that not all sitting is equivalent, yet many studies still operationalise sedentary behaviour mostly as duration, with EMA used more often to link sitting with mood than to build sharper behavioural taxonomies of sitting contexts. ([PubMed][13])

---

## 9. Best-practice recommendations for future studies

If the goal is a strong EMA component in a wearable-accelerometer PA/SB study, the EMA should be **brief, specific, and designed around a concrete analytic job**. The best default set is: **current main activity**, **sitting yes/no or posture relevance**, **location category**, **social context**, and—if theoretically central—**one or two subjective items** such as affect, intention, or pain. The broader review evidence strongly supports keeping assessments short and carefully justified. ([PMC][5])

For **physical activity classification**, EMA should not be treated as gold-standard labels for dense windows. It should be used as **weak supervision** or **coarse validation**. Prioritise items that resolve ambiguity the sensor cannot: **exercise vs transport vs household vs occupational movement**, **purpose/domain**, and **context**. If fine-grained classification is the goal, EMA should ideally be paired with a stronger label source on a subsample, not used alone. ([Frontiers][1])

For **sedentary behaviour interpretation**, prioritise **what kind of sitting it is**: work, TV/screen, transport, meals, socialising, meetings, reading, rest. That is where EMA adds the most scientific value. Asking only “were you sedentary?” is often too redundant, especially with a thigh-worn device that already captures posture well. ([PMC][5])

For **context-aware behaviour analysis**, the high-value low-burden items are **where**, **with whom**, and sometimes **indoors/outdoors**. Liao and related work show that these items are both feasible and useful. ([ResearchGate][3])

For **multimodal algorithm development**, the ideal design is probably a hybrid one: a body-mounted accelerometer gives the continuous stream, EMA gives sparse contextual annotations, and a smaller subset gets stronger labels or event verification. That is not yet common practice, but it is the most plausible way to extract modelling value without pretending EMA is something it is not. Emerging work is moving in this direction, but the evidence base is not yet mature. ([ResearchGate][14])

On burden, the best balance is usually **4–6 prompts/day** for general context sampling, or a carefully justified semi-random design within windows. That sits well with both representative studies and broader reviews showing that most PA/SB EMA studies use between 2 and 10 prompts/day, with semi-random prompting common. Event-triggered EMA is promising for rare or high-value states, but it needs better technical and reporting discipline. ([PMC][5])

---

## 10. Representative studies / datasets

### Dunton et al., 2012 — adults, accelerometer + 8 random EMA prompts/day

Why it matters: one of the clearest demonstrations that EMA-reported broad activity categories map sensibly onto concurrent accelerometer behaviour in free-living adults.
What EMA did: current main activity.
Scientific consequence: supports EMA as a valid **coarse momentary activity report**, not a total-volume replacement.
Limitation: coarse categories and ±15-minute linkage, so not fine-grained labels. ([Frontiers][1])

### Liao et al., 2015 — adults, accelerometer + EMA on where/with whom

Why it matters: strong example of EMA’s contextual role.
What EMA did: captured where behaviour occurred, with whom, and perceived environmental context.
Scientific consequence: showed that PA/SB patterns vary meaningfully by setting and company—information accelerometers alone cannot provide.
Limitation: more useful for interpretation than for classifier training. ([ResearchGate][3])

### Maher et al., 2018 — older adults, activPAL + 6 random EMA prompts/day for 10 days

Why it matters: one of the best older-adult feasibility and criterion-validity studies.
What EMA did: current activity right before prompt, sitting question, branched activity reporting.
Scientific consequence: strong support for EMA as a feasible and valid signal in older adults; also highlights reactivity and missingness issues.
Limitation: still a sparse, coarse report structure. ([PMC][5])

### Maher et al., 2020 — older adults, activPAL + intentions/self-efficacy EMA

Why it matters: shows EMA’s value as a **prospective behavioural predictor** rather than a label.
What EMA did: intentions and self-efficacy regarding limiting sedentary behaviour.
Scientific consequence: EMA can explain short-term changes in subsequent sedentary time.
Limitation: useful for behavioural theory and adaptive interventions, less directly for activity classification. ([PubMed][9])

### Hevel et al., 2021 — older adults, activPAL + affect/context EMA

Why it matters: shows that identical sedentary exposure can mean different things depending on context.
What EMA did: affect and social/physical context during sedentary behaviour.
Scientific consequence: sedentary behaviour interpretation improves when EMA is added.
Limitation: interpretive value is high, direct labelling value is limited. ([PubMed][13])

### Hancock et al., 2021 — older adults, waist ActiGraph + activity/context/meaning EMA

Why it matters: good example of EMA being used to understand the experiential meaning of activity and sedentary contexts.
What EMA did: current activities, contexts, happiness, and sense of purpose.
Scientific consequence: showed that activity meaning depends on context, not just movement magnitude.
Limitation: again, behaviour interpretation is stronger than direct modelling use. ([PubMed][12])

### Kracht et al., 2021 — adolescents, hip accelerometer + repeated EMA

Why it matters: shows how EMA can help interpret sedentary behaviour in youth.
What EMA did: context such as indoors/outdoors and alone/not alone.
Scientific consequence: links sedentary bouts to context, which accelerometer data alone cannot resolve.
Limitation: still sparse relative to dense time series. ([sedentarybehaviour.org][7])

### Monnaatsie et al., 2024 — shift and non-shift workers, ActiGraph + EMA

Why it matters: recent validation evidence in a worker population.
What EMA did: momentary reports of PA and sedentary behaviour.
Scientific consequence: further supports EMA as a convergent-validity tool.
Limitation: reinforces the same conclusion as earlier studies more than it expands modelling use. ([PubMed][6])

### Emerging but not yet mature for consensus

Recent work in WEALTH and sensor-triggered EMA studies is important because it starts pushing EMA toward **event-based sampling** and possible **free-living weak labelling**, but this is still methodologically emergent rather than settled field practice. ([PLOS][15])

---

## 11. Final synthesis: what everyone does, what they do not do, and what they should do

### What everyone does

In this narrow literature, researchers mostly use EMA to **sample current activity or sitting plus context**, then link that self-report to the accelerometer to ask whether the behavioural state makes sense and what contextual or psychological factors surround it. Random or semi-random prompting over several days is common, app-based delivery is common, and the core analytic frame is usually **within-person behavioural science**, not supervised HAR. ([Frontiers][1])

### What they do not do

They usually do **not** use EMA as a strong, structured annotation layer for free-living algorithm development. They also often do **not** report enough about latency, missingness, item validity, or prompt rationale. And they still underuse EMA for the distinctions that matter most for interpreting sensor data: **domain, purpose, and the meaning of sedentary time**. ([Springer][2])

### What they should do

They should use EMA much more strategically:

* to capture **only** the information the accelerometer cannot provide;
* to define explicit **sensor-linkage windows** and report latency/missingness rigorously;
* to prioritise **domain, purpose, location, and social context** over generic extra questions;
* to treat EMA as **weak labels and contextual metadata**, not gold-standard dense ground truth;
* and, when modelling is the goal, to combine EMA with a stronger label source on at least a subset rather than assuming sparse self-report can carry the whole labelling burden. ([Springer][2])

The sharpest field-specific answer to your main question is this:

**EMA’s real utility in body-mounted accelerometer studies of physical activity and sedentary behaviour is not that it measures movement better than the accelerometer. It does not. Its utility is that it explains the movement record: what the behaviour was, what kind of sitting or activity it was, where and with whom it occurred, and what the person was experiencing or intending at the time.** That makes it highly valuable for **contextualisation, interpretation, and selective weak supervision**, but only moderately valuable for dense activity classification unless the study is designed around that use from the start. ([Frontiers][1])

I can turn this into a **formal deep-research prompt**, a **literature matrix**, or a **review-style background section** next.

[1]: https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2012.00260/full "Frontiers | Momentary Assessment of Adults’ Physical Activity and Sedentary Behavior: Feasibility and Validity"
[2]: https://link.springer.com/article/10.1186/s12966-020-00932-9 "Content validity and methodological considerations in ecological momentary assessment studies on physical activity and sedentary behaviour: a systematic review | International Journal of Behavioral Nutrition and Physical Activity | Springer Nature Link"
[3]: https://www.researchgate.net/publication/260876235_Using_Ecological_Momentary_Assessment_to_Understand_Where_and_With_Whom_Adults%27_Physical_and_Sedentary_Activity_Occur "https://www.researchgate.net/publication/260876235_Using_Ecological_Momentary_Assessment_to_Understand_Where_and_With_Whom_Adults%27_Physical_and_Sedentary_Activity_Occur"
[4]: https://pmc.ncbi.nlm.nih.gov/articles/PMC5161656/?utm_source=chatgpt.com "Ecological Momentary Assessment in Physical Activity Research"
[5]: https://pmc.ncbi.nlm.nih.gov/articles/PMC6104625/ "
            Ecological Momentary Assessment Is a Feasible and Valid Methodological Tool to Measure Older Adults’ Physical Activity and Sedentary Behavior - PMC
        "
[6]: https://pubmed.ncbi.nlm.nih.gov/38899730/?utm_source=chatgpt.com "Ecological momentary assessment of physical activity and ..."
[7]: https://www.sedentarybehaviour.org/2021/04/21/adolescents-sedentary-time-affect-and-contextual-factors-an-ecological-momentary-assessment-study/ "https://www.sedentarybehaviour.org/2021/04/21/adolescents-sedentary-time-affect-and-contextual-factors-an-ecological-momentary-assessment-study/"
[8]: https://pubmed.ncbi.nlm.nih.gov/34456325/?utm_source=chatgpt.com "Leisure but Not Occupational Physical Activity and ..."
[9]: https://pubmed.ncbi.nlm.nih.gov/31550923/ "https://pubmed.ncbi.nlm.nih.gov/31550923/"
[10]: https://www.sciencedirect.com/science/article/pii/S1755296625000596 "https://www.sciencedirect.com/science/article/pii/S1755296625000596"
[11]: https://pubmed.ncbi.nlm.nih.gov/31550923/?utm_source=chatgpt.com "Dual-process model of older adults' sedentary behavior: an ..."
[12]: https://pubmed.ncbi.nlm.nih.gov/33395629/ "https://pubmed.ncbi.nlm.nih.gov/33395629/"
[13]: https://pubmed.ncbi.nlm.nih.gov/33656523/ "https://pubmed.ncbi.nlm.nih.gov/33656523/"
[14]: https://www.researchgate.net/publication/394339832_Data_Labelling_for_Free-Living_Physical_Activity_Recognition_using_Thigh-Worn_Wearables_and_Event-based_Ecological_Momentary_Assessment "https://www.researchgate.net/publication/394339832_Data_Labelling_for_Free-Living_Physical_Activity_Recognition_using_Thigh-Worn_Wearables_and_Event-based_Ecological_Momentary_Assessment"
[15]: https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0318772 "https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0318772"
