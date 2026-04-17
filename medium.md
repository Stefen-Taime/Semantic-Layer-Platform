# How I Rebuilt Airbnb's Minerva with Open Source — and What It Taught Me About Metrics That Actually Ship

*A storytelling walkthrough of MetricForge NYC: a self-hosted semantic layer powered by MinIO, Spark, Hive, Trino, Druid, Airflow, FastAPI, Streamlit — and a lot of humility.*

---

## The question that started everything

A few months ago, a product manager asked me a question that sounded innocent enough:

> "What was our revenue yesterday?"

In a healthy organisation, that takes thirty seconds. In most organisations, it takes four people, two dashboards, a Slack thread, and a mild existential crisis. Three of those four people will return different numbers. One of them will be right — but nobody will know which one.

This is the problem Airbnb solved internally with **Minerva**, their famous metrics platform. Minerva is the single source of truth: every chart, every experiment, every executive report starts from the same governed definitions. When Airbnb says "bookings yesterday," the number is the same in the CFO's slide, the growth team's notebook, and the ML model training last night.

I wanted the same thing. But I am not Airbnb. I do not have a platform team of twenty-five engineers. I do not have Presto clusters sized for a small country. I do have a laptop, a credit card for a small GCP VM, and an unhealthy amount of curiosity.

So I decided to rebuild Minerva. Not the real Minerva — the *spirit* of Minerva. Governed metrics, one definition, multiple engines, served through an API, visualised in a modern UI. Entirely on open source. I called it **MetricForge NYC**.

This is the story of how it came together, what broke (a lot), and what I learned about building a "semantic layer" when you are the only person on the team.

---

## Why a semantic layer, anyway?

If you've been in analytics for more than a year, you've seen this movie.

An analyst writes a SQL query to compute *active users*. Another analyst writes the same query slightly differently. Finance has a third version. The product team has a fourth. A year later, four dashboards exist, all labelled "Active Users," and nobody trusts any of them.

The semantic layer is the idea that **metric definitions should live in one place**, as versioned, reviewed code — not in the scroll history of seven different Tableau workbooks.

You define, once:

> `gross_revenue = SUM(total_amount) WHERE is_valid_trip = true`

…in a YAML file, in a Git repo, with a reviewer, an owner, a description. Every consumer — BI tools, APIs, ML pipelines, LLM agents, the CEO's email — pulls that definition. The *how* (SQL, Druid, Spark) becomes an implementation detail. The *what* is governed.

That is what Minerva is. And that is what I wanted to rebuild with open-source bricks anyone can run on a $200/month VM.

---

## The stack, or: choosing my weapons

I spent an embarrassing amount of time staring at the blank architecture diagram before I wrote a single line of code. Every choice is a trade-off. Here is what I ended up with, and why.

### Storage: **MinIO**

An S3-compatible object store I can run locally. Same API as AWS, zero vendor lock-in. Raw files land here. Parquet files land here. Everything downstream just speaks S3A.

### Compute: **Apache Spark**

Because I needed to write real data engineering pipelines: read raw CSV, partition, clean, build facts and dimensions, materialise pre-aggregates. Spark is the workhorse. It is verbose. It works.

### Catalog: **Hive Metastore**

Yes, in 2026. Because the Metastore is the lingua franca of open-source data: Spark speaks it, Trino speaks it, Flink speaks it. One catalog, three engines pointing at the same tables in MinIO. The *magic* of the lakehouse idea is exactly that shared catalog.

### Interactive SQL: **Trino**

For flexibility. When an analyst needs ad-hoc SQL, they hit Trino. Sub-second queries against the certified Hive tables sitting in MinIO.

### OLAP: **Apache Druid**

For speed. When a dashboard needs the top 10 zones by revenue over three months, and needs it in 200ms, that is not a Trino job. That is a Druid job. Druid ingests pre-aggregated JSON files Spark produces for exactly this purpose.

### Orchestration: **Apache Airflow**

Because somebody has to wake up at 3 AM, rebuild the certified tables, refresh Druid, re-validate the semantic layer. That somebody is Airflow, not me.

### API: **FastAPI**

Because the semantic layer needs a contract. `POST /query` accepts a metric name, dimensions, filters, an engine hint — and returns clean JSON. Everything downstream talks to the API, never directly to the engines.

### UI: **Streamlit + Plotly**

Because I needed a dashboard, and I didn't want to spend three weeks writing React. Dark theme, glass cards, Plotly charts that auto-select themselves based on the query shape. Good enough to demo, fast enough to iterate.

All of it containerised with **Docker Compose** and running on a single **GCP VM** (`e2-standard-8`, 100 GB disk). The entire stack comes up with one command.

---

## Act I: The lakehouse wakes up

I started with what sounded easy. Load the NYC Yellow Taxi dataset into MinIO. Have Spark read it. Have Spark write a clean, partitioned fact table. Have Trino query it.

Easy. Three days, right?

**Four days in**, Spark was running happily in one container, Trino in another, Hive Metastore in a third, and none of them agreed on what a table was. Spark would write a Parquet file to `s3a://metricforge/certified/fct_taxi_trips/`, register it as `metricforge.fct_taxi_trips` — and Trino would look at the same metastore and answer "Table does not exist."

The culprit? The Hive Metastore jars shipped in the official `apache/hive:4.0.0` image did not include `hadoop-aws` or the AWS SDK bundle. So when Trino asked the Metastore "where does this table live?", the Metastore itself could not resolve `s3a://` URIs.

Fix: a two-line bash entrypoint that copies the jars from `/opt/hadoop/share/hadoop/tools/lib` into `/opt/hive/lib` before starting the service. Obvious in hindsight. Infuriating in the moment.

**Lesson #1**: In a lakehouse, the catalog is not a separate concern. Every engine that reads from object storage needs the object-store SDK on *its own* classpath, including the catalog itself.

Once that was fixed, the entire storage/compute layer came alive. One Parquet table, written by Spark, readable by Trino, readable by Spark again from another container. The lakehouse was real.

![The MinIO warehouse bucket — raw, curated, and certified tables living in a single object store, readable by every engine in the stack.](img/minio-warehouse.png)

---

## Act II: The partition that broke production (twice)

The raw taxi dataset is a few GB of CSV with hundreds of millions of rows spread over several years. The first version of my certified fact table had no partitioning.

First query through Trino: 47 seconds. Unacceptable.
First query through Druid: well, there was no Druid yet.
First glance at the Spark UI: 280 tasks, all reading full files. Fine for a demo, catastrophic at scale.

I added partitioning by `pickup_year` and `pickup_month`. Rewrote the certified job. Ran the pipeline. Trino queries dropped to under a second. Victory.

![Trino query history: the same certified fact table answering joins and aggregates in hundreds of milliseconds once partitioning was right.](img/trino-query-history.png)

Three hours later, I ran the pipeline *again* with new data, and discovered that Spark's partition overwrite semantics were deleting the old partitions silently. Half my history was gone. I had two options: cry, or read the Spark documentation properly.

I read the documentation. `spark.sql.sources.partitionOverwriteMode=dynamic`. Four words. Every pipeline I have ever seen forgot them at least once.

**Lesson #2**: Partitioning is not a performance optimisation you bolt on at the end. It is a data model choice. Make it early. Make it once. Test overwrites on disposable data before you trust them.

---

## Act III: The semantic layer, or: YAML as a contract

With the lakehouse stable, I could finally do the fun part.

I wrote a YAML file. Three sections: `dimensions`, `metrics`, `joins`. Each dimension points to a physical column. Each metric points to a measure, an aggregation, an allowed list of dimensions, and (optionally) a filter predicate. Each join describes how to link a dimension to the fact.

Here is the entire definition for `gross_revenue`:

```yaml
- name: gross_revenue
  label: Gross Revenue
  type: sum
  measure: total_amount
  source: metricforge.fct_taxi_trips
  time_dimension: pickup_datetime
  allowed_dimensions: [pickup_borough, pickup_zone, payment_type]
  filters:
    - field: is_valid_trip
      operator: "="
      value: true
```

That is the entire contract. Nine fields. From those nine fields, the platform can generate:

- A Spark SQL query
- A Trino SQL query
- A Druid SQL query against a pre-aggregated datasource

…with consistent filters, consistent joins, consistent typing, consistent units. Every consumer — dashboards, APIs, notebooks, AI agents — gets the same number.

I wrote a small Python module called `metrics_engine` that loads this YAML, validates it (cycle detection on ratio metrics, dimension allowlists, identifier safety), and emits SQL per engine. The API wraps it. The dashboard wraps the API. It is turtles all the way down, but every turtle is governed.

**Lesson #3**: A semantic layer is not a tool. It is a *discipline*. The YAML file is less important than the code review, the ownership field, and the rule that nobody — nobody — writes a new metric without adding it to the layer.

---

## Act IV: Serving the metrics (three engines, one API)

Here is where things got interesting.

A semantic layer that generates SQL for one engine is a CLI tool. A semantic layer that generates SQL for *three* engines, depending on the query shape, is a **platform**.

The routing logic is simple in principle:

- If the query is an **ad-hoc slice** with filters and joins → **Trino** (flexibility)
- If the query is a **recurring dashboard aggregate** → **Druid** (speed, pre-computed)
- If the query is an **offline backfill or ML feature** → **Spark** (scale)

Every metric in the YAML declares where it can be served. The API picks the right engine automatically, or obeys a caller override. The dashboard lets the analyst flip between engines in a radio button and *see* the same number, computed from the same definition, arriving from a different back-end.

![The FastAPI contract: a single `POST /query` endpoint is the only door into the semantic layer. Everything downstream — dashboards, notebooks, LLM agents — goes through it.](img/fastapi-swagger.png)

![`GET /metrics` returns the governed catalog with owner, description, allowed dimensions, and serving engine for each metric. The contract is discoverable.](img/api-metrics-response.png)

That moment — seeing identical numbers appear in 800ms on Druid and 2.4s on Trino, from the same metric key — is when I understood why Airbnb built Minerva. It is not a query engine. It is a **trust engine**.

![The same `/query` payload, with `limit` and `order_by`, returning an average-tip ranking in Trino — SQL is generated from the YAML, not written by hand.](img/api-query-average-tip.png)

---

## Act V: The Druid detour

Druid is fast. Druid is also opinionated.

To make a metric fast on Druid, you do not just point Druid at your fact table. You pre-aggregate. You roll up daily. You roll up by zone. You write the rolled-up data as newline-delimited JSON files. You write an ingestion spec. You submit it to the Druid Overlord. The Overlord runs a task. The task writes segments. The segments are served by the Historical. The Broker routes queries. The Router fronts everything.

That is seven moving parts for one metric.

I wrote a Spark job — `04_build_druid_aggregates.py` — that reads the certified fact table, computes two rollups (daily metrics, zone metrics), and writes JSON to a volume mounted in both Airflow and Druid. An Airflow DAG runs the Spark job, then POSTs the ingestion specs to the Druid Overlord.

![Two Druid datasources — `metricforge_taxi_daily_metrics` and `metricforge_taxi_zone_metrics` — with their pre-aggregated dimensions and measures ready to serve queries in milliseconds.](img/druid-console.png)

First run: permission denied. The shared volume was owned by Druid's UID (1000). Airflow runs as UID 50000. Neither could see the other's files.

Fix: one `chmod 777` on the shared input directory, followed by a quiet promise to do it properly with a proper entrypoint later.

Second run: Druid ingestion worked. The Overlord accepted the specs. Tasks went SUCCESS. The Historical loaded segments. The Broker answered queries.

Third run — the live validation — I POSTed to the API:

```yaml
metric: daily_zone_revenue
group_by: [pickup_zone]
engine: druid
limit: 10
order_by: [{column: daily_zone_revenue, direction: desc}]
```

200 OK. Result in 160 milliseconds.

> JFK Airport: $20.6M
> LaGuardia Airport: $10.8M
> Midtown Center: $7.3M
> Upper East Side South: $6.4M
> …

I ran the same payload against Trino. Identical numbers, 2.3 seconds.

![The live `/query` endpoint hitting Druid: top boroughs by daily completed trips, answered in ~200 ms with SQL generated straight from the semantic layer.](img/api-query-druid-top-boroughs.png)

**Lesson #4**: Pre-aggregation is not an optimisation. It is a *product decision*. You are trading freshness, flexibility, and storage for speed. The semantic layer is the right place to make that trade explicitly, metric by metric.

---

## Act VI: The UI, or: making metrics feel inevitable

The original dashboard I shipped was functional and ugly. Streamlit default theme, grey backgrounds, form fields stacked vertically, a table dump at the bottom. It worked. Nobody would want to use it.

I rewrote it. Dark gradient background. Glassmorphic cards with blurred backdrops. A sidebar for configuration so the canvas stays focused on insight. Plotly charts with a custom palette (violet → cyan gradient, the MetricForge accent). The chart type auto-selects itself from the query shape:

- One categorical dimension → ranked horizontal bar chart
- Two categorical dimensions → heatmap
- Time grain selected → line chart with optional colour break-down
- No group-by → big-number indicator

Engine pills colour-coded by backend (Druid cyan, Trino amber, Spark orange) so the analyst always knows which brain computed the answer. KPI tiles on top: Total, Mean, Max, Min. A one-click CSV download below the chart. The generated SQL visible side-by-side with the data, because analysts always, *always* want to see the SQL.

It is still a single Python file. It is under 700 lines. It runs on a single Streamlit container. And it feels like a product.

![The governed catalog inside the dashboard: ten metrics, their owners, descriptions, allowed dimensions. Not a spreadsheet. A contract.](img/dashboard-catalog.png)

**Lesson #5**: Governance without usability is a private members' club. If the dashboard is ugly, analysts will export the data and build their own charts in Excel, and you are back at square one.

---

## What I would do differently

If I were to start again tomorrow, three things would change.

1. **Start with the semantic layer, not the lakehouse.** I spent my first two weeks on Spark, Hive, partitioning. But a lakehouse without a semantic layer is just storage with extra steps. The YAML file should have been written on day one, even against a mock backend.

2. **Pick one engine to ship, add the others later.** I wanted Spark + Trino + Druid from the start because it was intellectually interesting. In hindsight, shipping with Trino alone, getting real users, then adding Druid when latency actually hurt, would have been faster and saner.

3. **Write the dashboard last.** I rewrote mine three times because I kept learning what the user actually wanted to see. UI is the cheapest thing to change — but only *after* the platform underneath is stable.

---

## Does it actually work?

On a single GCP VM (`e2-standard-8`, 8 vCPU, 32 GB RAM), the full stack runs 18 containers: MinIO, two Postgres instances (Hive metadata, Airflow), Hive Metastore, Trino, ZooKeeper, five Druid services, three Airflow services, the FastAPI service, and the Streamlit dashboard.

Cold boot: ~90 seconds.
One-command deploy: `docker compose -f docker/compose.demo.yml up -d --build`.
End-to-end pipeline for a month of taxi data: 4 minutes on Spark, 30 seconds on Druid ingestion.
Dashboard query against Druid: 150-300 ms.
Dashboard query against Trino: 1-3 seconds.
Monthly cost: less than a good dinner in Manhattan.

![Airflow orchestrates the whole thing: ingest → build certified tables → rebuild the metric catalog → refresh Druid → validate the semantic layer. Every run is auditable.](img/airflow-dags.png)

![The VM itself during a full pipeline run — modest CPU, disciplined disk throughput. Minerva-like discipline on a single `e2-standard-8`.](img/gcp-vm-monitoring.png)

Ten governed metrics. Seven dimensions. Two Druid datasources. One semantic layer. One API. One number per question.

---

## The real lesson

When I finished, I sat back and realised the *technology* was never the point. I could have written the whole thing with Postgres, Metabase, and a cron job, and it would have delivered 80% of the value. The point was the **discipline**:

- Every metric has a definition.
- Every definition lives in Git.
- Every definition has an owner.
- Every consumer — human or machine — reads the same definition.
- Nobody, ever, defines a new metric in a BI tool.

That is what Minerva is. That is what every great data platform becomes, eventually, whether it is called Minerva, Metriql, Cube, MetricFlow, or MetricForge NYC. The stack changes. The discipline does not.

And the good news for the rest of us, the ones without Airbnb's engineering budget, is that the open-source ecosystem is finally mature enough that a single engineer with a laptop and a weekend can build the spirit of Minerva. You do not need a platform team. You need YAML, a catalog, three engines, a contract, and the patience to say *no* when the next analyst tries to define "active user" in a spreadsheet.

The code is on [GitHub](https://github.com/Stefen-Taime/Semantic-Layer-Platform). The architecture is opinionated. The story is still being written.

But the question "what was our revenue yesterday?" now takes thirty seconds. And the answer is always the same.

---

*Built with MinIO, Apache Spark, Apache Hive Metastore, Trino, Apache Druid, Apache Airflow, FastAPI, Streamlit, Plotly, and PostgreSQL. All open source. All self-hosted. All governed.*

*If this story resonated, consider giving the repo a ⭐. If it made you uncomfortable about your own metric definitions — good.*
