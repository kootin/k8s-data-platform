CREATE SCHEMA IF NOT EXISTS nyc311;

CREATE TABLE IF NOT EXISTS nyc311.service_requests (
  unique_key      bigint PRIMARY KEY,
  created_at      timestamp NOT NULL,
  closed_at       timestamp,
  agency          text,
  complaint_type  text NOT NULL,
  descriptor      text,
  status          text,
  borough         text,
  incident_zip    char(5),
  latitude        double precision,
  longitude       double precision,
  hours_to_close  numeric(10, 2),
  loaded_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS service_requests_created_at_idx
  ON nyc311.service_requests (created_at);

CREATE TABLE IF NOT EXISTS nyc311.daily_borough_summary (
  report_date            date NOT NULL,
  borough                text NOT NULL,
  complaint_type         text NOT NULL,
  requests               integer NOT NULL,
  closed_requests        integer NOT NULL,
  median_hours_to_close  double precision,
  PRIMARY KEY (report_date, borough, complaint_type)
);

CREATE TABLE IF NOT EXISTS nyc311.load_audit (
  id              bigserial PRIMARY KEY,
  report_date     date NOT NULL,
  raw_rows        integer NOT NULL,
  clean_rows      integer NOT NULL,
  warehouse_rows  integer NOT NULL,
  loaded_at       timestamptz NOT NULL DEFAULT now()
);
