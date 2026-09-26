"""A handoff preserves facts and unanswered questions without granting new powers."""

from pydantic import BaseModel, ConfigDict, Field


class Handoff(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    goal: str = Field(min_length=1)
    facts: list[str]
    open_questions: list[str]


def main() -> None:
    handoff = Handoff(
        goal="Identify the telescope's maker",
        facts=["The catalogue describes a brass body and an 1890 date."],
        open_questions=["Is a maker's mark visible in the archive photographs?"],
    )
    print(handoff.model_dump_json())
    print("The receiving worker gets its own permissions and budget from the application.")


if __name__ == "__main__":
    main()
