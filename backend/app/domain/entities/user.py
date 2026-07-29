"""User domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class User:
    """User domain entity representing a registered user account in the system.
    
    This domain entity is pure Python and completely decoupled from ORM models or database frameworks.
    """

    email: str
    password_hash: str
    full_name: str
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update_password(self, new_password_hash: str) -> None:
        """Updates the user's password hash and updates the timestamp."""
        self.password_hash = new_password_hash
        self.updated_at = datetime.now(timezone.utc)
