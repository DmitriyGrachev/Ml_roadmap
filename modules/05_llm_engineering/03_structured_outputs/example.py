"""A valid output shape does not establish whether a catalog label is true."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CatalogLabel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    category: Literal["plant", "mineral"]
    name: str = Field(min_length=1, max_length=80)


def validate_label(raw: str) -> CatalogLabel:
    return CatalogLabel.model_validate_json(raw)


def main() -> None:
    label = validate_label('{"category":"mineral","name":"granite"}')
    print(label.model_dump_json())
    wrong_but_well_formed = validate_label('{"category":"plant","name":"granite"}')
    print(f"Schema also accepts: {wrong_but_well_formed.model_dump_json()}")
    print("A domain reference or reviewer is needed to catch that semantic error.")


if __name__ == "__main__":
    main()
