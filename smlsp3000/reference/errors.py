class InvalidConfiguration(Exception):
    """Structured prepare() failure (docs/ENGINE_SPEC.md state/error contract).

    ``code`` is a stable machine-readable reason; ``detail`` is human text.
    """

    def __init__(self, code: str, detail: str):
        super().__init__(f"INVALID_CONFIGURATION[{code}]: {detail}")
        self.code = code
        self.detail = detail
