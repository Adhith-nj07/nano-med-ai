class SimulationAPIError(Exception):
    """Base class for structured API exceptions."""
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self):
        return {"error": self.code, "message": self.message}

class UnsupportedCapabilityError(SimulationAPIError):
    def __init__(self, capability: str, reason: str):
        super().__init__(f"Capability '{capability}' is not supported. Reason: {reason}", "UNSUPPORTED_CAPABILITY")
        self.capability = capability

class ModelNotValidatedError(SimulationAPIError):
    def __init__(self, model_name: str):
        super().__init__(f"Model '{model_name}' has not completed required scientific validation.", "MODEL_NOT_VALIDATED")

class DataNotValidatedError(SimulationAPIError):
    def __init__(self, dataset_name: str):
        super().__init__(f"Data '{dataset_name}' is not flagged as validated/model-ready.", "DATA_NOT_VALIDATED")

class IncompatibleEnvironmentError(SimulationAPIError):
    def __init__(self, mechanism: str, reason: str):
        super().__init__(f"Mechanism '{mechanism}' is incompatible with the requested environment. {reason}", "INCOMPATIBLE_ENVIRONMENT")

class IncompatibleFormulationError(SimulationAPIError):
    def __init__(self, mechanism: str, reason: str):
        super().__init__(f"Mechanism '{mechanism}' is incompatible with the requested formulation. {reason}", "INCOMPATIBLE_FORMULATION")

class MissingRequiredInputError(SimulationAPIError):
    def __init__(self, field: str):
        super().__init__(f"Missing required input: {field}", "MISSING_REQUIRED_INPUT")
