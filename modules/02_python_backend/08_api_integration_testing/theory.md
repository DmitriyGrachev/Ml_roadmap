# Fixture отдаёт ресурс на время, а не навсегда

## Зачем и что уже нужно знать

Два теста добавляют заметки на полку. Каждый должен начать с пустой полки и
получить собственный app, store и client. При падении assert уборка всё равно
обязана завершиться. Нужны [pytest и независимые ожидания](../../01_python_core/09_testing/README.md),
[FastAPI dependencies](../03_architecture_dependencies/README.md) и
[исключения/finally](../../01_python_core/06_exceptions_io/README.md).

Этот пример — другая предметная область и маршруты `/shelf-notes`.
Учебный платёжный review-код остаётся намеренно связанным до вашей работы.

## Ситуация и прогноз

Первый тест создал `{"id": 1, "text": "Read chapter 2"}`. Второй читает список.
Что он должен увидеть? А если первый упал после создания заметки — можно ли
второму доверять, если все тесты работают с одной глобальной application?

Интуиция: fixture выдаёт тесту ключ от комнаты, затем возвращает ресурсы и
убирает свои изменения. Но уборка не должна зависеть от того, довольны ли мы
результатом теста. **Ownership** (владение) означает, что создавший ресурс код
отвечает за его срок жизни; глобальный reset чужого состояния владение размывает.

| Объект | Где создаётся | Кто завершает работу |
|---|---|---|
| FastAPI app | каждый вызов `client_scope()` | lifespan в контексте клиента |
| NoteStore | тот же вызов | становится недоступен следующему тесту |
| dependency override | app этого вызова | finally того же scope |
| TestClient | тот же вызов | context exit + явный close |

`NoteStore` — простой реальный in-memory компонент: add меняет его список,
GET возвращает этот список. Никакой внешний сервис здесь не имитируется.

## Что делают yield и контекст

**Fixture** подготавливает вход теста. При стандартном **function scope**
pytest запрашивает отдельный экземпляр для каждого тестового вызова, в том числе
каждого набора параметров. Код до `yield` — setup, выданное значение — вход
теста, продолжение после yield — teardown. Pytest возобновляет генератор и
после падения теста. Если setup упал до yield, нельзя рассчитывать на обычное
продолжение после него: защищайте уже полученные ресурсы try/finally.
[pytest — yield fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html#yield-fixtures-recommended).

В [walkthrough.py](walkthrough.py) авторская fixture короткая:

```python
@pytest.fixture
def shelf_client() -> Iterator[ClientCase]:
    with client_scope() as case:
        yield case
```

`Iterator[ClientCase]` описывает генератор: это не `-> ClientCase` с обычным
return. Pytest управляет его продолжением; сам тест получает один ClientCase.
`client_scope` — `@contextmanager`, тоже построенный на yield, но управляемый
обычным `with`. Два разных потребителя используют один механизм владения:
pytest в тесте, `with` в самостоятельной демонстрации.

Главная часть scope после создания свежего app и store:

```python
@contextmanager
def client_scope() -> Iterator[ClientCase]:
    events = ["setup"]
    app = create_app(events)
    store = NoteStore()
    app.dependency_overrides[get_store] = lambda: store
    client = TestClient(app)
    try:
        with client:
            yield ClientCase(app, store, client, events)
    finally:
        try:
            client.close()
        finally:
            app.dependency_overrides.clear()
            events.append("teardown")
```

Ключ override — сама функция dependency `get_store`, а не её строковое имя и
не результат её вызова. Значение — функция, возвращающая store данного теста.
FastAPI использует её при разрешении Depends, поэтому тест по-прежнему проходит
через настоящий HTTP-маршрут. Чистить словарь безопасно именно потому, что app
свежий и все его overrides принадлежат этому scope.
[FastAPI — overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/).

Вложенный finally очищает overrides, даже если close сам выбросит исключение.
Он не обещает скрыть такую ошибку: ошибка уборки должна быть видна. Это пример
для успешно созданного TestClient и для сбоев в теле/context, а не универсальный
менеджер любых частично созданных сетевых ресурсов.

## Почему контекст TestClient важен

**Lifespan** — startup и shutdown приложения. Само `TestClient(app)` не запускает
startup. Контекст клиента запускает его при входе и выполняет shutdown при выходе.
[Starlette — TestClient](https://starlette.dev/testclient/).
У app есть lifespan с журналом: `startup` перед доступом к маршрутам, `shutdown`
в finally при выходе. Журнал — наблюдение за настоящим жизненным циклом приложения.

В проверенной локальной Starlette 1.6.0 `TestClient.__exit__` закрывает lifespan/
portal, но унаследованный HTTP-клиент после этого ещё имеет `is_closed=False`.
Авторский тест обнаружил это, исходник установленной библиотеки подтвердил.
Поэтому scope дополнительно вызывает `client.close()`; тест проверяет и shutdown,
и `is_closed=True`. Не делайте вывод «раз with завершён, закрыты все слои» только
по сходству синтаксиса с другим context manager.

```text
setup: fresh app/store + override
          │
       startup
          │
        yield ──► тело теста: HTTP запросы → assert или исключение
          │                                   │
          ◄───────────────────────────────────┘
       shutdown → client.close → clear overrides → teardown
```

Исключение теста не превращается в успешный результат, но не отменяет уборку.
Не кладите cleanup только после assert в самом тесте: до этой строки исполнение
может вообще не дойти.

## Полный запуск

```powershell
uv run --no-sync python modules/02_python_backend/08_api_integration_testing/walkthrough.py
uv run --no-sync pytest modules/02_python_backend/tests/test_r02_boundaries.py -q
```

Полный stdout демо:

```text
created: 201 {'id': 1, 'text': 'Read chapter 2'}
during: ['setup', 'startup']
after: ['setup', 'startup', 'shutdown', 'teardown']; overrides={}
caught: deliberate body failure
after failure: ['setup', 'startup', 'shutdown', 'teardown']; overrides={}
fresh notes: []
```

После yield первое тело создало заметку через POST. Выход дописал shutdown и
teardown. Следующий scope специально выбросил ValueError; тот же порядок уборки
сохранился, а ошибка дошла до вызывающего кода. Третий app получил отдельный store.

Авторские тесты дополнительно запускают маленький дочерний pytest: первый тест
намеренно падает после POST, второй проверяет уборку первого и пустой новый app.
Дочерний результат `1 failed, 1 passed` ожидаем, внешний авторский тест зелёный.
Это проверка реального pytest teardown, а не только ручного вызова генератора.

Прогноз перед изменением: замените fresh store на один глобальный store в копии.
Какая строка последнего GET изменится? Затем замените только `yield case` на
`return case` в fixture. Почему `with` завершится до того, как тест получит client?
Вернувшийся объект уже не имеет нужного срока жизни.

## Типичная ошибка

Присвоить override, вернуть клиент и забыть finally. Такой тест может долго
проходить за счёт разных идентификаторов, а потом стать зависимым от порядка.
Разные business IDs не доказывают изоляцию. Сравнение с Spring test slice полезно
для роли теста границы, но здесь нет автоматически сбрасываемого общего application
context: factory, scope и cleanup видны в Python-коде.

Не проверяйте только `store.notes` вместо HTTP-ответа: это пропустит неправильный
status code, сериализацию и ошибочную dependency в маршруте. Авторский тест
проверяет полный JSON POST и пустой JSON GET нового приложения.

## Проверка понимания

1. Какие четыре вида состояния принадлежат каждому вызову fixture?
2. Почему global app плюс новый client ещё не дают изоляции?
3. Что служит ключом dependency_overrides и когда используется его значение?
4. Кто возобновляет yield fixture после неуспешного assert?
5. Что случится с ресурсом при return изнутри with вместо yield?
6. Почему проверяются shutdown и is_closed, а не только одно из них?
7. Когда clear всего словаря overrides был бы опасен для чужого состояния?

<details>
<summary>Сверка после собственной попытки</summary>

1. App, store, override, client. 2. Состояние app и overrides остаётся общим.
3. Callable dependency; замена вызывается при разрешении Depends.
4. Pytest. 5. Контекст выйдет и выполнит cleanup до выполнения теста.
6. Lifespan и HTTP-client — разные части жизненного цикла.
7. Если app общий и в словаре есть overrides, которыми владеет другой код.

</details>

## Перенос в практику

Независимая вариация: два теста локальной корзины `/basket-items`. Один создаёт
две позиции и намеренно падает, второй начинает с пустой корзины. До реализации
нарисуйте владельца app, store и override; объясните, как проверить teardown
упавшего теста без «ожидаемо красного» всего основного набора. Готового решения
корзины здесь нет.

Затем [backend-api-test-review](exercises/api_test_review/README.md): сохраните
существующие HTTP-ответы и оба порядка действий, а владение и fixture исправьте
самостоятельно. Этот материал не меняет её файлы, assertions или student status.

## Источники и остановка

Проверено 2026-10-11: официальные страницы открыты через web; локальные HTTP,
success/failure cleanup и дочерний pytest выполнены. Документация английская:

- [pytest — Fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html):
  scope, yield fixtures, handling errors и safe teardowns; остановиться до
  сложной parametrization fixtures.
- [FastAPI — Testing dependencies with overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/):
  прочитать пример и reset overrides; перенести владение на свежий app.
- [Starlette — TestClient](https://starlette.dev/testclient/):
  раздел lifespan/context manager. Дополнительный close обоснован также
  локальным исходником установленной 1.6.0, не обещанием для всех будущих версий.

Нет внешнего HTTP-сервера, Docker или PostgreSQL. Зелёный авторский тест
подтверждает демонстрацию, а не освоение code review учеником.
