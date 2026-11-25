class DomainError(Exception):
    """Base exception for application domain errors."""


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist."""


class ConflictError(DomainError):
    """Raised when an operation conflicts with existing data."""


class BusinessRuleError(DomainError):
    """Raised when an operation violates a business rule."""
