# Applied tools extension PA1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Read only your extracted task brief. Shared-file integration and commits belong to root.

**Goal:** Extend the existing roadmap with independently assessable applied-tool practice and publish `namepfchekcoutbranch-extended-pa1` for user review.

**Architecture:** Add small teaching units under existing modules/labs. Keep teacher examples, learner implementations, local API smoke and real pretrained evidence distinct. Root integrates metadata, optional groups and routes after scoped implementations.

**Tech Stack:** Python 3.12, NumPy/Pandas/sklearn, pinned CPU PyTorch/Transformers/Datasets, optional Accelerate/PEFT/TRL/Sentence Transformers/MLflow/Optuna; optional GPU bitsandbytes.

**Spec:** `docs/superpowers/specs/2026-10-29-applied-tools-extension-design.md`

## Global Constraints

- Ветка `namepfchekcoutbranch-extended-pa1`; parent исходного изменения — `2c75f94becc999975cc397bbf4013716b46d4568`. Исходные ветки не меняются, merge/PR не выполняются.
- Существующие 180 catalog records и имеющиеся learner boundaries сохраняются; новые ID добавляются, progress не отмечается выполненным.
- Никаких скрытых network/download/training на import или обычном pytest. Pretrained loaders работают только с явным локальным snapshot; скачивание — отдельная документированная команда.
- Author demo, random model smoke, skip и xfail не дают learner credit. Строгий check требует learner implementation и заявленные артефакты; авторство/новый домен проверяются человеком.
- Не запускать полные pytest отдельно каждым агентом, повторные benchmarks, pretrained training, GPU, сервер или загрузку весов. Разрешены короткие scoped CPU/API tests и один интегрированный набор новых/затронутых tests; полный supported-platform прогон — в CI после публикации.
- Root единолично меняет общие catalog/tracks/progress/pyproject/uv.lock/CLI/CI и выполняет git commits. Агенты меняют только назначенные пути; setup зависимостей выполняет root.
- Base runtime остаётся CPU/offline. Optional группы: `trainer`, `sft`, `ranking`, `experiments`, `quantization`; отсутствие группы даёт понятную инструкцию и не засчитывается строгим check.
- Новые файлы имеют одну понятную ответственность; не создаётся общий framework экспериментов и не копируется общий validator между задачами без причины.
- В новой теории есть prerequisites, разбор вычисления/схемы данных, типичные ошибки и критерии переноса. Предпочитать Markdown/Mermaid и небольшие таблицы, не ASCII схемы и не изображения с выдуманными метриками.
- Learner функции остаются с прямым `NotImplementedError`; авторский пример не является готовой универсальной реализацией этих функций.
- Выходные артефакты создаются в новых каталогах, ограничены размером, не попадают в git; ошибка не выдаётся за успешный report. Результаты измерений и pretrained качество не выдумываются.

## Review Focus

- Wrong/future/misaligned rows: temporal features must be computed strictly from information available at each query, and preserve query identity.
- Loss/mask/label alignment: inactive/padding/prompt positions must not silently train or inflate entity/answer metrics.
- Evaluation contamination: split families/query IDs remain disjoint; tuning uses validation, holdout only final evaluation.
- False completion: fixtures/random models/handwritten metrics or untouched starters cannot stand in for the stated live pretrained learner result.
- Missing optional groups and platform limitations: base stays offline; explicit installed-group runs exercise real APIs; CUDA/vLLM absence never becomes a fabricated successful measurement.

---

### Task 1: Core NumPy, Pandas and sklearn practice

**Ownership:** create only `modules/03_data_foundations/exercises/vectorized_features/`, `modules/03_data_foundations/exercises/point_in_time_features/`, `modules/04_machine_learning/exercises/sklearn_selection/`. Root owns parent README/inventory integration.

**Produces:** three IDs `data-vectorized-features`, `data-point-in-time-features`, `ml-sklearn-selection`; README/theory/example/starter, focused teacher and learner tests, offline guards. No optional dependencies.

**Interfaces and decisions:**
- NumPy learner `masked_standardize(values, observed)` returns standardized values plus per-column mean/scale/count; mask is boolean and authoritative, observed values finite, missing positions output zero, constant or empty columns use scale one, empty-column mean zero. Input arrays cannot mutate. Add `topk_cosine(queries, candidates, k)` with zero-vector policy (score zero), deterministic index tie-break and validation. Explain broadcasting, views/copies, axes, temporary memory and batching; bounded teacher uses fixed different arrays.
- Pandas learner `build_point_in_time_features(events, queries, window)` returns query_id order, count/sum/mean of each entity's events in `[as_of-window, as_of)`. Require unique event/query IDs, timezone-aware UTC times, deterministic duplicate-time behavior, positive Timedelta, no future or same-time event. Empty history count/sum zero and mean NaN; unknown entities allowed. Reject mixed timezone-naive input and invalid finite amount. Tests include poisoned future rows, equal timestamps, out-of-order rows, multiple entities, empty history and no input mutation.
- sklearn learner `select_pipeline(frame, labels, groups, *, seed)` builds numeric imputation/scaling + categorical imputation/OneHotEncoder(handle_unknown='ignore') + LogisticRegression; runs bounded group-disjoint CV to choose C from `(0.1, 1.0, 10.0)` using macro-F1, refits training only, returns fitted pipeline and CV table. Holdout not an argument. A separate learner `permutation_report(model, x_holdout, y_holdout, *, seed)` measures heldout permutation importance with declared scoring/repeats. Use fixed train/dev task fixtures, unfamiliar categories/missing values and permuted labels to catch leakage. Explain train-only fit, negative importance and correlated features; no SHAP requirement.

- [ ] Read adjacent existing examples to avoid duplicate scope.
- [ ] Add contract tests and observe meaningful RED for author/helper behavior; preserve intentional learner xfail.
- [ ] Implement bounded examples and Russian theory with at least one worked input/output per unit and transfer questions.
- [ ] Run only new scopes with `.venv/bin/python -m pytest ... -q`; Ruff/mypy own files, no full suite.
- [ ] Self-review and write report with exact signatures, boundaries, headings and test targets; root commits.

### Task 2: HF Trainer workflow and token classification

**Ownership:** create only `labs/02_huggingface_models/trainer_workflow/` and `labs/02_huggingface_models/token_classification/`.

**Produces:** IDs `lab-hf-trainer-workflow` (`trainer` group) and `lab-token-classification` (`trainer` group). Core modules should keep data/metric contracts executable in base where possible; optional real library tests can skip if absent.

**Interfaces and decisions:**
- Trainer learner boundaries cover batched `Dataset.map` tokenization with non-input columns removed, dynamic `DataCollatorWithPadding`, `TrainingArguments`, `compute_metrics`, and training orchestration with best validation checkpoint/resume. Exact run/budget signature may use a local dataclass; document it in starter README and report. Use real tiny local BERT + local tokenizer in author smoke (max four optimizer steps, one CPU thread, no pretrained claim). Invoke actual Trainer/Datasets/collator, save/reload checkpoint and show best metric choice; return raw validation history and model identity. Reject overlapping split IDs or labels/config mismatch. No learner wrapper calling completed author solution.
- Token-classification learner `align_labels(word_ids, word_labels)` labels first subword only and uses `-100` for special/continuation tokens; reject non-monotonic/out-of-range alignment and orphan continuation. `entity_metrics(predictions, references)` evaluates exact BIO entity spans, with explicit invalid-I policy and no cross-sentence joining. A learner runner trains actual AutoModelForTokenClassification on explicit local data/snapshot. Author smoke builds tiny local model and validates real collation/loss and save/reload, not quality. Include subword, punctuation, multiple entities, all-ignored and truncation/word-boundary cases; count unsupported/truncated entities explicitly. Provide annotated neutral text fixture, independent heldout extension and human review.
- Live learner reports retain dataset/model provenance, split IDs, predictions, span metrics and reload identity; pure offline mechanics must not be described as completed pretrained NER.

- [ ] Read existing lab02 boundaries and reuse conventions without altering them.
- [ ] Write meaningful red tests for alignment/metrics/split/config contracts and small actual API expectations.
- [ ] Implement examples, local-only runner seams and learner contracts; add Russian theory with detailed token tables and train/dev curves interpretation.
- [ ] Run only own scopes with root-provided `.venv-training` once optional groups ready; CPU torch thread cap and no model downloads. Scope Ruff/mypy.
- [ ] Report exact catalog metadata and actual tested/unrun states; root commits.

### Task 3: SFT/LoRA learner path and training efficiency

**Ownership:** create `labs/04_llm_finetuning/sft_workflow/`, `labs/01_pytorch_foundations/exercises/training_efficiency/`; may add concise links to `labs/04_llm_finetuning/README.md` and `theory.md` only.

**Produces:** `lab-sft-lora` (`sft` group) and `lab-training-efficiency` (`training` via requires_training). The former requires actual learner implementation and separately submitted live evidence; the latter has mandatory CPU mechanics and opt-in GPU/QLoRA experiments.

**Interfaces and decisions:**
- SFT learner implements conversation validation/splitting, actual `apply_chat_template` use and target-mask construction, SFTTrainer+PEFT configuration/runner, and saved adapter comparison/reload. Supply small neutral author corpus separate from learner data. No assistant answer tokens from heldout training, no shared paraphrase family across splits. Use real local tiny causal-LM + tokenizer/chat template for bounded library smoke (max four steps), mark RANDOM_MECHANISM_ONLY. Check actual base frozen/adapter delta, causal loss masks, finite values, adapter safetensors and fresh-base reload; use local files only.
- Pretrained learner project is executable with explicit local base/tokenizer/data and independently written runner; no fabricated pretrained quality. Compare base/improved-prompt/LoRA on same holdout using parse success, field correctness, unsupported-case handling. Teacher smoke cannot satisfy live gate: origin, snapshot identity, dataset/splits, prediction arithmetic and real artifact files required; human review reruns learner code and checks authorship. Use standard TRL 1.16 / PEFT pinned environment APIs, not guessed snippets from latest docs.
- Efficiency learner `accumulated_step(model, optimizer, batches, loss_fn)` matches a full logical batch's row-weighted gradient/update even with uneven micro-batches. One optimizer step, correct zeroing, no silent batch dropping. Use small deterministic CPU tensors for tests; caller owns train mode/optimizer. Theory distinguishes batch, optimizer steps, effective batch, AMP, activation checkpointing, CUDA timing/memory and optimizer state. Provide explicit GPU runner measuring actual memory/time without pytest autostart; CPU run cannot report CUDA success.
- Add a runnable opt-in QLoRA recipe/entrypoint under sft_workflow using explicit local snapshot, bitsandbytes 4-bit config, prepare_model_for_kbit_training, LoRA and small declared limits. Validate flags and CUDA capability before loading; no automatic install/download. Explain 8 GB limits, no guaranteed model size; QLoRA NOT_RUN until actual evidence. DPO/distillation/continued-pretraining overview as later choices, no mandatory large-model run.

- [ ] Read existing tiny PEFT and SFT contracts to reuse teaching ideas without replacing original learner work.
- [ ] Add red contract tests for masking, split isolation, unequal micro-batches, absent CUDA and evidence provenance.
- [ ] Implement bounded real API author smoke, learner TODOs, detailed theory and explicit manual pretrained/GPU path.
- [ ] Run only own CPU scopes and optional library smoke after root environment setup; no actual pretrained or GPU training.
- [ ] Report exact boundaries/metadata, fixture vs live distinction and tests; root commits.

### Task 4: Neural reranking and embedding adaptation

**Ownership:** create `labs/03_real_rag/neural_reranking/` and `labs/03_real_rag/embedding_adaptation/` only.

**Produces:** `rag-neural-reranking`, `rag-embedding-adaptation` with `ranking` group.

**Interfaces and decisions:**
- Reranker learner `rerank(query, candidates, scorer, k)` invokes actual pair-scoring callable, validates finite score/length, preserves candidate IDs and deterministic ties, never adds unavailable documents. `ranking_metrics(rankings, qrels, k)` returns per-query candidate recall/MRR/nDCG with graded relevance and explicit no-relevant policy. Actual runtime loads `sentence_transformers.CrossEncoder` from an explicit local model directory, no network; author smoke constructs a tiny saved local sequence-classification model and exercises CrossEncoder.predict/rank. Tests use actual library in optional environment and literal score fixtures only for metric contracts.
- Adaptation learner creates query/positive/hard-negative triples and query/family-disjoint splits, uses SentenceTransformer and a documented contrastive training objective. Exclude duplicate positives/false negatives and make sampler/loss assumptions explicit. Provide bounded real local SentenceTransformer/Pooling + training smoke with save/reload, no pretrained claim; explicit live local-snapshot runner and artifact contract for baseline/adapted retrieval on same heldout queries. Test gradients/model change and checkpoint reload, not just mock call counts. No mandatory improvement threshold.
- Russian theory must explain bi-encoder vs cross-encoder, why reranker cannot recover absent candidates, hard-negative risks, in-batch negatives, domain similarity, ranking vs answer evaluation and cost. Include fully worked small ranking metric example and failure cases.

- [ ] Add metric/data-isolation red tests and actual local-library smoke checks.
- [ ] Implement modules/readmes/learner TODOs; preserve existing dense and end-to-end code.
- [ ] Run only own scopes in installed ranking environment, cap threads/steps; Ruff/mypy own files.
- [ ] Report catalog metadata, model provenance boundaries and exact evidence; root commits.

### Task 5: MLflow and bounded model search as learner work

**Ownership:** create `projects/document_intelligence_lab/experiment_management/` only; may add a link to `tracking_intro/README.md`.

**Produces:** `ml-experiment-management` with `experiments` group.

**Interfaces and decisions:**
- Learner performs bounded Optuna search over sklearn pipeline settings on train/dev; holdout withheld from objective. Fixed seed, at most four trials for tiny author smoke. Persist per-trial params/metrics and best trial in MLflow with local SQLite/artifact store; no tracking server/UI/network. Dataset/split digests and objective direction explicit.
- Reuse existing tracking_intro utilities where appropriate, but learner search/objective/log/reload boundaries remain unsolved. Real author demo executes Optuna and MLflow on distinct small fixture, reloads selected sklearn model and reproduces saved predictions. Student report must identify trials and saved model; verify metrics against predictions and selection against validation table. Failed/pruned trials cannot win, holdout tuning forbidden, no mandatory score improvement.
- Separate pure selection/protocol learner tests (base) and optional actual library behavior; strict completion targets require student behavior. Theory covers trial vs run vs artifact, search budget/selection bias, what seed can/cannot ensure, nested CV rationale, leakage, failure/pruning and transfer to HF/SFT runs. Include human rerun/defense.

- [ ] Read existing MLflow implementation and document reuse boundaries.
- [ ] Red tests for wrong selection direction, failed trials and holdout contamination; then implement teacher/runtime helpers and contracts.
- [ ] Run only own tests once optional deps available; keep real smoke four trials on tiny CPU data and no full suite.
- [ ] Report metadata and independent evidence; root commits.

### Task 6: vLLM evidence and shared integration

**Ownership (root):** `labs/05_model_serving/assessment/`, common catalog/tracks/progress/README/docs, dependency metadata/lock, src/roadmap_tools catalog/CLI, common integration tests and CI.

**Produces:** `lab-vllm-measurements`; the ten other new IDs from tasks 1–5; total expected 191 catalog items. Update counts from actual metadata, preserve original record prefix. Add new `applied-nlp` route assembled from existing core and selected LLM/RAG units plus all model-focused additions; augment existing routes at their proper prerequisite positions without making every NLP specialty mandatory for classic ML.

**Interfaces and decisions:**
- Add `CatalogItem.requires_groups: tuple[str, ...] = ()` parsed from optional `requires_groups`. Allow only declared trainer/sft/ranking/experiments/quantization plus existing training/migrations/tracking/retrieval/finetuning. Reject invalid types/duplicates/unknown groups. Import-availability map uses `importlib.util.find_spec` for known top-level modules. Preserve requires_training behavior, union diagnostics for whole tracks and standard strict pytest exit codes.
- Optional dependency groups use versions from spec; `trainer` includes training+accelerate; `sft` includes finetuning+TRL; `ranking` includes trainer+Sentence Transformers; `experiments` includes tracking+Optuna; `quantization` contains bitsandbytes. No optional group enters default runtime. Root updates lock once and installs all needed non-GPU groups into existing `.venv-training`, then freezes agent setup.
- vLLM learner measurement summary computes request count/success/error, empirical latency/TTFT statistics from raw measurements with clear definitions and no invented percentiles. Saved evidence requires actual vLLM provider, model/environment/config identity, request records and restart artifacts; missing NOT_RUN cannot pass strict live credit. Reuse existing smoke/experiment formats, do not launch server or replace documented Linux setup. Human verifies real runtime rather than trusting JSON provider labels.
- New metadata tests enumerate exact IDs/readmes/learner-only scopes and boundaries. Base strict-check probes confirm unimplemented/missing evidence fails without expensive subprocess repetition. Route prerequisites, missing-group diagnostics, backward compatibility and clean progress are tested.
- Document depth map, applied-NLP specialization/portfolio, stages of core vs optional GPU quality, current verification status and future methods. Link existing vLLM/MLflow lifecycle appropriately; don't present documentation as executed training.

- [ ] Write design/plan/ledger and record user-authorized workflow rulings; use existing isolated worktree and exact published parent.
- [ ] Add dependency/parser/CLI regression tests, observe RED, implement and run small tooling selection.
- [ ] Integrate task metadata and vLLM assessment; run scoped navigation/catalog/maintainer/type checks and one combined new-scope library test pass.
- [ ] Obtain scoped root-task review and one final whole-branch review. Fix concrete findings with narrow tests only.
- [ ] Commit, publish exact reviewed tree to requested branch, verify parent/tree and source heads, observe one automatic CI and report links/results/limits.
