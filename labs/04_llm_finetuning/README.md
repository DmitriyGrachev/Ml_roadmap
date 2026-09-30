# SFT и PEFT — спецификация

ML-DEPTH · PLANNED. Код обучения адаптера в этой волне не реализован.

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
