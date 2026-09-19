from pydantic import BaseModel, ConfigDict, Field


class TicketCreate(BaseModel):
    """The request body accepted when a customer opens a support ticket."""

    model_config = ConfigDict(str_strip_whitespace=True)

    subject: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=2_000)


class TicketResponse(BaseModel):
    """The public representation of a support ticket."""

    id: str
    subject: str
    description: str
