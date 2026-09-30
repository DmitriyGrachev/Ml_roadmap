# Окружение и ресурсы

База: Windows/PyCharm, Python 3.12. GPU не нужен для начала. Проверенные команды
и границы — [журнал первой волны](wave1-verification.md) и
[свежая проверка второй волны](wave2-verification.md).

## Два профиля одного проекта

```powershell
# База: Python, data и существующие offline modules
uv sync --locked
uv run python scripts/learn.py validate-env

# Только когда переходите к моделям
uv sync --locked --group training
uv run --group training python -m labs.01_pytorch_foundations.example
uv run --group training python -m labs.02_huggingface_models.example
```

Linux: те же команды `uv`; путь интерпретатора `.venv/bin/python` вместо
`.venv\Scripts\python.exe`. Инструкции Linux не равны проверке Linux.

В PyCharm выберите `.venv\Scripts\python.exe`, working directory — корень
репозитория. Run configuration использует module name, например
`labs.01_pytorch_foundations.example`, не директорию с lesson README.

`training` не default group. Не используйте старое `uv sync --all-groups` для
обычного старта: теперь это сознательная установка и тяжёлой группы.
После установки training используйте `uv run --group training ...`: простой
`uv run` синхронизирует базовый набор и может удалить opt-in библиотеки.
Верификация сопровождающего использует `.venv-training` через
`UV_PROJECT_ENVIRONMENT`, чтобы проверить отсутствие torch в базовой `.venv`.
Это два интерпретатора одного pyproject/lock, не отдельный проект или runner.

Чтобы держать лёгкую базу и training одновременно (рекомендуемый вариант для
второй волны), из корня проекта в PowerShell:

```powershell
uv sync --locked
$env:UV_PROJECT_ENVIRONMENT = ".venv-training"
uv sync --locked --group training
Remove-Item Env:UV_PROJECT_ENVIRONMENT
.venv/Scripts/python.exe scripts/learn.py test ml-knn-mechanics
.venv-training/Scripts/python.exe scripts/learn.py test lab-attention-mechanics
.venv-training/Scripts/python.exe scripts/learn.py check lab-attention-mechanics
```

В PyCharm для трёх continuation ID (`lab-training-resume`,
`lab-training-diagnostics`, `lab-attention-mechanics`) выберите
`.venv-training\Scripts\python.exe`. Остальные 11 новых exercise ID используют
базовую `.venv`. Прямой запуск выбранного interpreter не пересинхронизирует другой.
`check` до реализации TODO должен завершаться ненулевым кодом. Короткие offline
примеры и механические smokes не являются собственным исследованием ученика;
большой data release и все pretrained/GPU/cloud опыты требуют отдельного запуска.

Зафиксировано: `torch==2.14.0+cpu` из официального CPU index,
`transformers==5.17.0`, `datasets==5.0.1`; transitive versions — в `uv.lock`.
MLflow, PEFT, vLLM и CUDA не включены. Base libraries не обновлялись массово.

Проверки типов разделены по зависимостям: `uv run mypy` проверяет базовые модули
и tooling; `uv run --group training mypy -p labs` дополнительно проверяет обе labs
с настоящими типами PyTorch. Это не заглушки типов тяжёлых библиотек в базовой среде.

## Ресурсы и явные действия

| Профиль | Сеть/секреты/расходы | RAM/диск и ограничения |
| --- | --- | --- |
| Базовые уроки/tests | установка packages один раз; tests offline, без ключей | обычный Python stack; модели не скачиваются |
| PyTorch CPU smoke | без сети, локальные синтетические данные, без платежей | оценка 1–2 GB RAM; небольшая временная модель; CPU only |
| HF offline smoke | случайный local encoder/tokenizer, без сети и pretrained weights | оценка 1–2 GB RAM; проверяет механику, НЕ качество |
| HF pretrained experiment | отдельная explicit download command в lab02; public ungated Hub, без ключей/платных API | MiniLM weights ~90.9 MB + Bitext CSV ~19.2 MB и tokenizer/config; оценка 2–4 GB RAM, несколько GB диска с окружением |
| CUDA/Colab/vLLM | NOT_RUN, отдельная будущая проверка/окружение | RTX 5060 Laptop 8 GB не гарантия совместимости или вместимости |

Оценки памяти не измеренный benchmark. При установке группы wheel torch был
~118.3 MiB; это библиотека, не pretrained модель. Сетевую модельную загрузку
мы не запускали: выполните её сами по lab02, прочитав license/size и ограничения.
Ничего не скачивается на import или pytest. Возможный traffic вашего провайдера
не равен платному inference API; платный cloud/GPU автоматически не запускается.

Веса/cache/отчёты не включайте в Git. Не загружайте недоверенные pickle/joblib,
не включайте `trust_remote_code=True`. Данные и ответы модели — недоверенный ввод;
prompt и regex не гарантия безопасности.
