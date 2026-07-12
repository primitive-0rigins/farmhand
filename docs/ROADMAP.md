# Farmhand Roadmap

## Phase 0 - Project Skeleton

- [x] Name and product direction
- [x] Python backend scaffold
- [x] React frontend scaffold
- [x] Repo standards in `AGENTS.md` and `CLAUDE.md`
- [x] Deterministic rule engine seed
- [x] Backend tests for first rules

## Phase 1 - Farm Setup

- [x] Create demo farm profile
- [x] Capture city/state and planting zone in demo data
- [ ] Add growing spaces: field, greenhouse, high tunnel, orchard, pasture
- [x] Add demo assets: tractor, greenhouse, irrigation
- [x] Add demo crop list
- [ ] Store setup in Postgres

## Phase 2 - Daily Operating Calendar

- [x] Today view
- [x] This week view
- [x] Task completion and snooze
- [x] Session-local manual task creation
- [x] Generated task reasons
- [x] Session-local editable task templates

## Phase 3 - Weather Rules

- [ ] NOAA/NWS weather adapter
- [x] Thunderstorm prep rules
- [x] Frost prep rules
- [x] Heat stress rules
- [x] High wind rules
- [x] Rain/irrigation rules
- [x] Session-local farmer-customized alert playbooks

## Phase 4 - Crop And Zone Rules

- [x] Zone-aware monthly calendar seed
- [x] Crop-specific scouting windows
- [x] Greenhouse start reminders
- [x] Transplant reminders
- [x] Harvest windows
- [ ] Succession planting reminders

## Phase 5 - Pest And Disease Pressure

- [ ] Rule tables for common crops and pests
- [ ] Regional observation model
- [ ] Neighboring county/state signal ingestion
- [ ] Pest arrival estimates
- [x] Disease pressure estimates from rain
- [x] Scout-now alerts with explainable reasons

## Phase 6 - Commercial Readiness

- [ ] Auth and account creation
- [ ] Mobile-friendly UI pass
- [ ] Onboarding copy pass
- [ ] Billing decision
- [ ] Backup/export
- [ ] Terms/privacy review
- [ ] Trademark/domain review for "Farmhand"
