"""Neutral transaction demo, independent of the student repository."""

from sqlalchemy import String, create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)


def create_schema(engine: Engine) -> None:
    Base.metadata.create_all(engine)


def write_batch(engine: Engine, names: list[str], events: list[str]) -> None:
    events.append("open")
    try:
        with Session(engine) as session:
            try:
                session.add_all(Label(name=name) for name in names)
                events.append(f"pending={len(session.new)}")
                session.flush()
                events.append(f"flushed={len(names)}")
                session.commit()
                events.append("commit")
            except Exception:
                session.rollback()
                events.append("rollback")
                raise
    finally:
        events.append("close")


def main() -> None:
    engine = create_engine("sqlite://")
    try:
        create_schema(engine)
        for names in (["Atlas"], ["Beacon", "Atlas"], ["Cedar"]):
            events: list[str] = []
            try:
                write_batch(engine, names, events)
            except IntegrityError:
                print("rejected: duplicate label")
            print(f"{names}: {' -> '.join(events)}")
            with Session(engine) as session:
                persisted = list(session.scalars(select(Label.name).order_by(Label.name)))
                print(f"persisted: {persisted}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
