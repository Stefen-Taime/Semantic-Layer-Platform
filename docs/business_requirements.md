# Business Requirements

This document captures the initial business needs that drive the semantic layer.

## Finance

The Finance team wants to track the economic performance of the taxi service at a daily and geographic grain.

- `gross_revenue` by zone and by day
- `average_fare` by zone and by day
- `tip_rate` by zone and by day

Typical questions:

- What is the daily gross revenue per pickup zone?
- Which zones generate the highest average fares?
- Does tip rate vary by borough or by payment type?

## Operations

The Operations team wants to track service volume and efficiency.

- `completed_trips` by zone
- `average_trip_duration` by zone
- `average_trip_distance` by zone

Typical questions:

- Which zones concentrate the most completed trips?
- Does average trip duration grow with time of day or location?
- What relationship exists between average distance and borough?

## Product

The Product team wants to better understand rider behaviour and payment modes.

- `payment_type_share`
- distribution of `passenger_count`

Typical questions:

- What share of trips is paid by card versus cash?
- Does the distribution of passenger count change across pickup zones?
- Are there segments with distinct payment behaviour?

## Modelling consequences

These needs require at minimum:

- a certified fact table of taxi trips,
- time, zone, borough, vendor, and payment-type dimensions,
- simple aggregated metrics,
- a few derived metrics to illustrate the semantic layer.
