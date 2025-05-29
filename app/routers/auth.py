from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SessionDep,
    Token,
    authenticate_user,
    create_access_token,
    get_current_active_user,
)
from app.models import User, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
) -> Token:
    user = authenticate_user(form_data.username, form_data.password, session=session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me")
def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserPublic:
    return UserPublic.model_validate(current_user)
