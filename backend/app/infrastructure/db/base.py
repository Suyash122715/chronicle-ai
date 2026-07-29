"""SQLAlchemy 2 Declarative Base for domain ORM mappings."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2 ORM models across the application.
    
    TODO: Database models will inherit from this base class when implemented in future phases.
    """
    pass
