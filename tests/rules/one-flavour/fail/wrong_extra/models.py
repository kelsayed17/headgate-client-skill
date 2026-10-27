from pydantic import BaseModel, ConfigDict


class Item(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
