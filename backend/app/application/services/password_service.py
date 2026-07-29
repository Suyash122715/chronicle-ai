"""Password service interface/re-export for application use cases."""

from app.infrastructure.security.password_service import PasswordService

__all__ = ["PasswordService"]
