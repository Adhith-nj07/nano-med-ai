# Live Environment Updates

## Behaviour
When a client updates the simulation environment (e.g., modifying `pH` or `temperature_c`), the following strictly occurs:
1. The new values are merged into `EnvironmentState`.
2. A chronological `ENVIRONMENT_CHANGE` event is logged.
3. The engine hashes the environment deterministically (SHA-256) and evaluates all active transformation models.

## Crucial Release Model Handling
Because the Korsmeyer-Peppas model parameters were fitted under static experimental conditions, it **cannot causally respond** to dynamic pH or temperature changes. 

If the environment changes, the K-P model explicitly suppresses any invented acceleration and logs an event stating:
`"Environment changed, but Korsmeyer-Peppas release parameters cannot causally update. Ignoring change."`

The API reflects this in the response:
`"release_model_response": "unsupported"`
