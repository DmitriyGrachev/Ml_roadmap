# Сравнение roadmap с вакансиями ML / AI Engineer

Дата: **29 октября 2026 по Бухаресту**; поиск и чтение страниц начались
28 октября UTC. Проверена исходная ветка `codex/ai-ml-wave1` на коммите
`934b34bcaab5c0c241dfa820d807a9bb61e166c6`, до изменений этой ветки.

Это небольшая целевая выборка для выбора учебной практики, а не статистика всего
рынка. Страница с кнопкой/формой отклика подтверждает доступность публикации,
но не подтверждает бюджет работодателя, результат найма или право работать из
Румынии. Отклики не отправлялись. Название Junior само по себе не определяет
требуемый опыт; обязанности и nice-to-have отделены от входных требований.

## Что действительно опубликовано

| Вакансия и источник | Уровень и география | Что важно для обучения | Статус при проверке |
|---|---|---|---|
| [PPC Romania — Junior ML Engineer](https://www.hipo.ro/locuri-de-munca/locuri_de_munca/271804) | Hipo указывает 0–1 год, Бухарест | Python, NumPy/Pandas/sklearn, основы ML и учебные/проектные результаты, Git и чистый код. AWS, Spark/Airflow/EMR перечислены также в будущих обязанностях: это не требование заранее владеть всем стеком. | Доступно объявление и Apply на Hipo. [Страница работодателя](https://ppc.jobful.io/company/ppc-energy/jobs/junior-machine-learning-engineer-3) отдаёт оболочку; форму там подтвердить не удалось. On-site в метаданных и hybrid в тексте расходятся. |
| [Showpad — AI Engineer](https://job-boards.greenhouse.io/showpad/jobs/8264241) | Бухарест, hybrid 2 дня; число лет не задано, работа под руководством senior; не объявлена Junior | Python, практическая работа с AI/LLM, один cloud. RAG, поиск и GenAI evaluation находятся в nice-to-have. | На ATS работодателя доступны описание и форма отклика. |
| [Provectus — Junior AI/ML Engineer, GenAI/AWS](https://jobs.lever.co/provectus/ce930027-43a2-4b4c-af03-ea3edb8f7581) | 2+ года software **или** ML engineering; remote в перечисленных странах, Румыния не указана | Прямой мост из backend: Python/TypeScript, RAG, AWS, API, containers/CI, оценка и мониторинг. Spark/Airflow/Kafka — дополнительные плюсы. | Основная Lever-страница и [форма](https://jobs.lever.co/provectus/ce930027-43a2-4b4c-af03-ea3edb8f7581/apply) доступны; стороннее зеркало сообщало об удалении. Приоритет отдан наблюдаемому первичному источнику, доступность из Румынии не установлена. |
| [Rangein — Junior ML/AI Engineer](https://djinni.co/jobs/854330-junior-ml-ai-engineer/) | 1–2 года релевантной коммерческой работы; worldwide, отдельно указан Ukrainian Native | Python, Pandas/NumPy/sklearn, preprocessing/статистика, оценка, REST/Git/tests; практический опыт хотя бы в одном из ML, NLP или LLM-приложений. Конкретные RAG-библиотеки не все обязательны. | Объявление от 20 октября, форма Apply доступна, нет Offline. Географическая доступность не отменяет языковое требование. |
| [Artellence — Strong junior MLE](https://jobs.dou.ua/companies/artellence/vacancies/377791/) | DOU: 2+ года DS/MLE, математическое образование; [Djinni](https://djinni.co/jobs/842742-strong-junior-machine-learning-engineer/) указывает 1+, Ukraine/Ukrainian C2 | NLP и tabular, feature engineering, Python/DL, SQL/NoSQL, production-код, Git/Docker. Airflow — плюс. | Публикация DOU от 26 октября и доступная форма Djinni. Расхождение стажа не сглажено; это не позиция для полного нуля. |
| [Sombra — Middle ML Engineer](https://sombrainc.com/careers/middle-senior-ml-engineer-data-science) | Middle, remote Colombia/Ukraine; Румыния не подтверждена | Классические модели, boosting, leakage/time split, метрики, Python/PySpark, SQL/window functions, data platform, Docker/CI/orchestration. | Форма Send CV на сайте компании доступна. |
| [Qualysoft — AI Engineer, Banking](https://jobs.lever.co/qualysoft/26f03a37-4e88-4b0e-9072-33121b0e8235) | Бухарест/remote, минимум 3 года именно AI engineering | Python/sklearn, Java/SQL, LLM/RAG/MCP, API, подготовка данных, тесты и мониторинг. Хорошая иллюстрация пользы backend, но не стартовый стандарт. | Описание и [форма](https://jobs.lever.co/qualysoft/26f03a37-4e88-4b0e-9072-33121b0e8235/apply) доступны. |
| [Finom — Senior ML Engineer](https://jobs.eu.lever.co/pnlfin/c57b2869-8d1b-4006-a414-7d694b46fe53) | Romania remote, 5+ лет production ML | Classification/regression, Python/SQL, API/cloud, мониторинг, champion/challenger и A/B. Graph/foundation models — плюс. | Форма работодателя доступна. Использована как ориентир последующего роста, не критерий Junior. |
| [AMS Accelerate IT — ML Engineer](https://amsaccelerateit.recruitee.com/o/machine-learning-engineer) | Recruiter ATS, конечный клиент не назван; hybrid Bucharest/Brasov/Iasi; опытный platform/full-stack профиль | Python API, async, GCP/data pipelines, Docker/CI/IaC, оркестрация; также React/TypeScript. Эти требования описывают конкретную смешанную роль. | Форма отклика доступна. Не превращаем весь стек этой вакансии в обязательный курс. |

В основную выборку не включены объявления с Offline/закрытой формой и страницы
«на будущие проекты». Например, Insoftex прямо описывает senior bench, а не
подтверждённую немедленную вакансию; старое объявление LetsData помечено Offline.

## Что это означает для исходного проекта

Следующие выводы — интерпретация выборки и аудит кода, а не обещание работодателей.

| Компетенция | Что уже было в исходной ветке | Чего не хватало как доказательства навыка | Изменение этой ветки |
|---|---|---|---|
| Python и backend | 11 уроков Python, FastAPI, typing, тесты, async, SQL/SQLAlchemy | Подробного жизненного цикла async-задач, установки своего wheel вне checkout, настоящей миграции заполненной схемы | `python-async-lifecycle`, `python-package-delivery`, `backend-schema-migrations` |
| Моделирование и оценка | Splits, leakage, sklearn pipelines, метрики, calibration, статистика и CI уже представлены | Самостоятельных градиентов, геометрии регуляризации, механики дерева/boosting и повторного полного обучения | Четыре новых math/stability упражнения |
| Работа с реальными данными | Детерминированные учебные данные и локальные author demos | Независимого внешнего tabular проекта с происхождением данных, закрытым holdout и воспроизводимыми артефактами | `ml-external-tabular` |
| NLP и pretrained модели | HF/PyTorch механика, реальные локальные интерфейсы и Document Intelligence | Обязательного честного TF-IDF/frozen/adapted сравнения на внешнем корпусе | `document-external-model-study`; random encoder не засчитывается |
| RAG/AI-приложения | Chunking, hybrid retrieval, citations, MiniLM CLS smoke и отдельный Ollama smoke | Совместного dense+generator пути, masked mean pooling, отдельных retrieval/answer метрик на heldout и негативных случаях | `rag-end-to-end-evaluation` |
| Эксплуатация | API, сохранённый sklearn bundle, локальные registry/rollback примеры | Конкурентных TCP-запросов, наблюдаемого timeout/restart/rollback, отчёта latency/failure | `production-service-lifecycle` |
| Данные и cloud | SQL, качество данных и delivery-теория | Повторяемого incremental/idempotent pipeline и понятного переноса в один cloud | `ml-data-pipeline` и cloud bridge |
| Самостоятельность | Много starter-контрактов, строгий check и ручной progress | Единого маршрута и обязательных внешних артефактов; старая template-проверка могла ругаться на решённую задачу | Треки, рубрики и отдельный maintainer-режим |

## Разумная цель перехода

Опыт Java/Spring полезен для HTTP, SQL, контрактов, тестов, CI, диагностики и работы
с требованиями. Он не заменяет умение объяснить, почему разбиение корректно,
какие признаки доступны в момент предсказания и насколько устойчив выигрыш модели.
Самый ценный результат курса — два самостоятельно защищённых проекта и рабочая
цепочка данных/обучения/доставки, а не количество просмотренных README.

Для ML Engineer приоритетны Python, данные, валидация, классические модели,
математическая база и эксплуатация. Для Applied AI Engineer дополнительно важны
LLM/RAG, ограничения контекста, оценка ответов и интеграционные сбои. Специализации
в forecasting, CV, recommendations, Spark/Databricks или Kubernetes выбираются
под роль. Достаточно начать с одного облака и объяснять контракт каждого сервиса;
курс не требует платного развёртывания для прохождения базовых упражнений.

Документация и технические проверки могут подготовить к самостоятельной работе.
Они не предоставляют коммерческий стаж, языковой уровень, математический диплом
или разрешение на работу. Эти ограничения следует проверять отдельно для каждой
вакансии. Публикации меняются: перед откликом повторно открыть исходную страницу.

Следующий шаг: [текущая учебная карта](learning-map.md) и
[критерии готовности и защиты](readiness-assessment.md).
