# CLAUDE.md - Farmhand

This repository is for Farmhand, a farm-aware daily operations calendar.

## Non-Negotiables

- Do not build a chatbot-first app.
- Do not hide rule decisions behind vague AI output.
- Do not use real farm addresses, customer data, credentials, or private logs.
- Do not overbuild. Start with daily tasks, farm setup, weather rules, and
  editable playbooks.

## Product Shape

Farmhand helps a farmer answer:

1. What should I do today?
2. What should I watch for?
3. What weather or pest pressure is changing?
4. What is coming soon?

The UI should feel like a reliable farmhand, not an analytics dashboard.

## Architecture Direction

- Python domain logic owns task generation.
- Postgres stores farms, crops, assets, playbooks, tasks, and signals.
- React owns the commercial-grade operator experience.
- Background jobs eventually sync weather, pest, and disease signals.

## Initial Domain Model

- Farm profile: location, zone, farm type
- Crops: crop name, planting windows, risk windows
- Assets: greenhouse, tractor, irrigation, row cover, cold storage
- Playbooks: editable reusable procedures
- Signals: weather, pest, disease, regional observations
- Tasks: generated or manual, with reasons

## Tone

Use plain language. Farmers should not have to decode software jargon.
