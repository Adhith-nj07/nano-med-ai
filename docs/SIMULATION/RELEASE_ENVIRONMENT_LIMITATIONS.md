# Release Environment Limitations

## Missing Environment Data
The foundational release dataset lacks controlled variation in pH, temperature, and ionic strength. All trajectories were measured under assumed standard static *in vitro* conditions.

## Engine Behaviour
If a simulation dynamically alters pH or temperature (e.g. from 7.4 to 5.5), the Korsmeyer-Peppas model **WILL NOT** hallucinate an accelerated release curve. It will record an ENVIRONMENT_CHANGE event explicitly stating that release parameters cannot causally update, and continue evaluating time against the original static fit.
