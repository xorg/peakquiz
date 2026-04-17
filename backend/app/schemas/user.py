from pydantic import BaseModel


class UserOut(BaseModel):
    id: str
    username: str
    best_score: int

    model_config = {"from_attributes": True}
