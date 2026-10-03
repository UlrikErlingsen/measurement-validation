"""Friendly domain errors for Measure Signal."""


class DataProblem(ValueError):
    """Raised when an input cannot support the requested analysis."""


MEMORY_MESSAGE = (
    "There is not enough memory on this computer for this file or step. Close other programs, keep only the item, "
    "identifier and wave columns you need, or split the respondents into batches."
)


def friendly_message(exc: Exception) -> str:
    """Return a concise user-facing error without exposing internals."""
    if isinstance(exc, DataProblem):
        return str(exc)
    if isinstance(exc, MemoryError):
        return MEMORY_MESSAGE
    if isinstance(exc, (KeyError, ValueError, TypeError)):
        return f"Measure Signal could not complete that request: {exc}"
    return "Measure Signal hit an unexpected problem. Check the data roles and try again."

