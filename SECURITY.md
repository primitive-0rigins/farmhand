# Security Notes

Farmhand is public. Keep demo data public-safe and city-level.

## Current Rules

- Do not commit real farm addresses, customer records, API keys, access tokens, database dumps, logs, or `.env` files.
- Use `.env.example` for placeholder configuration only.
- Keep CORS origins explicit through `FARMHAND_ALLOWED_ORIGINS`; do not use wildcard origins for deployed environments.
- Keep weather, pest, disease, and AI providers behind adapters before adding external credentials.
- Treat editable playbooks and farm notes as private user data once persistence is introduced.

## Before Production

- Keep authentication and authorization checks on every user-owned farm resource.
- Add rate limits around public API routes.
- Review provider terms for weather, pest, and disease data.
- Add backup and export controls before storing commercial farm records.
