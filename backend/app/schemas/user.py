from pydantic import BaseModel


class UserOut(BaseModel):
    id: str
    username: str
    best_score: int
    is_admin: bool = False

    model_config = {"from_attributes": True}
