from sqlmodel import Field, SQLModel

# User model


class UserBase(SQLModel):
    username: str = Field(unique=True, max_length=64)


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    hashed_password: str = Field(default="", max_length=255)


class UserPublic(SQLModel):
    username: str
    id: int
    is_active: bool
    is_admin: bool


class UserCreate(UserBase):
    password: str


class UserUpdate(SQLModel):
    username: str | None = None
    is_active: bool | None = None
