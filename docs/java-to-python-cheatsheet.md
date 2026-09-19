# Java-to-Python cheat sheet

These mappings shorten orientation; they are not claims that the two runtimes or ecosystems are interchangeable.

| Java concept | Python counterpart | Semantic difference |
| --- | --- | --- |
| `record Payment(...)` | `@dataclass(frozen=True)` | A Java record has language-defined component, equality, and accessor behavior; a dataclass generates configurable methods and immutability is a convention enforced through generated assignment behavior. |
| `interface PaymentProcessor` | `typing.Protocol` or a small abstract base class | Java interfaces are nominal: a type declares implementation. Protocols can be structural, so compatible methods satisfy the boundary without an explicit declaration. |
| Stream API | Iterables, generators, comprehensions, and `itertools` | Streams are an explicit pipeline API; Python often expresses lazy or eager traversal directly, and many operations return concrete collections unless you choose a generator. |
| `Optional<T>` | `T | None` | `None` is a normal singleton value rather than an optional wrapper; callers must use type narrowing and explicit checks instead of fluent optional operations. |
| JUnit | pytest | Pytest uses plain functions, fixtures, parametrization, and assertion introspection; it does not require test classes or annotation-based lifecycle methods. |
| Maven or Gradle | `pyproject.toml` with `uv` | Python packaging metadata and environment resolution are separate concerns; `uv` manages a virtual environment and lockfile rather than compiling a JVM project. |
| Bean Validation annotations | Pydantic models and field validators | Pydantic validates and parses data when models are created; it is not an annotation processor layered over arbitrary Java objects. |
| try-with-resources | `with` and context managers | Python cleanup is supplied by the context manager protocol, which can wrap resources beyond file-like objects and is not tied to a `Closeable` interface. |
| `Executor` or `CompletableFuture` | `asyncio`, `await`, and task groups | `asyncio` provides cooperative concurrency suited to non-blocking I/O; it does not make CPU-bound work parallel and must not be mistaken for Java thread-pool execution. |

Return to the [learning rules](learning-rules.md) before translating a familiar Java pattern into a Python design.
