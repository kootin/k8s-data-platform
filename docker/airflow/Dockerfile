# Airflow image with the pipeline and DAG baked in. Built from the repo root:
#   docker build -f docker/airflow/Dockerfile -t k8s-data-platform/airflow:local .
FROM apache/airflow:2.10.3-python3.11

# pandas, pyarrow, boto3, psycopg2 and requests already ship with this image
# (via the Amazon and Postgres providers); pin anything extra here.
COPY --chown=airflow:root requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=airflow:root pipeline /opt/airflow/pipeline
COPY --chown=airflow:root dags /opt/airflow/dags

ENV PYTHONPATH=/opt/airflow
