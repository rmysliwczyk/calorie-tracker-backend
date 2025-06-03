import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import User

load_dotenv()

## Database

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

## Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

SECRET_KEY = os.environ["SECRET_KEY"]
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: str | None = None


def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(
        password=bytes(plain_password, encoding="utf-8"),
        hashed_password=bytes(hashed_password, encoding="utf-8"),
    )


def get_password_hash(password: str):
    return bcrypt.hashpw(
        password=bytes(password, encoding="utf-8"), salt=bcrypt.gensalt()
    )


def authenticate_user(username: str, password: str, session: SessionDep) -> User | None:
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_user_from_token(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    try:
        user = session.exec(
            select(User).where(User.username == token_data.username)
        ).one()
    except NoResultFound:
        raise credentials_exception
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(decode_user_from_token)],
):
    if current_user.is_active is False:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_admin_user(
    current_user: Annotated[User, Depends(decode_user_from_token)],
):
    if current_user.is_active is False:
        raise HTTPException(status_code=400, detail="Inactive user")

    if current_user.is_admin is False:
        raise HTTPException(status_code=403, detail="Only for admins")
    return current_user


def allow_self(
    current_user: Annotated[User, Depends(decode_user_from_token)],
    user_id: int = Path(...),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="User is not the owner")


def allow_admin_or_self(
    current_user: Annotated[User, Depends(decode_user_from_token)],
    user_id: int = Path(...),
):
    if current_user.is_admin == False:
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="User is not the owner")
