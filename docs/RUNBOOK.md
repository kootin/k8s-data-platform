# Runbook

Start with `make troubleshoot`: it prints pod status, warning events, PVCs,
recent logs for every component, LocalStack health and recent DAG runs. Then
find the symptom below.

All `kubectl` commands assume:

```bash
export KUBECONFIG=~/.kube/kind-k8s-data-platform
alias kc='kubectl -n data-platform'
```

---

## Bring-up

### `make infra` fails creating the cluster
- **Docker not running**: `docker info` errors. Start Docker Desktop.
- **Port already allocated** (8080, 4566 or 5432): find the owner with
  `lsof -nP -iTCP:8080 -sTCP:LISTEN`, stop it, or change the port in
  `terraform/variables.tf` (e.g. `-var airflow_host_port=8090`).
- **Cluster already exists from an earlier run** without Terraform state:
  `kind delete cluster --name k8s-data-platform`, then `make infra`.

### `terraform apply` hangs on `wait_for_localstack`
LocalStack isn't answering on `localhost:4566`.
```bash
kc get pods -l app=localstack
kc logs deploy/localstack
curl -s localhost:4566/_localstack/health
```
Usually the image is still pulling on a slow connection; re-run `make infra`.

### Terraform says the cluster or a bucket is missing
Someone deleted it outside Terraform (or LocalStack restarted and lost its
in-memory buckets). `terraform plan` shows the drift; `make infra` recreates it.
If the whole cluster is gone: `terraform -chdir=terraform state list`, then
`terraform -chdir=terraform apply -replace=kind_cluster.this`.

---

## Pods

### Pod stuck in `Pending`
```bash
kc describe pod <pod>     # read the Events at the bottom
```
- `Insufficient memory/cpu`: give Docker Desktop more memory (6 GB+).
- `pod has unbound immediate PersistentVolumeClaims`: `kc get pvc`; kind's
  `standard` storage class should bind within seconds. `kubectl get sc` to check it exists.

### `ErrImageNeverPull` / `ImagePullBackOff` on Airflow pods
The Airflow image only exists locally; it has to be loaded into the kind node.
```bash
make image                 # build + kind load
docker exec k8s-data-platform-control-plane crictl images | grep airflow
```
If Jenkins deployed a commit tag, the image with that tag must have been loaded
by the same build.

### Scheduler in `Init:CrashLoopBackOff`
The `db-migrate` init container failed.
```bash
kc logs deploy/airflow-scheduler -c db-migrate
```
- `could not connect to server`: Postgres isn't ready, check `kc get pods -l app=postgres`.
- `password authentication failed`: the Secret changed after Postgres first
  initialized its volume. Postgres keeps the original password. Either restore it, or
  reset the data: `kc delete statefulset postgres && kc delete pvc data-postgres-0 && make deploy`
  (this deletes the warehouse; re-run the DAG to reload).

### Webserver never becomes Ready
It waits for migrations (`wait-for-migrations` init container), so fix the
scheduler first. Then `kc logs deploy/airflow-webserver`. Gunicorn takes 1–2 minutes to
start on a small laptop; the readiness probe tolerates that.

### Pod `OOMKilled`
`kc describe pod <pod> | grep -A3 'Last State'`. Raise the `limits.memory`
in `k8s/airflow-*.yaml` and `make deploy`.

---

## Pipeline

### DAG not in the UI
```bash
kc exec deploy/airflow-scheduler -c scheduler -- airflow dags list-import-errors
```
A Python error in `dags/` or `pipeline/` shows up here. Fix, then `make image deploy`.

### `extract` fails
- `429` / timeouts: the task already retries with backoff. For heavy use set an
  app token: `kc set env deploy/airflow-scheduler SOCRATA_APP_TOKEN=<token>`.
- No internet from the cluster: switch to the bundled sample with
  `kc set env deploy/airflow-scheduler NYC311_SOURCE=sample`.

### `quality_checks` fails
The run stops before anything is loaded, which is the point. The task log lists every
check with PASS/FAIL and the numbers.
- `row_count_positive`: the API had no rows for that day yet (311 data lands with a lag).
  Re-run later.
- `reconciles_with_raw`: rows were dropped in transform; look for unparseable keys in the raw file:
  `aws --endpoint-url http://localhost:4566 s3 cp s3://nyc311-raw/nyc311/dt=<day>/service_requests.json - | head`
- `created_at_in_partition`: the API filter or timezone handling changed.

Re-run a day after a fix:
```bash
kc exec deploy/airflow-scheduler -c scheduler -- airflow tasks clear nyc311_daily -s <day> -e <day> -y
```

### Backfill a date range
Loads are idempotent, so overlapping ranges are safe:
```bash
kc exec deploy/airflow-scheduler -c scheduler -- airflow dags backfill nyc311_daily -s 2026-10-01 -e 2026-10-31
```

### Check what actually landed
```sql
SELECT * FROM nyc311.load_audit ORDER BY loaded_at DESC LIMIT 10;   -- raw vs clean vs warehouse per run
SELECT created_at::date, count(*) FROM nyc311.service_requests GROUP BY 1 ORDER BY 1;
```

---

## Jenkins

### `Connect to cluster` stage fails
The cluster must exist before Jenkins starts (Jenkins joins the `kind` Docker network).
`make infra`, then `docker compose -f jenkins/docker-compose.yml up -d --force-recreate`.

### `docker: permission denied` in a build
The Jenkins container needs the Docker socket; it runs as root in the compose file. Check
`docker exec k8s-data-platform-jenkins docker ps`.

### Tests stage can't reach `ci-postgres-N`
Same network requirement: the throwaway Postgres runs on the `kind` network, so Jenkins must be on it too.

---

## Host / Linux checks

```bash
docker system df                                         # image/volume disk use
docker exec k8s-data-platform-control-plane df -h /       # disk inside the node
docker exec k8s-data-platform-control-plane crictl ps     # containers kubelet is running
kubectl top pods -n data-platform                         # needs metrics-server (not installed by default)
```

Free space: `docker image prune` (unused images), or `make down && make up` for a clean slate.
