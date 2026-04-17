# Druid Serving Layer

Apache Druid acts here as a fast OLAP layer for a few pre-aggregated metrics.

## Why Druid

- lower latency on already-aggregated datasets
- good support for dashboard-style queries
- a credible complement to Trino in a data platform architecture

## Trino vs Druid

- **Trino**: flexible, strong for ad-hoc, better for scanning the certified tables
- **Druid**: fast on pre-aggregated datasources, better for targeted serving

## Metrics routed to Druid

- `daily_zone_revenue`
- `daily_completed_trips`

## Ingestion

The specs in `druid/ingestion_specs/` assume that an intermediate export has already produced daily or per-zone aggregated files.

## Docker topology

The project's Druid Docker stack now uses a multi-service topology:

- `druid-zookeeper`
- `druid-postgres`
- `druid-coordinator`
- `druid-broker`
- `druid-historical`
- `druid-middlemanager`
- `druid`: router and console

This layout is closer to the official Druid Docker quickstart than a hand-rolled single container.

## Limits

- aggregated datasets must be prepared before ingestion
- Druid makes the stack noticeably heavier in memory
- the topology is a single-machine demo, not a high-availability cluster
