from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import col, select

from app.dependencies import SessionDep, get_current_active_user
from app.models import FoodItem, FoodItemCreate, FoodItemPublic, FoodItemUpdate, User

router = APIRouter(prefix="/fooditems", tags=["fooditem"])


@router.get(
    "/",
    response_model=list[FoodItemPublic],
    dependencies=[Depends(get_current_active_user)],
)
def read_food_items(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    name: str = "",
    barcode: str = "",
) -> list[FoodItemPublic]:
    food_items = session.exec(
        select(FoodItem)
        .where(col(FoodItem.name).ilike(f"%{name}%"))
        .where(col(FoodItem.barcode).ilike(f"%{barcode}%"))
        .offset(offset)
        .limit(limit)
    ).all()
    return [FoodItemPublic.model_validate(food_item) for food_item in food_items]


@router.get(
    "/{food_item_id}",
    response_model=FoodItemPublic,
    dependencies=[Depends(get_current_active_user)],
)
def read_food_item(food_item_id: int, session: SessionDep) -> FoodItemPublic:
    food_item = session.get(FoodItem, food_item_id)
    if not food_item:
        raise HTTPException(status_code=404, detail="Food item not found")
    return FoodItemPublic.model_validate(food_item)


@router.post(
    "/",
    response_model=FoodItemPublic,
    dependencies=[Depends(get_current_active_user)],
)
def create_food_item(
    current_user: Annotated[User, Depends(get_current_active_user)],
    food_item_in: FoodItemCreate,
    session: SessionDep,
) -> FoodItemPublic:
    new_food_item = FoodItem.model_validate(
        food_item_in.model_dump(exclude_unset=True),
        update={"creator_id": current_user.id},
    )
    if new_food_item.calories == 0:
        new_food_item.carbs = 0
        new_food_item.fats = 0
        new_food_item.protein = 0

    session.add(new_food_item)
    session.commit()
    session.refresh(new_food_item)
    return FoodItemPublic.model_validate(new_food_item)


@router.delete("/{food_item_id}", dependencies=[Depends(get_current_active_user)])
def delete_food_item(
    current_user: Annotated[User, Depends(get_current_active_user)],
    food_item_id: int,
    session: SessionDep,
):
    food_item = session.get(FoodItem, food_item_id)
    if not food_item:
        raise HTTPException(status_code=404, detail="Food item not found")
    if current_user.is_admin == False:
        if current_user.id != food_item.creator_id:
            raise HTTPException(
                status_code=403, detail="Only creator or admin can delete food item"
            )
    try:
        session.delete(food_item)
        session.commit()
    except AssertionError:
        raise HTTPException(
            status_code=400,
            detail="This food item is part of a recipe. You can't delete it.",
        )
    return {"ok": True}


@router.patch(
    "/{food_item_id}",
    response_model=FoodItemPublic,
    dependencies=[Depends(get_current_active_user)],
)
def update_food_item(
    current_user: Annotated[User, Depends(get_current_active_user)],
    food_item_id: int,
    food_item_data: FoodItemUpdate,
    session: SessionDep,
):
    food_item_in_db = session.get(FoodItem, food_item_id)
    if not food_item_in_db:
        raise HTTPException(status_code=404, detail="Food item not found")
    if current_user.is_admin == False:
        if current_user.id != food_item_in_db.creator_id:
            raise HTTPException(
                status_code=403, detail="Only creator or admin can update food item"
            )
    food_item_data = FoodItemUpdate.model_validate(
        food_item_data.model_dump(exclude_unset=True)
    )
    food_item_in_db.sqlmodel_update(food_item_data)
    session.add(food_item_in_db)
    session.commit()
    session.refresh(food_item_in_db)
    return food_item_in_db
