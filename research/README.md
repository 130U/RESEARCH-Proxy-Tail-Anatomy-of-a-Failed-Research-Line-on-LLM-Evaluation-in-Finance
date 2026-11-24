# Research Records

One folder per stage or task: protocols, prompts, raw model outputs, analysis code and results. The
stage letters match the [report](../report/Proxy-Tail-Anatomy-of-a-Failed-Research-Line-on-LLM-Evaluation-in-Finance.pdf)
and the route on the [front page](../README.md). Start with the entry point of a stage, then follow
its links to the protocol and the raw records.

## Stage A: Certifiable Financial Language Models

I asked whether a small financial language model could carry proved bounds: on contamination, on
numeric sensitivity, and on the size of the audit needed to trust it. Nine rounds of theory,
implementation and testing, organised as five research paths, showed that each component was a
standard tool and that the strongest simple baselines matched the elaborate designs.

**Entry points:** [theory/notes.md](theory/notes.md) (the proof notes),
[planning/record.md](planning/record.md) (audit-design computations),
[experiments/real_baseline/report.md](experiments/real_baseline/report.md) (the SEntFiN baseline).

| Folder | Contents |
|---|---|
| [theory/](theory/) | Proof notes: certificate basics, collective metrics, impact audits, localisation value, randomised audits, point-in-time non-interference, semantic envelopes |
| [planning/](planning/) | Audit-design computations: threshold, localisation and randomisation tables, with their protocols |
| [real_baseline/](real_baseline/), [experiments/](experiments/) | The SEntFiN entity-sentiment baseline (protocol, preparation, training, bootstrap) and experiment outputs |
| [literature/](literature/) | The literature ledger of the stage |
| [local/](local/), [certificates/](certificates/), [checks/](checks/), [evaluation/](evaluation/) | Synthetic foundation experiments, the collective-metric checker, theory checks, reconstruction of the older model's metrics |
| [numeric/](numeric/), [pit/](pit/), [xbrl/](xbrl/), [data/](data/) | Numeric-envelope checks, point-in-time pipeline checks, a restricted local XBRL parser, the FOMC source audit and compute budget |
| [REPRODUCE.md](REPRODUCE.md), [reproduce.py](reproduce.py) | The offline reproduction runner for the stage |

The stage started from my earlier financial language-model project,
[130U/RESEARCH-Financial-Large-Language-Model](https://github.com/130U/RESEARCH-Financial-Large-Language-Model).
It ran offline after the first round, so no SEC data were downloaded. All scripts run offline and
download nothing.

## Stage B: Proxy Tail, Tail Screening with a Cheap Model

How wide must a cheap model's shortlist be to keep a fixed share of a reference model's top items?
The law turned out to be known, and the reference model did not agree with itself in the tail.

**Entry points:** [tail_screening/SUMMARY.md](tail_screening/SUMMARY.md) (final assessment),
[tail_screening/one_page.md](tail_screening/one_page.md) (theory and lexical baseline).

| Folder | Contents |
|---|---|
| [tail_screening/](tail_screening/) | Theory and counterexamples, literature check, lexical baselines, the pilot, stage 1 (32 items) and stage 2 (128 items) protocols, reports, figures and analysis code |
| [private/agent_tail_pilot/](private/agent_tail_pilot/), [private/agent_tail_methods/](private/agent_tail_methods/) | Raw inputs and outputs of every ranking and pairwise run |
| [private/real_baseline/](private/real_baseline/) | SEntFiN entity rows, fixed splits, saved lexical models and per-row predictions (shared with Stages A and C) |

The two models measured in this stage are labelled "Luna" and "Sol" in the records.

## Stage C: Absolute-Score Stability

Does one model agree with itself on its own top 10%? 1,000 headlines scored in 8 rounds, 10,000
scores. Formally inconclusive: the pre-registered tie gate was breached.

**Entry point:** [absolute_scoring/ONE_PAGE.md](absolute_scoring/ONE_PAGE.md); the frozen protocol is
[absolute_scoring/protocol.md](absolute_scoring/protocol.md).

## Stage D: Two Behavioural Probes

| Folder | Question | Outcome | Entry point |
|---|---|---|---|
| [t2_magnitude/](t2_magnitude/) | T2: does sentiment respond smoothly to the size of a number? | Stopped at the prior-art check; no scoring run | [DECISION.md](t2_magnitude/DECISION.md) |
| [t3_combination/](t3_combination/) | T3: how does a model combine a good and a bad fact? | 3,360 scores; close to additive; no mechanism to pursue | [README.md](t3_combination/README.md) |

## Stage E: Rounding Precision in FinQA

Filings print rounded numbers; benchmarks treat them as exact. How many answers does the displayed
precision fail to determine? The effect is real, and it changes no official score.

| Folder | Question | Outcome | Entry point |
|---|---|---|---|
| [t1_rounding/](t1_rounding/) | T1: count the questions | 196 / 1,147 test questions (17.1%) | [ONE_PAGE.md](t1_rounding/ONE_PAGE.md) |
| [t1a_law/](t1a_law/) | T1a: a predictive rule | Zero-parameter rule matches the exact classification on 5,337 questions | [ONE_PAGE.md](t1a_law/ONE_PAGE.md) |
| [t1b_tighten/](t1b_tighten/) | T1b: try to falsify the finding | Survives; 139 questions after review | [ONE_PAGE.md](t1b_tighten/ONE_PAGE.md) |
| [t1c_models/](t1c_models/) | T1c: effect on model scoring | None found | [ONE_PAGE.md](t1c_models/ONE_PAGE.md) |
| [t1d_precision/](t1d_precision/) | T1d: do models know their precision? | Yes, when reminded; a second review leaves 123 questions | [ONE_PAGE.md](t1d_precision/ONE_PAGE.md) |
| [t1f_novelty/](t1f_novelty/) | T1f: novelty check of five candidate claims | Four of five had prior work | [README.md](t1f_novelty/README.md) |
| [t1g_consequence/](t1g_consequence/) | T1g: where does precision have consequences? | Almost nowhere; the rule holds on TAT-QA | [ONE_PAGE.md](t1g_consequence/ONE_PAGE.md) |

T1e, an extension to the full test set, was planned and not run; its second-dataset part moved into T1g.

## Conventions in These Records

- "Pass", "fail", "continue", "stop" and "inconclusive" refer to gates written down before the data
  were seen. Gates were never moved after the fact.
- Semantic reviews and adjudications were model-based; no human annotation was collected.
- The working records were written in Chinese and appear here in English, with numbers, code,
  prompts, raw model outputs and link targets unchanged. Some files record SHA-256 hashes of other
  files; those hashes were computed on the working-language files.
- Every ranking, score and answer comes from a model session opened by the pipeline's session
  runner: one new session per call, starting from an empty context (`fork_turns=none` in the call
  records), with the model and the reasoning effort fixed in the record. The records call a scoring
  session an agent and its working directory an agent path. The sessions were not run through a
  metered API, which is why the protocols say "no paid API".
- Each stage opened with a written task statement: the question, the prompts and the decision
  thresholds, fixed before any data were read. The records cite it as the task, the task file or
  `TASK.md`. Its thresholds are restated in the stage's protocol, and its prompts are saved beside
  the stage's inputs.
- Each stage ran in its own working copy on its own branch (`proxy-tail`, `proxy-tail-t1a` and so
  on; `task/t1`, `task/t1a` and so on). Branch names and commit ids in the records identify the
  state of that working copy when the record was written. This repository gathers the final files
  of every working copy in one tree, one folder per stage.
- Search logs list each query as it was run. "GitHub connector" is GitHub's search over issues
  and code.
