# Деплой и проверка отката в AWS ECS

Практикум `document-cloud-rollback` отвечает на вопрос: как доказать, что после отката запрос снова обслуживает исходная модель? Вы развернёте **один ECS service** с одной Fargate task, замените ревизию A на B и вернёте тот же ARN ревизии A. На каждом этапе отдельный процесс пошлёт одинаковый HTTP-запрос и сохранит ответ в CloudWatch. Для портфолио понадобится ваш прогон в собственном AWS-аккаунте. Статус публикации материала: **AWS NOT_RUN, Docker NOT_RUN**.

Основа — [сервис классификации](../service/README.md), [проверка bundle и жизненного цикла](../production_readiness/README.md) и [предыдущий runbook](../production_readiness/deployment.md). Здесь проверяется доставка модели. Синтетический контрольный текст различает версии и ничего не говорит о качестве на новых документах.

### 1. Подготовьте две версии до входа в AWS

Используйте Linux или WSL, Bash, Git, Python/uv с зависимостями репозитория, Docker Engine с buildx и драйвером `docker` у builder `default`, AWS CLI v2 и jq 1.6+. Выполняйте блоки по порядку из корня репозитория в **одной Bash-сессии**. Выберите собственный синтетический токен из 4–40 строчных ASCII-букв и цифр с буквой на первом месте. Впишите его и метку B в план проверки до запуска: для приведённого rules bundle ответ A будет `circle`, для B выберите `square` или `triangle`.

```bash
set -euo pipefail
umask 077
ROOT="$PWD"
LAB="$ROOT/projects/document_intelligence_lab/cloud_rollback"
PROD="$ROOT/projects/document_intelligence_lab/production_readiness"
suffix=$(uv run --frozen python -c 'import secrets; print(secrets.token_hex(3))')
STACK="mlrollback-$(date -u +%Y%m%d%H%M%S)-$suffix"
export STACK
SESSION="$ROOT/generated-reports/$STACK"
mkdir -p "$SESSION"
RUN="$SESSION/evidence"
read -rp 'Синтетический токен для проверки: ' TOKEN
read -rp 'Ожидаемая метка B (square или triangle): ' B_LABEL
uv run --frozen python -m projects.document_intelligence_lab.part_a1.demo --output "$SESSION/source"
uv run --frozen python -m projects.document_intelligence_lab.cloud_rollback.prepare \
  "$SESSION/source/rules" "$RUN" "$TOKEN" "$B_LABEL"
jq . "$RUN/expect.json"

docker buildx build --builder default --platform linux/amd64 --provenance=false --sbom=false \
  --load -f "$ROOT/projects/document_intelligence_lab/service/Dockerfile" -t document-service:local .
for key in a b; do
  docker buildx build --builder default --platform linux/amd64 --provenance=false --sbom=false \
    --load -f "$PROD/Dockerfile" -t "$STACK:$key" "$RUN/$key"
done
```

`prepare` загружает JSON rules через штатный loader, добавляет в B правило только для вашего токена, пересчитывает test predictions, метрики, контрольные суммы и снова загружает оба bundle. Файлы `expect.json`, `a/bundle` и `b/bundle` задают независимое от HTTP ожидание. Контейнеры используют существующие Dockerfile и единый путь нормализации. Сохраните ожидание и причину отката в `$RUN/defense.md` до следующего шага.

### 2. Выделите ресурсы одного запуска

Нужны короткоживущие credentials учебного аккаунта, существующая public subnet с маршрутом `0.0.0.0/0 → Internet Gateway`, включённым VPC DNS и доступным IPv4. Для первой работы ECS может понадобиться разрешение создать service-linked role. Оператору нужны права управлять ресурсами этого стека (CloudFormation, IAM, ECR, ECS, Logs, security group), `iam:PassRole` для двух создаваемых ролей и чтение VPC. До создания стека проверьте account/region, бюджет и время остановки. Fargate тарифицирует CPU и RAM, отдельно учитываются public IPv4, ECR storage, CloudWatch Logs и возможный трафик. Лимит AWS Budgets присылает уведомления. [Расчёт Fargate](https://aws.amazon.com/fargate/pricing/) · [тарифы IPv4](https://aws.amazon.com/vpc/pricing/)

```bash
export AWS_PAGER=""
read -rp 'AWS region: ' AWS_REGION
export AWS_REGION
read -rp 'ID существующей public subnet учебного аккаунта: ' SUBNET_ID
aws sts get-caller-identity --output json
VPC_ID=$(aws ec2 describe-subnets --subnet-ids "$SUBNET_ID" --query 'Subnets[0].VpcId' --output text)
aws cloudformation create-stack --stack-name "$STACK" --template-body "file://$LAB/stack.yaml" \
  --parameters "ParameterKey=VpcId,ParameterValue=$VPC_ID" --capabilities CAPABILITY_IAM \
  --output json > "$RUN/stack.json"
STACK_ID=$(jq -er .StackId "$RUN/stack.json")
aws cloudformation wait stack-create-complete --stack-name "$STACK_ID"
aws cloudformation describe-stacks --stack-name "$STACK_ID" --output json > "$RUN/resources.json"
stack_output() {
  jq -er --arg k "$1" '.Stacks[0].Outputs[] | select(.OutputKey==$k) | .OutputValue' \
    "$RUN/resources.json"
}
REPO=$(stack_output Repo)
SG=$(stack_output SecurityGroup)
EXEC_ROLE=$(stack_output ExecutionRole)
TASK_ROLE=$(stack_output TaskRole)
aws ecr get-login-password | docker login --username AWS --password-stdin "${REPO%%/*}"
```

Стек создаёт собственные ECR repository, ECS cluster, log group с хранением три дня, security group без входящих правил и две IAM-роли. Execution role нужна агенту ECS для загрузки image и отправки логов. У роли приложения нет разрешающих политик: артефакты находятся в image. Public IPv4 позволяет task устанавливать исходящие HTTPS-соединения; входящий доступ к приложению закрыт. Клиент в соседнем контейнере обращается к `127.0.0.1:8000` внутри той же task. [Сеть Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-networking.html) · [Execution role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)

### 3. Зарегистрируйте A и B по digest

```bash
for key in a b; do
  docker tag "$STACK:$key" "$REPO:$key"
  docker push "$REPO:$key"
  digest=$(aws ecr describe-images --repository-name "$STACK" --image-ids "imageTag=$key" \
    --query 'imageDetails[0].imageDigest' --output text)
  [[ "$digest" =~ ^sha256:[a-f0-9]{64}$ ]]
  jq --arg stack "$STACK" --arg image "$REPO@$digest" --arg region "$AWS_REGION" \
    --arg exec "$EXEC_ROLE" --arg role "$TASK_ROLE" --arg token "$TOKEN" \
    --rawfile code "$LAB/probe.py" -f "$LAB/task.jq" "$PROD/ecs-task.template.json" \
    > "$RUN/task-input-$key.json"
  aws ecs register-task-definition --cli-input-json "file://$RUN/task-input-$key.json" \
    --output json > "$RUN/td-$key.json"
done
docker logout "${REPO%%/*}"
A=$(jq -er '.taskDefinition.taskDefinitionArn' "$RUN/td-a.json")
B=$(jq -er '.taskDefinition.taskDefinitionArn' "$RUN/td-b.json")
```

Регистрация сохраняет точный ARN каждой ревизии. В контейнере сервиса задан health check на `/ready`: ECS отслеживает проверку из task definition. Клиент `probe` запускается после `HEALTHY`, отправляет `POST /predict?probe_id=<uuid>`, печатает ответ и завершает работу. Тело содержит только выбранный синтетический токен. Uvicorn пишет обычную строку access log с тем же UUID. [Проверки ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/healthcheck.html) · [Имена потоков awslogs](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html)

### 4. Выполните смену версии и откат

Обработчик ниже при выходе из этой Bash-сессии пытается уменьшить число задач до нуля. Он ограничивает время работы при прерванном прогоне. Полное удаление ресурсов описано в шаге 5; при аварийном закрытии машины воспользуйтесь им из новой сессии.

```bash
guard_cluster=$(stack_output ClusterArn)
guard_region=$AWS_REGION
service_may_exist=1
on_exit() {
  local rc=$?
  if [[ "$service_may_exist" == 1 ]]; then
    aws ecs update-service --region "$guard_region" --cluster "$guard_cluster" \
      --service classifier --desired-count 0 --output json >/dev/null || \
      echo 'Проверьте состояние сервиса и выполните очистку вручную.' >&2
    echo "Каталог для очистки: $RUN" >&2
  fi
  return "$rc"
}
trap on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
aws ecs create-service --cluster "$STACK" --service-name classifier --desired-count 1 \
  --launch-type FARGATE --platform-version 1.4.0 --task-definition "$A" \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG],assignPublicIp=ENABLED}" \
  --deployment-configuration 'maximumPercent=100,minimumHealthyPercent=0,deploymentCircuitBreaker={enable=true,rollback=true}' \
  --output json > "$RUN/create-service.json"
aws ecs wait services-stable --cluster "$STACK" --services classifier
uv run --frozen python "$LAB/capture.py" "$RUN" A

aws ecs update-service --cluster "$STACK" --service classifier --task-definition "$B" \
  --query service.taskDefinition --output text
aws ecs wait services-stable --cluster "$STACK" --services classifier
uv run --frozen python "$LAB/capture.py" "$RUN" B

aws ecs update-service --cluster "$STACK" --service classifier --task-definition "$A" \
  --query service.taskDefinition --output text
aws ecs wait services-stable --cluster "$STACK" --services classifier
uv run --frozen python "$LAB/capture.py" "$RUN" restored
```

При `maximumPercent=100`, `minimumHealthyPercent=0` и одной реплике существует окно недоступности. Этот опыт показывает работу одного приватного сервиса; доступность внешнего трафика потребовала бы отдельного теста с маршрутизацией. Если waiter истёк или контрольная метка неверна, сохраните последние события (`aws ecs describe-services --cluster "$STACK" --services classifier --query 'services[0].events[:5]'`), исследуйте логи и перейдите к очистке. Автооткат ECS при неудачном deployment возможен; учёт B требует фактического ответа B. [AWS CLI update-service](https://docs.aws.amazon.com/cli/latest/reference/ecs/update-service.html)

| Что сравнить на защите | Исходная A | После смены на B | После отката |
|---|---|---|---|
| Task definition и image digest | Сохранить оба | Другая ревизия и другой digest | Точные значения A |
| Выполняющаяся task | Записать ID | Новый ID | Ещё один новый ID |
| HTTP-ответ на один токен | Все четыре поля из `expect.json.a` | Все поля из `expect.json.b`, метка изменилась | Полное совпадение с первым ответом A |
| Подтверждение запроса | UUID из probe + HTTP 200 в access log | Новый UUID в обоих потоках B | Новый UUID в обоих потоках восстановленной A |

### 5. Удалите ресурсы и проверьте расходы

После каждой попытки, в том числе при ошибке, откройте тот же каталог запуска. Стек принадлежит только этому практикуму; при его удалении будут уничтожены его ECR-образы и CloudWatch logs. Сохраните нужные фрагменты заранее. Следующие команды читают точный Stack ID и ARN зарегистрированных ревизий из файлов **текущего запуска**. Если терминал закрыт, снова задайте `RUN` абсолютным путём к каталогу evidence и восстановите тот же AWS profile. Удаляйте только созданный вами стек.

```bash
STACK_ID=$(jq -er .StackId "$RUN/stack.json")
export AWS_REGION=$(cut -d: -f4 <<< "$STACK_ID")
STACK=$(cut -d/ -f2 <<< "$STACK_ID")
export STACK
[[ "$STACK" =~ ^mlrollback-[0-9]{14}-[a-f0-9]{6}$ ]]
[[ "$(aws sts get-caller-identity --query Account --output text)" == "$(cut -d: -f5 <<< "$STACK_ID")" ]]
# После создания сервиса выполните блок до конца. Если сервис ещё не создавался,
# начните с цикла deregister ниже. При повторной очистке пропускайте уже удалённое.
aws ecs update-service --cluster "$STACK" --service classifier --desired-count 0 \
  --query service.desiredCount --output text
aws ecs wait services-stable --cluster "$STACK" --services classifier
aws ecs delete-service --cluster "$STACK" --service classifier --query service.status --output text
aws ecs wait services-inactive --cluster "$STACK" --services classifier
service_may_exist=0
trap - EXIT INT TERM
aws ecs list-tasks --cluster "$STACK" --desired-status RUNNING --output json > "$RUN/tasks-after.json"
jq -e '.taskArns == []' "$RUN/tasks-after.json"

for key in a b; do
  file="$RUN/td-$key.json"
  if [[ -s "$file" ]]; then
    td=$(jq -er '.taskDefinition.taskDefinitionArn' "$file")
    [[ "$td" == *":task-definition/$STACK:"* ]]
    aws ecs deregister-task-definition --task-definition "$td" --query taskDefinition.status --output text
    aws ecs delete-task-definitions --task-definitions "$td" --query failures --output json
  fi
done
aws cloudformation delete-stack --stack-name "$STACK_ID"
aws cloudformation wait stack-delete-complete --stack-name "$STACK_ID"
aws cloudformation describe-stacks --stack-name "$STACK_ID" --output json > "$RUN/deleted.json"
jq -e '.Stacks[0].StackStatus == "DELETE_COMPLETE"' "$RUN/deleted.json"
```

Если создание стека завершилось ошибкой до регистрации tasks, используйте полученный `StackId` для проверки событий и удаления стека. При `DELETE_FAILED` прочтите `aws cloudformation describe-stack-events --stack-name "$STACK_ID"`, дождитесь освобождения task ENI и повторите удаление. Если файл регистрации потерян после успешного ответа AWS, найдите свои ревизии через `aws ecs list-task-definitions --family-prefix "$STACK"` и сверьте **точное** имя семейства перед снятием регистрации. Проверьте затраты за нужную дату и регион в Billing после обновления данных. Для оценки вычислений умножьте суммарное оплачиваемое время задач на ставки за 0.25 vCPU и 0.5 GiB; добавьте IPv4, объём и срок хранения образов и логов. Запишите регион, допущения и результат в `defense.md`.

### Что сдать

Каталог `generated-reports/<имя запуска>/evidence` остаётся локальным. В нём находятся исходные bundle, ожидания, task definitions, сырые ответы AWS по этапам, связка двух потоков CloudWatch и подтверждение удаления стека. До публикации замените account ID, ARNs, имена ресурсов и другие внутренние идентификаторы в **копии** отчёта. Для локальной проверки нужны оригиналы. В `defense.md` запишите ожидаемую и наблюдавшуюся метки, объясните, какие два независимых источника связывают ответ с задачей, почему восстановился исходный образ и как вы подтвердили остановку расходов.

```bash
export ROADMAP_CLOUD_ROLLBACK_EVIDENCE="$RUN"
uv run --frozen python -m pytest -p roadmap_tools.strict_check "$LAB/test_submission.py" -q
```

Проверка читает сохранённые данные без обращения к AWS. Авторские и синтетические тесты подтверждают только механику проверки. Если AWS недоступен, выполните локальную подготовку и запишите `AWS NOT_RUN`. Для зачёта облачного этапа покажите собственные артефакты; проверяющий может попросить повторить запрос с новым контрольным токеном.
