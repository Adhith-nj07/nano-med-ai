
class KorsmeyerPeppasModel(TransformationModel):
    """
    Mathematical/Empirical drug release model based on Korsmeyer-Peppas.
    Equation: Mt / M_inf = k * t^n
    """
    def __init__(self, k: float, n: float, max_valid_fraction: float = 0.6):
        self.k = k
        self.n = n
        self.max_valid_fraction = max_valid_fraction
        self.last_env_hash = None
        
    def apply(self, current_time: float, np_state: NanoparticleState, env_state: EnvironmentState) -> List[TransformationEvent]:
        events = []
        
        # Environmental check: K-P parameters are static for the conditions they were fitted on.
        current_env_hash = hash(f"{env_state.pH}_{env_state.temperature_c}_{env_state.buffer}")
        
        if self.last_env_hash is not None and current_env_hash != self.last_env_hash:
            events.append(TransformationEvent(
                event_id=str(uuid.uuid4()),
                timestamp=current_time,
                event_type=EventType.ENVIRONMENT_CHANGE,
                description="Environment changed, but Korsmeyer-Peppas release parameters cannot causally update. Ignoring change.",
                trigger="unsupported_for_release_model",
                model_source="KorsmeyerPeppasModel",
                uncertainty="extrapolation"
            ))
        
        self.last_env_hash = current_env_hash

        if current_time <= 0:
            return events
            
        try:
            # Calculate fractional release at current time
            fractional_release = self.k * (current_time ** self.n)
            
            # Clip at 1.0 physically
            fractional_release = min(fractional_release, 1.0)
            
            # Evaluate domain validity
            validity = "within_model_domain"
            if fractional_release > self.max_valid_fraction:
                validity = "extrapolation"
            
            # Check if this changed significantly
            old_val = np_state.cumulative_released_fraction
            if abs(fractional_release - old_val) > 1e-6:
                np_state.cumulative_released_fraction = fractional_release
                np_state.remaining_drug_amount = max(0.0, 1.0 - fractional_release)
                
                event = TransformationEvent(
                    event_id=str(uuid.uuid4()),
                    timestamp=current_time,
                    event_type=EventType.DRUG_RELEASE,
                    description=f"Cumulative release updated to {fractional_release*100:.2f}%",
                    trigger="Time step",
                    previous_state_snapshot={"cumulative_released_fraction": old_val},
                    new_state_snapshot={"cumulative_released_fraction": fractional_release},
                    magnitude=abs(fractional_release - old_val),
                    model_source=f"Korsmeyer-Peppas (k={self.k:.4f}, n={self.n:.4f})",
                    uncertainty=validity
                )
                events.append(event)
        except Exception as e:
            pass
            
        return events
