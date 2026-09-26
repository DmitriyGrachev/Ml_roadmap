"""Student repository using provided SQLAlchemy Core schema and caller-owned engine."""

from dataclasses import dataclass

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine


@dataclass(frozen=True)
class Equipment:
    """An immutable record; text validation belongs in the repository boundary."""

    serial: str
    name: str


class EquipmentRepository:
    """Multiple repository instances using the same engine share persisted records."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        metadata = MetaData()
        self.table = Table(
            "equipment",
            metadata,
            Column("serial", String, primary_key=True),
            Column("name", String, nullable=False),
        )
        metadata.create_all(engine)

    def add(self, item: Equipment) -> None:
        """Commit one valid record; translate duplicate serials into ValueError."""
        # TODO: validate both text fields and insert atomically using bound parameters.
        raise NotImplementedError("add equipment")

    def list_all(self) -> list[Equipment]:
        """Read fresh immutable records ordered by serial, in a detached result list."""
        # TODO: select with an explicit sort and close the connection after reading.
        raise NotImplementedError("list equipment")
