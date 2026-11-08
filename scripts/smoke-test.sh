#!/usr/bin/env bash
# End-to-end check: run the DAG for one day and confirm rows landed in Postgres.
# Usage: smoke-test.sh [YYYY-MM-DD]   (defaults to 3 days ago, so the API has data)
source "$(dirname "$0")/lib.sh"
require kubectl python3

day="${1:-$(python3 -c 'import datetime; print(datetime.date.today() - datetime.timedelta(days=3))')}"
run_id="smoke__${day}__$(date +%s)"
sched=(kubectl -n "$NAMESPACE" exec deploy/airflow-scheduler -c scheduler --)

log "triggering nyc311_daily for $day (run $run_id)"
"${sched[@]}" airflow dags unpause nyc311_daily >/dev/null
"${sched[@]}" airflow dags trigger nyc311_daily -e "${day}T00:00:00+00:00" -r "$run_id" >/dev/null

state=""
for _ in $(seq 1 90); do
  state="$("${sched[@]}" airflow dags state nyc311_daily "${day}T00:00:00+00:00" 2>/dev/null | tail -1 || true)"
  case "$state" in
    success) break ;;
    failed)
      "${sched[@]}" airflow tasks states-for-dag-run nyc311_daily "$run_id" || true
      die "DAG run failed. Run 'make troubleshoot' or open the task logs in the Airflow UI" ;;
  esac
  sleep 10
done
[[ "$state" == "success" ]] || die "DAG run did not finish in 15 minutes (last state: ${state:-unknown})"
log "DAG run succeeded"

sql="SELECT raw_rows, clean_rows, warehouse_rows FROM nyc311.load_audit WHERE report_date = '$day' ORDER BY loaded_at DESC LIMIT 1"
result="$(kc exec statefulset/postgres -- sh -c "psql -U \"\$POSTGRES_USER\" -d warehouse -At -F ' ' -c \"$sql\"")"
read -r raw clean wh <<<"$result"
log "load audit for $day: raw=$raw clean=$clean warehouse=$wh"
(( ${wh:-0} > 0 )) || die "no rows in the warehouse for $day"
log "smoke test passed"
