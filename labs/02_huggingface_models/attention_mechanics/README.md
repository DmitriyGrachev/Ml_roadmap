# Механика attention: маски и градиенты

ID: `lab-attention-mechanics`. Prerequisites: [lab-huggingface](../README.md)
и [data-numpy](../../../modules/03_data_foundations/01_numpy/README.md).
Это отдельное упражнение после lab02; старые задания и `starter.py` lab02 не меняются.
Обязательные проверки работают на CPU и без сети.

## От текста к loss

1. Tokenizer разбивает текст на токены и возвращает целочисленные ID `[B,T]`.
   Padding добавляет фиктивные позиции. Embedding lookup даёт `[B,T,D]`,
   позиционные embeddings той же формы сообщают порядок; после сложения форма та же.
2. Проекции дают `Q`, `K`, `V` формы `[B,H,T,Dh]`, где обычно `D=H·Dh`.
   Для cross-attention длины различаются: `Q=[B,H,Tq,Dh]`,
   `K=[B,H,Tk,Dh]`, `V=[B,H,Tk,Dh]`.
3. Scores `Q @ Kᵀ / √Dh` имеют форму `[B,H,Tq,Tk]`. Bool-маска
   `[B,1,Tq,Tk]` распространяется на все головы: `True` разрешает ключ.
   Padding закрывает фиктивные ключи; causal mask закрывает будущие ключи.
   При их совместном использовании берите логическое И. После маски softmax
   нормирует **каждую** query-строку по допустимым ключам; строка без ключей
   здесь считается ошибкой. Взвешенная сумма `softmax(scores) @ V` имеет
   форму `[B,H,Tq,Dh]`.
4. Головы объединяют обратно в `[B,Tq,H·Dh]`, выходная проекция возвращает
   размер скрытого представления. Residual добавляет вход при совместимой форме;
   нормализация стабилизирует следующие блоки. Feed-forward часть также обычно
   заключена в residual/norm. Голова классификации даёт `[B,C]` logits и
   cross-entropy с метками `[B]`; языковая голова даёт `[B,T,Vocab]` logits
   и loss на нужных позициях. Эти головы решают разные задачи.

Encoder-only (например, BERT) видит обе стороны токена и подходит для
классификации или извлечения представлений. Decoder-only закрывает будущие
позиции и предсказывает следующий токен, поэтому подходит для генерации.
Encoder–decoder читает вход двусторонним encoder и генерирует выход causal
decoder с cross-attention к входу, например при переводе или суммаризации.
Эта схема объясняет механику; она не вводит новый курс по библиотеке Hugging Face.

## Ваш контракт

Меняйте только [starter.py](starter.py): реализуйте
`attention(q, k, v, allowed) -> Tensor`. Входы — конечные CPU float32/float64
тензоры одинакового dtype: `q=[B,H,Tq,Dh]`, `k=[B,H,Tk,Dh]`, `v=[B,H,Tk,Dh]` с `Dh>0`.
Маска — bool `[B,1,Tq,Tk]`, `True` означает доступный ключ. Длины ключей и
values совпадают, dropout отсутствует. Неверные формы, типы, nonfinite значения
и **любая** полностью закрытая query-строка дают `ValueError`. Выход сохраняет
dtype, форму `[B,H,Tq,Dh]` и градиент по `q`, `k`, `v`.

[test_starter.py](test_starter.py) сравнивает значения и градиенты с
`torch.nn.functional.scaled_dot_product_attention` на других случайных данных:
float64 `rtol=1e-7, atol=1e-9`; float32 `rtol=1e-5, atol=1e-6`.
Он отдельно меняет padding и будущие values и проверяет отсутствие влияния.
Изолированный [example.py](example.py) показывает библиотечную операцию на
синтетических векторах; это не реализация learner TODO.

Подсказки по этапам:

1. Проверьте формы, dtype, CPU, конечность, `Dh` и хотя бы один разрешённый
   ключ в каждой строке до softmax.
2. Считайте scores по последним двум осям и масштабируйте по `Dh`, не по `T`.
3. Закройте недоступные scores **до** softmax. Проверьте направление bool-маски
   на примере, где запрещённый value очень велик.
4. После softmax умножьте веса на `V`; проверьте backward на всех трёх входах.

Из корня репозитория в PowerShell, с установленной training-группой:

```powershell
.venv-training/Scripts/python.exe -m labs.02_huggingface_models.attention_mechanics.example
.venv-training/Scripts/python.exe scripts/learn.py test lab-attention-mechanics
.venv-training/Scripts/python.exe scripts/learn.py check lab-attention-mechanics
.venv-training/Scripts/python.exe -m pytest labs/02_huggingface_models/attention_mechanics/test_starter.py labs/02_huggingface_models/attention_mechanics/test_example.py -q
```

В PyCharm выберите `.venv-training/Scripts/python.exe` и корень репозитория
как working directory. Пока TODO не выполнен, `test` отмечает его `XFAIL`,
а строгий `check` зачёт не даёт. `test_example.py` — offline smoke библиотеки;
он не проверяет вашу реализацию. `test_starter.py` — unit-контракт.
ML evaluation на реальных данных здесь **NOT_RUN**: численная близость к библиотеке
не показывает качество языковой модели. Объяснение выбора масок, shape trace и
своих результатов остаётся **REQUIRES_REVIEW** человеком.

Дальше самостоятельно, **OPTIONAL/PLANNED**: обучить маленькую символьную
языковую модель на локальном тексте и сравнить causal mask с её отсутствием.
Это не новая обязательная лабораторная.
