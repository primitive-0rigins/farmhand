# Math Engineering Review: Weather Risk and Planning Rules

## Finding

- Location: `backend/app/weather.py`, `backend/app/domain/rules.py`
- Severity: low correctness risk; high risk if probabilistic language is added
  without measurements.
- Current method: provider-supplied weather fields feed explicit deterministic
  rules (for example, thunderstorm risk or wind at least 30 mph).
- Problem: determine whether weather-task generation should use a learned or
  calibrated risk score.

## Engineering frame

The decision is whether to show a farm-preparation task. Inputs are a forecast
provider's categorical and numeric fields plus farm assets and crops. The
system has no stored forecast probabilities, task outcomes, false-alarm labels,
or loss model. Forecasts can drift by provider, location, and season; the cost
of a missed dangerous-weather task is potentially higher than an unnecessary
preparation task. The current deterministic policy is explainable, has no
online state, and is the credible baseline.

## Candidate methods

| Method | Fit | Assumptions | Expected benefit | Cost | Main risk |
|---|---|---|---|---|---|
| Existing deterministic thresholds | Direct | Provider fields are usable | Explainable action now | Low | Thresholds are not locally tuned |
| Brier score / reliability diagram | Evaluation only | Probability forecasts and observed outcomes | Measures calibration | Low after instrumentation | Cannot calibrate categorical inputs |
| Platt or isotonic calibration | Not yet eligible | Labeled outcomes and stable probability scores | Locally calibrated risk | Moderate | False confidence from sparse or shifted data |
| EWMA of outcomes | Not yet eligible | Repeated comparable observations | Detects changing local rates | Moderate | Confounds weather, farmer behavior, and reporting |

## Recommended action

Keep the deterministic rules. Do not replace them with a probability score or
claim that a task has a calibrated chance of being necessary.

Before reconsidering, instrument per-farm, privacy-reviewed observations:

1. forecast provider, timestamp, and raw forecast fields;
2. task shown, completed, snoozed, or dismissed;
3. a voluntary outcome label such as `weather_damage_observed` or
   `preparation_helped`;
4. explicit retention and export policy.

With sufficient representative observations, evaluate provider probabilities
using Brier score and reliability diagrams before considering Platt or isotonic
calibration. Compare every candidate against the existing deterministic policy
on missed-risk rate, unnecessary-task rate, and task completion burden.

## Guardrails and rollback

Any future score must remain behind a feature flag, retain the deterministic
fallback, expose its reason and confidence source, and be disabled when data
coverage, calibration, or drift checks fail. No production mathematical method
is selected in this review.
