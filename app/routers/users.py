from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select

from app.dependencies import (
    SessionDep,
    allow_admin_or_self,
    allow_self,
    get_current_active_admin_user,
    get_password_hash,
)
from app.models import User, UserCreate, UserPublic, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    response_model=list[UserPublic],
    dependencies=[Depends(get_current_active_admin_user)],
)
def read_users(
    session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100
) -> list[UserPublic]:
    users = session.exec(select(User).offset(offset).limit(limit)).all()
    return [UserPublic.model_validate(user) for user in users]


@router.get(
    "/{user_id}",
    response_model=UserPublic,
    dependencies=[Depends(allow_self)],
)
def read_user(user_id: int, session: SessionDep) -> UserPublic:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic.model_validate(user)


@router.post("/", response_model=UserPublic)
def create_user(
    user_in: UserCreate,
    session: SessionDep,
) -> UserPublic:

    new_user = User.model_validate(
        user_in, update={"hashed_password": get_password_hash(user_in.password)}
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return UserPublic.model_validate(new_user)


@router.post(
    "/admin",
    response_model=UserPublic,
    dependencies=[Depends(get_current_active_admin_user)],
)
def create_admin(
    user_in: UserCreate,
    session: SessionDep,
) -> UserPublic:

    new_user = User.model_validate(
        user_in,
        update={
            "hashed_password": get_password_hash(user_in.password),
            "is_admin": True,
        },
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return UserPublic.model_validate(new_user)


@router.delete("/{user_id}", dependencies=[Depends(allow_admin_or_self)])
def delete_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"ok": True}


@router.patch(
    "/{user_id}",
    response_model=UserPublic,
    dependencies=[Depends(allow_admin_or_self)],
)
def update_user(user_id: int, user: UserUpdate, session: SessionDep):
    user_db = session.get(User, user_id)
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = user.model_dump(exclude_unset=True)
    user_db.sqlmodel_update(user_data)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)
    return user_db
