# SFT, LoRA и границы адаптации

ML-DEPTH. Начните с [теории и числового разбора](theory.md), затем запустите
маленький [teacher example](demo.py). Он показывает low-rank update и reload
на явных константах, не обучает языковую модель и не заменяет PEFT experiment.
Отдельный [локальный PEFT teacher run](theory.md#настоящий-peft-lifecycle-на-локальном-transformer)
обучает настоящий LoRA adapter на tiny random Transformer и проверяет fresh-process
reload. Pretrained SFT experiment и QLoRA — **NOT_RUN** до вашего отдельного опыта.

Prerequisites: [PyTorch](../01_pytorch_foundations/README.md),
[Hugging Face](../02_huggingface_models/README.md), фиксированные split и evaluation.

Expected artifacts: разрешённый SFT dataset, chat template, train/eval config,
packing/masking contract выбранного API, LoRA adapter и reload command, результаты
исходной модели/prompting/адаптации с одинаковыми условиями и cost report.

Done: adapter загружен и проверен на независимых данных; оценены формат, деградации
и бюджет, а не только training loss. QLoRA — только после отдельной проверки
совместимости quantization/устройства; 8 GB VRAM не обещание запуска.
RAG и fine-tuning решают разные задачи и могут дополнять друг друга.
DPO/RLHF, большая LLM с нуля и платные GPU не обязательны.

Из корня проекта, в уже подготовленном CPU training окружении:

```powershell
.venv-training/Scripts/python.exe -m labs.04_llm_finetuning.demo
.venv-training/Scripts/python.exe -m pytest labs/04_llm_finetuning/test_demo.py -q
```

Для демонстрации checkpoint добавьте `--output artifacts/lora-mechanism-01`:
каталог должен быть новым. Существующие файлы не перезаписываются. Здесь нет
скачивания моделей, датасетов или PEFT. Отдельно подготовьте
[самостоятельный эксперимент](exercise/README.md); свой отчёт и результаты
заполняете вы. Строгий зачёт прежних PyTorch/HF задач не расширяется этой папкой.

Для настоящего PEFT механизма в уже подготовленном `.venv-finetuning`:

```powershell
.venv-finetuning/Scripts/python.exe -m labs.04_llm_finetuning.peft_demo --output artifacts/peft-author-01
.venv-finetuning/Scripts/python.exe -m labs.04_llm_finetuning.peft_demo --verify artifacts/peft-author-01
$env:ROADMAP_RUN_PEFT = '1'
.venv-finetuning/Scripts/python.exe -m pytest labs/04_llm_finetuning -q
Remove-Item Env:ROADMAP_RUN_PEFT
```

Новый run сохраняет base и adapter в safetensors отдельно, hashes, данные/split,
версии, bounded predictions, `report.json` и измеренный `loss.svg`. Это проверка
обучения и inference lifecycle со случайной базой, без pretrained language quality.
Opt-in tests пропускаются без `ROADMAP_RUN_PEFT=1`; с явным gate отсутствие
torch/peft/transformers/safetensors означает ошибку подготовки окружения.
Обычная установка не требует этих пакетов. Состояние optimizer/RNG не сохранено:
это inference reload, не training resume.

## Самостоятельный TRL SFT / LoRA

[Новый learner workflow](sft_workflow/README.md) добавляет отдельный `lab-sft-lora`: реальные
chat templates и TRL/PEFT mechanics, независимый pretrained evidence gate и opt-in QLoRA.
Авторский random smoke и live learner evidence проверяются отдельно.
