"""Token service interface re-export for application use cases.

Use cases depend on TokenServiceInterface, not on JWTTokenService directly,
keeping the Application layer decoupled from the concrete JWT implementation.
"""

from app.domain.interfaces.token_service import TokenServiceInterface, TokenPayload

__all__ = ["TokenServiceInterface", "TokenPayload"]
