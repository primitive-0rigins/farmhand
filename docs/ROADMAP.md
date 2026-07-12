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

> Crop timing (start, transplant, harvest) is zone-anchored for USDA zones 3-8,
> where a spring-transplant / summer-harvest pattern holds. The general monthly
> calendar is still zone 8b only, and zones 9+ (winter growing season) are left
> unscheduled on purpose until a dedicated model exists, rather than given
> confidently wrong dates.

## Phase 5 - Pest And Disease Pressure

- [ ] Rule tables for common crops and pests
- [ ] Regional observation model
- [ ] Neighboring county/state signal ingestion
- [ ] Pest arrival estimates
- [x] Disease pressure estimates from rain
- [x] Scout-now alerts with explainable reasons
- [x] Forward-looking disease watch from the forecast window

> Disease/fungus pressure is weather-driven, not calendar-driven, so its
> anticipation reads the upcoming forecast rather than a fixed date. The logic
> is wired against the demo forecast now; it earns real lead time once the
> Phase 3 NOAA/NWS adapter supplies live multi-day weather.

## Phase 6 - Commercial Readiness

- [ ] Auth and account creation
- [ ] Mobile-friendly UI pass
- [ ] Onboarding copy pass
- [ ] Billing decision
- [ ] Backup/export
- [ ] Terms/privacy review
- [ ] Trademark/domain review for "Farmhand"
