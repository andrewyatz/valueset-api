"""SQLAlchemy ORM models for ValueSet database schema."""

import json
from typing import Any, Dict, List, cast

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class ValueSetORM(Base):
    """ORM model for valuesets table."""

    __tablename__ = "valuesets"

    accession: Mapped[str] = mapped_column(String, primary_key=True)
    purl: Mapped[str] = mapped_column(Text, nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    full_definition: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship to values
    values: Mapped[List["ValueSetValueORM"]] = relationship(
        "ValueSetValueORM", back_populates="valueset_rel", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ValueSetORM(accession={self.accession!r})>"


class ValueSetValueORM(Base):
    """ORM model for valueset_values table."""

    __tablename__ = "valueset_values"

    accession: Mapped[str] = mapped_column(String, primary_key=True)
    valueset: Mapped[str] = mapped_column(String, ForeignKey("valuesets.accession"), nullable=False)
    purl: Mapped[str | None] = mapped_column(Text, nullable=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    identical_terms: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON serialized
    similar_terms: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON serialized
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    full_definition: Mapped[str] = mapped_column(Text, nullable=False)
    deprecated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deprecated_to: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON serialized
    additional: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON serialized

    # Relationship to valueset
    valueset_rel: Mapped["ValueSetORM"] = relationship("ValueSetORM", back_populates="values")

    # Indexes
    __table_args__ = (
        Index("idx_valueset_values_valueset", "valueset"),
        Index("idx_valueset_values_deprecated", "deprecated"),
    )

    def __repr__(self) -> str:
        return f"<ValueSetValueORM(accession={self.accession!r}, valueset={self.valueset!r})>"

    # Helper methods for JSON field serialization/deserialization
    def get_identical_terms(self) -> List[str]:
        """Deserialize identical_terms JSON field."""
        if not self.identical_terms:
            return []
        try:
            return cast(List[str], json.loads(self.identical_terms))
        except json.JSONDecodeError:
            return []

    def set_identical_terms(self, terms: List[str]) -> None:
        """Serialize identical_terms to JSON."""
        self.identical_terms = json.dumps(terms) if terms else None

    def get_similar_terms(self) -> List[str]:
        """Deserialize similar_terms JSON field."""
        if not self.similar_terms:
            return []
        try:
            return cast(List[str], json.loads(self.similar_terms))
        except json.JSONDecodeError:
            return []

    def set_similar_terms(self, terms: List[str]) -> None:
        """Serialize similar_terms to JSON."""
        self.similar_terms = json.dumps(terms) if terms else None

    def get_deprecated_to(self) -> List[str]:
        """Deserialize deprecated_to JSON field."""
        if not self.deprecated_to:
            return []
        try:
            return cast(List[str], json.loads(self.deprecated_to))
        except json.JSONDecodeError:
            return []

    def set_deprecated_to(self, terms: List[str]) -> None:
        """Serialize deprecated_to to JSON."""
        self.deprecated_to = json.dumps(terms) if terms else None

    def get_additional(self) -> Dict[str, Any]:
        """Deserialize additional JSON field."""
        if not self.additional:
            return {}
        try:
            return cast(Dict[str, Any], json.loads(self.additional))
        except json.JSONDecodeError:
            return {}

    def set_additional(self, data: Dict[str, Any]) -> None:
        """Serialize additional to JSON."""
        self.additional = json.dumps(data) if data else None
