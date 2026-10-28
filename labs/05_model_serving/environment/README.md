# Отдельный Linux runtime: рецепт, ещё не проверенный lock

Статус **NOT_RUN**. На 11.10.2026 доступен Windows base client с httpx 0.28.1;
WSL не установлен, training torch 2.14.0+cpu, RTX 5060 Laptop имеет 8151 MiB и
compute capability 12.0. GPU через Linux и конкретный wheel не проверены.
[Compute guide](../../../docs/compute-guide.md#vllm-linux-route) объясняет маршрут
Ubuntu 24.04 LTS/WSL2 либо native Linux. Установки, downloads и server startup
требуют отдельного действия оператора; команды ниже сейчас не исполнялись.

Официальная [vLLM GPU инструкция](https://docs.vllm.ai/en/latest/getting_started/installation/gpu/)
при чтении 11.10.2026 требует Linux, Python 3.11–3.14 и NVIDIA capability ≥7.5;
fresh environment нужен из-за связи kernels с CUDA/PyTorch build. Текущие default
binaries указаны как CUDA 12.9; для Blackwell документация отмечает минимум 12.8.
Это compatibility recipe, **не tested lock RTX 5060**. В WSL не ставить Linux
display driver поверх Windows driver: [NVIDIA CUDA on WSL](https://docs.nvidia.com/cuda/wsl-user-guide/index.html).

## Граница окружений

Serving environment, cache и snapshots создаются вне Windows checkout, например
в выбранном оператором `/srv/aiml-serving`. Это пример пути, не уже существующая
директория и не команда создания. Не копировать Windows `.venv`, не менять root
`uv.lock`/CPU Torch index. Клиент остаётся в Windows `.venv`; Linux server получает
собственный resolved lock со всеми transitive GPU dependencies, wheel sources,
hashes, Python/platform и runtime manifest. GPU memory fit заранее неизвестен.

До установки оператор выбирает точный release vLLM/CUDA wheel для Linux/Python/GPU,
проверяет release docs, разрешает зависимости и составляет hash-pinned
`requirements.lock`. В нём должны оказаться и совместимые kernel distributions.
Такого lock в этом пакете **нет**: dependency resolution/install не разрешены,
выдумывать версии/хеши нельзя. `pip freeze` фиксирует версии, но не заменяет
полный lock с wheel hashes и index provenance.

После разрешённой подготовки, только в новой отдельной Linux среде:

```bash
# SERVING_ROOT — уже выбранный абсолютный Linux путь с reviewed lock.
test "$(uname -s)" = Linux || exit 2
test -n "${SERVING_ROOT:-}" && test -s "$SERVING_ROOT/requirements.lock" || exit 2
test -x "$SERVING_ROOT/.venv/bin/python" || exit 2
uv pip sync --python "$SERVING_ROOT/.venv/bin/python" --require-hashes "$SERVING_ROOT/requirements.lock"
"$SERVING_ROOT/.venv/bin/vllm" download-kernels
```

Эта **preparation** секция обращается к сети и устанавливает packages/kernels;
её не выполнять для чтения урока/pytest. `uv pip sync` — только по уже reviewed
lock в новой serving среде; [uv reference](https://docs.astral.sh/uv/reference/cli/#uv-pip-sync).
Создание самой среды/разрешение lock — отдельный согласованный setup, не скрытая
команда `uv run`. После `download-kernels` сверить весь installed inventory с
финальным lock, включая FlashInfer/cubin/JIT-cache при их наличии. При изменении
версий заново подготовить согласованные kernels. До совпадения остановиться.
Текущая документация предупреждает: без этого startup может скачивать/компилировать
kernels, особенно на Blackwell. Локальный snapshot сам по себе не делает startup offline.

## Модель и ресурсы: сначала inventory

Первый кандидат — Qwen/Qwen3-0.6B, Apache-2.0. При чтении
[tree](https://huggingface.co/Qwen/Qwen3-0.6B/tree/main) выбрана revision
[`c1899de289a04d12100db370d81485cdf75e47ca`](https://huggingface.co/Qwen/Qwen3-0.6B/commit/c1899de289a04d12100db370d81485cdf75e47ca).
Это metadata evidence, не скачивание и не гарантия качества. Review лицензии
делает оператор; `license_reviewed=false` в шаблоне намеренно не даёт готовность.

| Что | Metadata до загрузки | Что нужно записать после явной подготовки |
| --- | --- | --- |
| `model.safetensors` | 1,503,300,328 bytes; около 1.50 GB | SHA-256 сверить с published pointer и локальным файлом |
| config, generation config | tree показывает 726/239 bytes | точный размер и SHA-256 выбранной revision |
| tokenizer.json/config, vocab, merges | примерно 11.4 MB / 9.73 kB / 2.78 MB / 1.67 MB в tree | точные bytes/hashes, chat template, stop tokens |
| LICENSE | Apache-2.0, около 11.3 kB в tree | прочитанная лицензия и локальный hash |
| Linux wheels и lock | версии/bytes/hashes пока unknown | source URL/index, exact versions, architecture, hashes всех wheels |
| FlashInfer kernels/cache | состав и объём пока unknown | версии, cache/root paths, каждый используемый file/bytes/hash |

Published SHA-256 весов:
`f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b`.
Источник [pinned blob metadata](https://huggingface.co/Qwen/Qwen3-0.6B/blob/c1899de289a04d12100db370d81485cdf75e47ca/model.safetensors);
точные bytes прочитаны из [LFS pointer](https://huggingface.co/Qwen/Qwen3-0.6B/raw/main/model.safetensors)
с тем же hash. Остальные rounded sizes — ориентир traffic, **не hash allowlist**.
До загрузки проверьте metadata именно pinned revision, свободный диск с запасом
под wheels/cache и RAM; модель и runtime по отдельности занимают место.

Не скачивать все модели. После первого smoke выбрать при необходимости **одну**:
[Qwen2.5-1.5B-Instruct или SmolLM2-1.7B-Instruct](../../../docs/compute-guide.md#vllm-candidates).
Их revision/конкретные assets ещё не выбраны; память только весов в compute guide
не равна peak VRAM. SmolLM2 прежде всего англоязычная; русский оценить отдельно.

Явная preparation download команда после review трафика/лицензии, с уже установленным
и зафиксированным `hf` в Linux serving environment:

```bash
test -x "$SERVING_ROOT/.venv/bin/hf" || exit 2
test -n "${MODEL_SNAPSHOT:-}" && test ! -e "$MODEL_SNAPSHOT" || exit 2
"$SERVING_ROOT/.venv/bin/hf" download Qwen/Qwen3-0.6B \
  --revision c1899de289a04d12100db370d81485cdf75e47ca \
  --local-dir "$MODEL_SNAPSHOT" \
  --include model.safetensors config.json generation_config.json tokenizer.json \
  tokenizer_config.json merges.txt vocab.json LICENSE
```

Смысл flags: [официальный HF CLI](https://huggingface.co/docs/huggingface_hub/guides/cli#hf-download).
Отдельный новый destination исключает молчаливую замену старых/частичных artifacts.
Если загрузка прервалась, исследовать staging и hashes, не объявлять его готовым
snapshot и не перезаписывать повреждённые файлы автоматически.

Скопируйте [manifest template](manifest.template.json) **в generated directory**,
заполните абсолютные Linux roots и file inventories. Не заменяйте `null`
предположениями. Для каждого файла `stat --format=%s` даёт bytes,
`sha256sum` — локальный digest; сравните с trusted metadata/approved wheel source.
Самостоятельно вычисленный hash фиксирует воспроизводимость, а не происхождение.
`runtime_files` должен содержать итоговый `requirements.lock`, wheel/source inventory
и диагностические evidence; `runtime_versions` — все locked distributions,
включая vllm/torch/FlashInfer и kernel packages. `kernel_files` не может быть пустым.
Не помещайте cache, weights, секреты и generated manifest в Git.

## Read-only preflight и tiny CUDA

Из корня Linux копии курса, где уже существует отдельная среда:

```bash
"$SERVING_ROOT/.venv/bin/python" -m labs.05_model_serving.environment.preflight "$SERVING_ROOT/manifest.json"
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv,noheader
```

`preflight` не импортирует torch/vLLM, не запускает сервер и не скачивает файлы.
Он проверяет Linux, exact revision/license acknowledgement, roots, sizes/hashes,
обязательные config/tokenizer/safetensors и installed distribution versions.
Missing/partial/corrupt assets → exit 2 / NOT_RUN. Успех означает только
INVENTORY_OK; полнота kernel inventory и соответствие lock требуют review.

Далее после отдельного разрешения на GPU smoke, в этом же interpreter:

```bash
"$SERVING_ROOT/.venv/bin/python" -c 'import torch; assert torch.cuda.is_available(); x=torch.tensor([2.0],device="cuda"); y=x*x; torch.cuda.synchronize(); assert y.item()==4.0; print(torch.__version__,torch.version.cuda,torch.cuda.get_device_name(),torch.cuda.get_device_capability())'
"$SERVING_ROOT/.venv/bin/vllm" serve --help
```

Сохранить реальные выводы и parser flags. Tiny tensor доказывает CUDA operation,
но не запуск модели. Любая ошибка/несовместимость — остановка; не менять Windows
training environment ради её обхода. Никакого автоматического fall back на HF/Ollama.

## Offline serving candidate и restart

Все следующие flags проверены **по официальной документации**, установленный
parser и настоящий startup **NOT_RUN**:
[serve reference](https://docs.vllm.ai/en/latest/cli/serve/).
Перед запуском сопоставить их с `serve --help`; неизвестный flag — остановка,
не удалять защитное ограничение наугад. `MODEL_SNAPSHOT` — абсолютный путь,
совпадающий с проверенным `model_root` в manifest; `MODEL_ID` — его `server_model_id`.

```bash
test -n "${MODEL_SNAPSHOT:-}" && test -d "$MODEL_SNAPSHOT" || exit 2
test -n "${MODEL_ID:-}" || exit 2
"$SERVING_ROOT/.venv/bin/python" -m labs.05_model_serving.environment.preflight "$SERVING_ROOT/manifest.json" || exit 2
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 \
"$SERVING_ROOT/.venv/bin/vllm" serve "$MODEL_SNAPSHOT" \
  --tokenizer "$MODEL_SNAPSHOT" --served-model-name "$MODEL_ID" \
  --host 127.0.0.1 --port 8000 --model-impl vllm --load-format safetensors \
  --max-model-len 1024 --max-num-seqs 1 --dtype half \
  --gpu-memory-utilization 0.65 --enforce-eager --generation-config vllm \
  --no-trust-remote-code --no-enable-auto-tool-choice --no-enable-prefix-caching
```

В первой конфигурации tools/remote code отключены; client не посылает tools.
`generation-config vllm` делает server defaults явными, client задаёт temperature
и `max_tokens=128`. Qwen3 request передаёт `chat_template_kwargs.enable_thinking=false`:
см. [Qwen3 card](https://huggingface.co/Qwen/Qwen3-0.6B#switching-between-thinking-and-non-thinking-mode).
Контекст 1024 включает chat template + prompt + response, а не только пользовательский
текст. Другому tokenizer нельзя переносить количество токенов/stop tokens автоматически.
При thinking бюджет 128 может кончиться до видимого ответа; такое усечение записать
как limitation, не как успешный короткий ответ. Thinking experiment позже имеет
собственный budget/config и не смешивается с baseline.

HF offline flags останавливают Hub fetch, но не являются сетевым sandbox всех
CUDA backends. Убедиться в заранее подготовленных kernels и испытать запуск
при реально заблокированном outbound доступе в согласованной Linux среде.
Без такой проверки `offline_launch=NOT_RUN`, даже если API ответил.

Readiness — не лог «startup complete», а `/v1/models` с точным MODEL_ID и короткий
[streaming smoke](../smoke/README.md). Сохранить process/version evidence.
Остановить сервер Ctrl+C, дождаться завершения процесса и стабилизации GPU памяти,
повторить **ту же** команду из того же snapshot/lock. После смены модели изменить
MODEL_ID и проверить readiness заново: старый server id не должен случайно пройти.
Concurrency 2 пробовать после успеха 1; max-num-seqs=2 — отдельный записанный
server config. Insufficient memory → остановка/меньшая модель/отчёт, не OOM stress.
