FROM apache/airflow:2.9.2-python3.12

USER root
RUN apt-get update \
 && apt-get install --no-install-recommends -y build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

USER airflow
ENV PYTHONPATH=/opt/airflow:/opt/airflow/shared/python/djr_core

COPY infra/docker/requirements-airflow.txt /requirements-airflow.txt
RUN pip install --no-cache-dir -r /requirements-airflow.txt
