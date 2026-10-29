# Самостоятельный SFT и LoRA

**lab-sft-lora · ML-DEPTH.** Это learner path поверх настоящих TRL/PEFT APIs.
Prerequisites: causal next-token loss, PyTorch gradients, HF tokenizer/model lifecycle,
[предыдущий masking contract](../sft_contract.py), train/validation/holdout,
JSON evaluation и смысл LoRA rank. Прочитайте [теорию](theory.md).

## Что реализует ученик

В `starter.py` оставлены пять прямых `NotImplementedError`:

| Граница | Проверяемый результат |
| --- | --- |
| `validate_conversations` | уникальные ID, family, user/assistant messages, JSON object answer, expected и supported |
| `split_conversations` | полное разбиение по family на train/validation/holdout |
| `encode_conversation` | реальный `apply_chat_template`, assistant mask, unshifted labels и padding |
| `build_trainer` | настоящий `SFTTrainer` и PEFT; замороженная base; supplied labels не заменены |
| `compare_and_reload` | adapter safetensors; fresh local base; одинаковые конечные eval logits |

Шестая граница — `learner_run.run_project`: самостоятельно напишите runner для
своего нового домена. Входные base/tokenizer/data задаются явно. Скрипт проверяет
пути и бюджет, затем вызывает ваш код. Никакого автоматического скачивания.
По умолчанию 4 шага — проверка запуска; разрешён явный бюджет 1..100. Выберите
собственную задачу/данные и обоснуйте, достаточен ли ваш бюджет для выводов.

Данные learner имеют форму JSON list:

```json
[
  {"id":"new-domain-01","family":"refund-policy-a","supported":true,
   "expected":{"route":"refund"},
   "messages":[{"role":"user","content":"Return a route for a refund request"},
               {"role":"assistant","content":"{\"route\":\"refund\"}"}]},
  {"id":"new-domain-02","family":"unsupported-weather","supported":false,
   "expected":{"unsupported":true},
   "messages":[{"role":"user","content":"Predict tomorrow's weather"},
               {"role":"assistant","content":"{\"unsupported\":true}"}]}]
```

Это иллюстрация schema, не готовый достаточный dataset. Нужны три непустых split;
в holdout — supported и unsupported случаи. Все перефразировки одного задания
имеют одну family. Holdout answers остаются только в оценке; их нельзя передать в
train dataset, генерационный prompt, поиск гиперпараметров или выбор prompt.

## Подготовка и CPU contracts

Из корня репозитория (Windows: замените `bin/python` на `Scripts/python.exe`):

```bash
uv sync --python 3.12 --group sft
.venv/bin/python -m pytest labs/04_llm_finetuning/sft_workflow/test_starter.py -q
ROADMAP_RUN_SFT=1 .venv/bin/python -m pytest labs/04_llm_finetuning/sft_workflow/test_library.py -q
```

Обычные tests не запускают обучение. Explicit library contract использует только
локальную случайную модель, максимум 2 optimizer steps, и ваши функции.
Untouched starter даёт xfail и **не проходит строгий check**; skip тоже не даёт credit.
`test_library.py` требует всю группу `sft`: при явном opt-in отсутствие пакетов —
ошибка окружения, а не успех. Fresh strict target: `test_starter.py`, `test_library.py`,
`test_live.py`. Для strict run нужны оба `ROADMAP_RUN_SFT=1` и `ROADMAP_SFT_EVIDENCE`.

## Авторская проверка реального API

```bash
.venv/bin/python -m labs.04_llm_finetuning.sft_workflow.author_smoke \
  --output artifacts/sft-author-01 --steps 2
```

Новый каталог обязателен. Этот runnable teacher сохраняет локальную random Llama,
настоящий tokenizer с `{% generation %}`, adapter и `report.json`. Проверяются
ручной causal shift loss, finite values, frozen base, изменение adapter, safetensors
и fresh-base reload. Данные `author_fixture.CORPUS` нейтральные и отдельные от ваших.
Метка **RANDOM_MECHANISM_ONLY**, origin **AUTHOR**, **NO_LEARNER_CREDIT**.
Training loss этой модели ничего не доказывает о pretrained language quality.

API проверен в окружении TRL **1.16.0**, PEFT **0.21.2**, Transformers **5.17.0**,
PyTorch **2.14.0+cpu**, datasets **5.0.1**, Accelerate **1.15.0**.
Для pretokenized rows используются `processing_class`,
`dataset_kwargs={"skip_prepare_dataset": True}`, custom collator, `packing=False`,
`remove_unused_columns=False`: в этой версии SFTTrainer иначе удаляет attention_mask
до custom collator. `report_to="none"` исключает случайный MLflow/W&B tracking.
Learner contract читает именно `trainer.get_train_dataloader()`: сравнивает все IDs,
attention и labels с ожидаемыми rows независимо от shuffle, затем сравнивает
`trainer.compute_loss` с независимой shifted cross entropy до optimizer step.
Teacher-only `test_batch_contract.py` отвергает коллатор, заменяющий labels, и неверный
loss override без обучения; он не входит в learner completion.

## Независимый pretrained run и evidence

Получите разрешённый snapshot отдельно, например явной командой вне тестов
`hf download OWNER/MODEL --revision COMMIT --local-dir .model-cache/my-base`.
Выберите доступный вам model/revision и предварительно проверьте лицензию и память.
Команда — шаблон загрузки, она здесь **не запускалась**. Далее только локальные файлы:

```bash
.venv/bin/python -m labs.04_llm_finetuning.sft_workflow.learner_run \
  --base .model-cache/my-base --tokenizer .model-cache/my-base \
  --data /absolute/path/my-conversations.json --output artifacts/my-sft-01 --max-steps 4
.venv/bin/python -m labs.04_llm_finetuning.sft_workflow.evidence artifacts/my-sft-01
ROADMAP_SFT_EVIDENCE=artifacts/my-sft-01 ROADMAP_RUN_SFT=1 \
  .venv/bin/python -m pytest labs/04_llm_finetuning/sft_workflow/test_starter.py \
  labs/04_llm_finetuning/sft_workflow/test_library.py \
  labs/04_llm_finetuning/sft_workflow/test_live.py -q
```

`run_project` пока честно останавливается на TODO. Это задание написать код, не
готовая авторская дообучалка с переименованными данными. Ваша реализация использует
`local_files_only=True`, `trust_remote_code=False`, ограниченный generation budget,
новый output и фиксированные seed/config. Не пишите успешный manifest при ошибке.

`manifest.json` содержит:

| Поле | Контракт |
| --- | --- |
| exercise_id / origin / evidence_kind | `lab-sft-lora` / `LEARNER` / `LIVE_PRETRAINED` |
| review_status | `REQUIRES_REVIEW` — автоматическая согласованность не авторство |
| domain / authorship_explanation | новый домен и объяснение собственного решения |
| base_snapshot / tokenizer_snapshot | `path` абсолютного локального каталога, `source_revision`, `files`: relative path → SHA256 |
| artifacts | relative path → SHA256 всех обязательных файлов ниже |
| trained_ids | ровно train IDs |
| metrics | для каждого `base`, `improved_prompt`, `lora`: три метрики ниже |

Обязательные реальные файлы: `dataset.json` (полные rows), `splits.json`
(`train`, `validation`, `holdout` → ID lists), `predictions.json` (mode → list из
`{"id": ..., "text": ...}`), `runner.py` (ваш полный воспроизводимый runner),
`adapter/adapter_model.safetensors`, `adapter/adapter_config.json`. Base manifest
содержит config и weights; поддерживаемый tokenizer snapshot содержит
`tokenizer.json`/`tokenizer_config.json`. Validator также требует hashes всех локальных
JSON, Jinja, text, SentencePiece/vocabulary и tiktoken assets: в том числе
`chat_template.jinja`, `chat_templates/*.jinja`, added/special tokens, vocab и merges.
Они проверяются даже если submitter не включил их добровольно; изменение template
после manifest отвергается. Служебный `.cache` локальной Hub-загрузки исключён.
Все evidence JSON и Python source читаются/пишутся явно в UTF-8.
Зафиксируйте все shards, template, generation settings, prompt versions, training
config и зависимости в своём дополнительном отчёте. Не публикуйте лицензированные
weights или чувствительные данные в git; `artifacts/` игнорируется.

На **одном и том же holdout** сравните base, improved prompt и LoRA. `parse_success`
— доля ответов, распарсенных как JSON object; `field_correctness` — доля полного
совпадения JSON object с expected (лишнее поле тоже ошибка); `unsupported_handling`
— доля правильных `{"unsupported": true}` среди unsupported rows. Parse failure
не выбрасывается из знаменателя. Boolean и number различаются рекурсивно:
`true` не равен `1`, включая вложенные objects/lists; unsupported expected требует
именно boolean `true`. Числовые JSON значения `1` и `1.0` намеренно считаются
эквивалентными. Prompt выбирают только на validation.

Validator проверяет origin/identity, bytes реальных артефактов, непересечение
семейств, охват ID и пересчитывает метрики из predictions; проверяет finite LoRA
tensors. Это **проверка согласованности**, не криптографическое доказательство
pretraining, исполнения runner или авторства. Человек проверяет источник snapshot,
новый домен, историю/код ученика и отдельно **перезапускает runner**, воспроизводит
base/improved-prompt/LoRA predictions и fresh-base reload. Авторский fixture,
нарисованные метрики и чужой runner не получают credit. До этого live: **NOT_RUN**.

## Opt-in QLoRA

```bash
.venv-cuda/bin/python -m labs.04_llm_finetuning.sft_workflow.qlora \
  --base .model-cache/my-base --tokenizer .model-cache/my-base \
  --data /absolute/path/train-only-messages.json --output artifacts/qlora-01 \
  --max-steps 2 --max-length 128 --target-modules q_proj,v_proj
```

Готовый ограниченный recipe принимает 1..32 **уже выделенных TRAIN rows**, каждый
только с `messages`; проверяет длину и assistant masks до загрузки weights.
Требует отдельного совместимого CUDA PyTorch окружения и optional `quantization`
(bitsandbytes); default repository torch — CPU. Ничего не устанавливает/скачивает.
До загрузки модели проверяет flags, local paths, CUDA и capability; применяет NF4,
double quantization, `prepare_model_for_kbit_training`, LoRA и ≤4 optimizer steps.
Результат recipe не закрывает learner/live gate. 8 GB — бюджет устройства, не
гарантия размера модели: память занимают activations, sequence length, временные
buffers, adapter gradients и optimizer. Начните с короткой последовательности и
малого разрешённого snapshot; OOM — не успешный report. QLoRA здесь: **NOT_RUN**.
