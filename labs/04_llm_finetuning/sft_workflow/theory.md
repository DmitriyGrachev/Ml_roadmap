# От conversation к проверяемому adapter

Prerequisites: tensor shapes, cross entropy, causal attention, замороженные weights,
[PyTorch efficiency](../../01_pytorch_foundations/exercises/training_efficiency/README.md).
Сначала выполните mask вручную, потом проверяйте библиотечный batch.

## Схема и причинный loss

Conversation — не просто склеенный prompt. Chat template вводит управляющие tokens;
роль assistant, padding и special delimiters должны иметь однозначный контракт.
`apply_chat_template(..., tokenize=True, return_dict=True,
return_assistant_tokens_mask=True)` использует template с `{% generation %}`.
Если модельный template не поддерживает assistant mask, нужно корректно адаптировать
его и проверить token offsets, а не объявлять prompt целевым ответом.

| Position | Token | Assistant mask | Label | Предсказывает logit |
| --- | --- | --- | --- | --- |
| 0 | user | 0 | -100 | — |
| 1 | repeat | 0 | -100 | — |
| 2 | amber | 0 | -100 | — |
| 3 | assistant | 0 | -100 | — |
| 4 | amber | 1 | amber ID | position 3 |
| 5 | EOS | 1 | EOS ID | position 4 |
| 6 | PAD | 0 | -100 | — |

Causal model сам сопоставляет `logits[:, :-1]` и `labels[:, 1:]`. Labels остаются
unshifted. Attention mask 0 отключает PAD как контекст; label -100 исключает его
из loss. Это разные механизмы. Если вручную сдвинуть labels ещё раз, модель учит
не те цели. В author template EOS входит в generation region; для другого template
явно решите, входит ли terminator в цель. Не обрезайте ответ молча: отбрасывайте
строку с диагностикой либо меняйте max_length до подготовки train.

## Разбиение прежде токенизации

ID отвечает за identity записи, family — за identity смысла/перефразировки.
Сначала назначьте family единственный split. Затем токенизируйте train отдельно.
Validation используется для prompt/config selection; holdout открывают для финальной
оценки. Даже разные ID не исключают leakage одинакового ответа в перефразировках.
В generative holdout подаётся только user часть и generation prompt; expected
assistant answer нужен evaluator, но не модели.

## Что именно меняет LoRA

Для линейного слоя `y = Wx` LoRA добавляет `ΔW = (alpha / r) BA`, где
`A: r × d_in`, `B: d_out × r`. Trainable count приблизительно
`r(d_in + d_out)` вместо `d_in*d_out` на выбранный слой. Rank и target_modules —
гиперпараметры, не обещание качества. Base weights заморожены, но base forward
и propagation до adapters всё ещё требуют вычислений и activation memory.
Проверьте `requires_grad`, gradients и реальные tensor deltas после update.

Сохранённый adapter не содержит исходную базу целиком. Для reload нужны точные
base revision, tokenizer/template и adapter config. Fresh-base reload проверяет
artifact, а сравнение logits на ещё живом объекте без загрузки файлов — нет.
Inference reload не восстанавливает optimizer/RNG/cursor; exact resume — отдельная
задача. Safetensors исключает pickle-десериализацию tensors, но не доказывает их
происхождение или качество.

## Выбор следующего метода

| Потребность | Следующая гипотеза | Что потребуется |
| --- | --- | --- |
| Выучить формат/поведение на демонстрациях | SFT | качественные инструкции и ответы |
| Сравнить предпочтительные ответы | DPO | пары chosen/rejected, независимая оценка |
| Перенести поведение teacher в меньший student | distillation | разрешённые teacher outputs/logits и budget |
| Адаптировать языковые представления к корпусу | continued pretraining | чистый большой domain corpus и контроль forgetting |
| Внести свежие проверяемые факты | retrieval/RAG | источники, retrieval eval и attribution |

Не превращайте каждый вопрос в training. Prompt baseline нужен, чтобы оценить,
окупает ли LoRA дополнительные данные, training time и поддержку adapter. Снижение
train loss без holdout format/field/unsupported оценок не доказывает полезность.
Ни DPO, ни distillation, ни continued pretraining здесь не требуют большого run.

## Типичные ошибки и перенос

Prompt tokens в loss, double shift, потерянный assistant mask, implicit truncation,
повтор family в train/test, случайное обучение holdout и коллатор, заменивший labels,
могут давать правдоподобный loss. Проверяйте один batch вручную и независимый loss.
Для переноса на другую модель сначала проверьте template, target_modules, длину и
precision. Затем frozen-base/changed-adapter, reload, и только потом качество.
Критерий понимания: объяснить каждый target token, показать независимые splits,
воспроизвести три baseline на общих ID и назвать ограничения measured evidence.
