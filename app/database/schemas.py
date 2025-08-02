from pydantic import BaseModel

class MetaData(BaseModel):
    id: int
    likes: int
    dislikes: int

    class Config:
        # Pydantic's orm_mode is still useful here for converting a sqlite3.Row object to the Pydantic model
        orm_mode = True