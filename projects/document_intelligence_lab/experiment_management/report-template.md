# Защита MLflow / Optuna

- Exercise: `ml-experiment-management`
- Автор, дата, новый домен и происхождение документов:
- Command / seed / budget / versions:
- Source SHA-256 / dataset SHA-256 / split SHA-256:
- Схема split, family policy, почему тексты не дублируются:

## Реальные trials и выбранная модель

| Trial | Params | State | Dev macro F1 | MLflow run ID | Причина исключения/выбора |
|---|---|---|---|---|---|
| | | | | | |

- Study name и расположение локального `study.sqlite`:
- Selected trial / run ID / model ID / pinned model URI / flavor SHA-256:
- Ручной расчёт F1 по сохранённым dev predictions одного trial:
- Holdout macro F1 из predictions, первое и единственное финальное применение:
- Результат reload и независимого train-only refit (не выдумывать непроверенное):

## Анализ

- `budget_bias`: заранее выбранный бюджет, selection bias, отличие nested CV:
- `failure_pruning`: COMPLETE/FAIL/PRUNED, расход бюджета, как обработан отказ:
- `holdout_policy`: почему holdout не доступен objective, что нельзя менять после оценки:
- `seed_limits`: что повторяет seed и чего он не гарантирует:
- `hf_transfer`: trial/run/checkpoint/tokenizer/template/mask в HF Trainer/SFT:
- Почему рост score не обязателен; что эти tiny данные не доказывают:

## Human rerun и защита

- Проверяющий, дата:
- Команда с выбранным проверяющим seed/budget:
- Полученные trial/run/model IDs и сохранённые predictions:
- Объяснение выбора, ручной пересчёт и вопросы по leakage:
- Решение человека; до проверки: `REQUIRES_REVIEW`.
