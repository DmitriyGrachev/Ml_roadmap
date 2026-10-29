# Linux/WSL + Docker + один AWS bridge

Это runbook для самостоятельного запуска, не отчёт о выполненном deployment.
В author environment нет Docker daemon/CLI и AWS deployment не выполнялся:
**Docker build/run NOT_RUN; AWS NOT_RUN; PostgreSQL NOT_RUN**. Локальный TCP
эксперимент и эти конфигурации — разные evidence. Команды облака создают платные
ресурсы; выполняйте их только в своей учебной AWS account с заранее выбранным
лимитом бюджета. Само чтение этого runbook не запускает команды.

## Локально: Linux/WSL и контейнер

На Windows используйте WSL2/Docker Desktop либо обычный Python localhost run.
Не нужны native Windows vLLM, GPU или скачивание pretrained weights.
Из корня repo после создания author или собственного bundles output:

```bash
python -m projects.document_intelligence_lab.production_readiness.demo \
  --output /tmp/tcp-before-docker --requests 12 --concurrency 3
# Реальная существующая base image; frozen lock, CPU-only inference dependencies.
docker build -f projects/document_intelligence_lab/service/Dockerfile \
  -t document-service:local .
mkdir -p /tmp/roadmap-container-context
cp -R /tmp/tcp-before-docker/bundles/rules /tmp/roadmap-container-context/bundle
python - <<'PY'
import hashlib, json
from pathlib import Path
root = Path('/tmp/roadmap-container-context')
digest = hashlib.sha256((root/'bundle/manifest.json').read_bytes()).hexdigest()
(root/'service.json').write_text(json.dumps({
    'bundle_root': '/runtime/bundle', 'expected_manifest_sha256': digest
}), encoding='utf-8')
PY
docker build -f "$PWD/projects/document_intelligence_lab/production_readiness/Dockerfile" \
  -t roadmap-service:a /tmp/roadmap-container-context
docker run --rm -d --name roadmap-service --read-only --memory=512m --cpus=1 \
  -p 127.0.0.1:8000:8000 roadmap-service:a
curl --fail http://127.0.0.1:8000/ready
curl --fail -H 'Content-Type: application/json' \
  -d '{"text":"  TRIANGLE  "}' http://127.0.0.1:8000/predict
docker logs roadmap-service
docker stop --time 5 roadmap-service
```

Wrapper использует существующий service app factory с JSON rules saved model.
TF-IDF pickle child factory из TCP harness не переносится в internet endpoint.
Чтобы показать container A→B→A, подготовьте второй **валидный rules-json-v1** bundle
с отличающимся probe behavior, соберите `roadmap-service:b`, повторите curl и верните
immutable A image. Не меняйте model.json без пересчёта bundle/test predictions:
startup должен отвергнуть нарушение целостности. Измерения контейнера, cgroup memory
и network timings записываются новым отдельным отчетом; TCP report не их замена.

## AWS: соответствия контракта

| Локальный контракт | Один AWS вариант | Что ученик должен сохранить |
|---|---|---|
| Immutable input/manifest | Private S3 bucket + object key by source hash | bucket/key/version or checksum, schema, retention |
| Container image | ECR image **digest**, не mutable latest | source revision, image digest, bundle digest |
| Один HTTP process | ECS Fargate task в отдельной security group | task-definition revision, task ARN, health/curl outcomes |
| SQL batch job | Отдельная ECS task, запущенная вручную; затем optional EventBridge Scheduler | source offset, output manifest, retry/idempotency contract |
| Identity | execution role для ECR/logs; отдельная task role | только нужные S3 prefixes для data job, без static keys |
| stdout/stderr | CloudWatch Logs | startup/bundle identity; безопасные request aggregates |
| Monitoring | Logs/metrics + отдельный delayed-label job | thresholds, label availability/coverage, review decision |
| Rollback | Previous task definition + pinned ECR digest | before/after probe, readiness, shutdown evidence |

Ни Airflow, ни Spark, ни Kubernetes здесь не обязательны. Добавляйте scheduler,
partitioned Parquet и distributed compute, только когда SQL/одна job уже не покрывают
объём/зависимости. Fargate HTTP task ниже не читает S3: bundle встроен в image.
S3 upload демонстрирует границу pipeline artifact. Автоматический download/ingest,
metrics exporter, load balancer и production auth этим конфигом **не реализованы**.
Для production endpoint понадобятся HTTPS/auth и балансировщик; учебный ingress
ниже разрешает только собственный IPv4/32, без публичного широкого CIDR.

## Явный AWS runbook (не запускался)

Предварительно: AWS CLI настроен через SSO/short-lived credentials, Docker работает,
выбраны `AWS_REGION`, account и **существующие public subnet/VPC с internet route**.
Не создавайте NAT Gateway ради этой маленькой проверки. Подготовьте две tested
локальные image versions A/B описанным способом. Переменные задаёте своими значениями:

```bash
export AWS_REGION=eu-central-1
export ACCOUNT_ID=YOUR_ACCOUNT_ID
export SUBNET_ID=YOUR_PUBLIC_SUBNET_ID
export VPC_ID=YOUR_VPC_ID
export MY_IPV4=YOUR_CURRENT_PUBLIC_IPV4
export BUCKET=YOUR_GLOBALLY_UNIQUE_PRIVATE_BUCKET
export REPOSITORY=roadmap-document-service
export ECR_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY"
# До создания: проверьте account/region и доступный учебный бюджет.
aws sts get-caller-identity
aws ecr create-repository --repository-name "$REPOSITORY" --image-tag-mutability IMMUTABLE
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
docker tag roadmap-service:a "$ECR_URI:a"
docker push "$ECR_URI:a"
aws ecr describe-images --repository-name "$REPOSITORY" --image-ids imageTag=a
aws s3api create-bucket --bucket "$BUCKET" --region "$AWS_REGION" \
  --create-bucket-configuration LocationConstraint="$AWS_REGION"
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3 cp /absolute/path/to/your/pipeline-run/manifest.json \
  "s3://$BUCKET/pipeline/your-source-sha256/manifest.json"
aws logs create-log-group --log-group-name /roadmap/document-service
aws logs put-retention-policy --log-group-name /roadmap/document-service --retention-in-days 3
aws ecs create-cluster --cluster-name roadmap-lab
```

Создайте execution role и пустую task role с trust policy для `ecs-tasks.amazonaws.com`.
Это файл `ecs-trust.json` в **временном** каталоге:

```json
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}
```

```bash
aws iam create-role --role-name roadmapEcsExecution --assume-role-policy-document file://ecs-trust.json
aws iam attach-role-policy --role-name roadmapEcsExecution \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
aws iam create-role --role-name roadmapEcsTask --assume-role-policy-document file://ecs-trust.json
aws ec2 create-security-group --group-name roadmap-lab --description roadmap-local-learner \
  --vpc-id "$VPC_ID"
export SG_ID=THE_CREATED_SECURITY_GROUP_ID
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp \
  --port 8000 --cidr "$MY_IPV4/32"
```

Скопируйте [ecs-task.template.json](ecs-task.template.json) во временный `task-a.json`.
Замените все `REPLACE_...`: region, execution/task role ARNs из create-role,
ECR image URI **с `@sha256:...`** из describe-images. Roles могут требовать несколько
секунд распространения IAM; это не причина отключать проверки доступа.

```bash
aws ecs register-task-definition --cli-input-json file://task-a.json
# TASK_A_ARN — точный ARN:revision из предыдущего вывода.
export TASK_A_ARN=YOUR_REGISTERED_TASK_DEFINITION_ARN
aws ecs run-task --cluster roadmap-lab --launch-type FARGATE \
  --task-definition "$TASK_A_ARN" \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}"
export RUN_A_ARN=YOUR_RUNNING_TASK_ARN
aws ecs wait tasks-running --cluster roadmap-lab --tasks "$RUN_A_ARN"
aws ecs describe-tasks --cluster roadmap-lab --tasks "$RUN_A_ARN"
# Получите networkInterfaceId из attachments/details; затем public IP:
aws ec2 describe-network-interfaces --network-interface-ids YOUR_TASK_ENI_ID
curl --fail http://YOUR_TASK_PUBLIC_IP:8000/ready
curl --fail -H 'Content-Type: application/json' -d '{"text":"TRIANGLE"}' \
  http://YOUR_TASK_PUBLIC_IP:8000/predict
aws logs tail /roadmap/document-service --since 10m
```

Promotion: push immutable tag b, register `task-b.json` с новым digest, run-task B,
дождаться ready, проверить отличный probe, затем stop A. Rollback: run-task с
сохранённым TASK_A_ARN, ready + прежний probe, затем stop B. Это ручной lifecycle
двух tasks с возможной сменой IP; zero-downtime/traffic routing не заявляются.
Никогда не мутируйте tag a для имитации rollback. Save outputs locally (ARN, digest,
время, исходы, labels) и уберите credentials/account-private данные перед sharing.

## Cleanup и контроль стоимости

После каждого run сохраните все task ARNs; `--desired-count` здесь нет, потому что
ECS service не создаётся. Остановите **каждую** task, дождитесь tasks-stopped,
удалите cluster, security group после удаления ENI, ECR repository, private bucket
только с вашими учебными объектами, log group, IAM roles/policy attachments.
Повторите inventory, чтобы убедиться, что нет забытых running tasks. Не запускайте
cleanup в чужом bucket или общей cluster.

```bash
aws ecs stop-task --cluster roadmap-lab --task "$RUN_A_ARN" --reason learner-cleanup
aws ecs wait tasks-stopped --cluster roadmap-lab --tasks "$RUN_A_ARN"
# Повторить для B и restored A, если они были запущены.
aws ecs delete-cluster --cluster roadmap-lab
aws ec2 delete-security-group --group-id "$SG_ID"
aws ecr delete-repository --repository-name "$REPOSITORY" --force
aws s3 rm "s3://$BUCKET" --recursive
aws s3api delete-bucket --bucket "$BUCKET"
aws logs delete-log-group --log-group-name /roadmap/document-service
aws iam detach-role-policy --role-name roadmapEcsExecution \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
aws iam delete-role --role-name roadmapEcsExecution
aws iam delete-role --role-name roadmapEcsTask
```

Billing budget alert не является hard spending cap. Ограничьте время задачи,
retention logs, размер CPU/RAM, количество replicas и срок хранения данных.
CloudWatch logs не дают classifier quality без labels; отдельный join job и
threshold decision должны существовать до заявления о quality monitoring.

Официальные справочники для проверки команд перед самостоятельным cloud run:
[ECS task definitions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html),
[run-task CLI](https://docs.aws.amazon.com/cli/latest/reference/ecs/run-task.html),
[task execution role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html),
[S3 public access block](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html),
[ECR image push](https://docs.aws.amazon.com/AmazonECR/latest/userguide/docker-push-ecr-image.html).
