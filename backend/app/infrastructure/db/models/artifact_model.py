"""SQLAlchemy 2 ORM model for the artifacts table."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.artifact import Artifact, ProcessingStatus
from app.infrastructure.db.base import Base


class ArtifactModel(Base):
    """SQLAlchemy ORM model mapping to the 'artifacts' PostgreSQL table."""

    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=ProcessingStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_domain(self) -> Artifact:
        """Converts ORM model to pure Domain entity."""
        return Artifact(
            id=self.id,
            user_id=self.user_id,
            filename=self.filename,
            stored_filename=self.stored_filename,
            file_path=self.file_path,
            file_size=self.file_size,
            mime_type=self.mime_type,
            status=ProcessingStatus(self.status),
            raw_text=self.raw_text,
            error_message=self.error_message,
            retry_count=self.retry_count,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, artifact: Artifact) -> "ArtifactModel":
        """Converts Domain entity to ORM model."""
        return cls(
            id=artifact.id,
            user_id=artifact.user_id,
            filename=artifact.filename,
            stored_filename=artifact.stored_filename,
            file_path=artifact.file_path,
            file_size=artifact.file_size,
            mime_type=artifact.mime_type,
            status=artifact.status.value,
            raw_text=artifact.raw_text,
            error_message=artifact.error_message,
            retry_count=artifact.retry_count,
            created_at=artifact.created_at,
            updated_at=artifact.updated_at,
        )
