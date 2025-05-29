from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import col, select

from app.dependencies import SessionDep, get_current_active_user
from app.models import Meal, MealCreate, MealPublic, MealUpdate, User

router = APIRouter(prefix="/meals", tags=["meals"])


@router.get(
    "/",
    response_model=list[MealPublic],
    dependencies=[Depends(get_current_active_user)],
)
def read_my_meals(
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
    selected_date: date = Query(None),
    ids: list[int] = Query(None, description="List of meal IDs to retrieve"),
) -> list[MealPublic]:
    if ids:
        meals = session.exec(
            select(Meal).where(col(Meal.is_shared) == True).where(col(Meal.id).in_(ids))
        ).all()
        return [MealPublic.model_validate(meal) for meal in meals]
    if selected_date is None:
        raise HTTPException(
            status_code=400, detail="You must provide the selected date query"
        )
    meals = session.exec(
        select(Meal)
        .where(col(Meal.creator_id) == current_user.id)
        .where(col(Meal.created_at) == selected_date)
    ).all()
    return [MealPublic.model_validate(meal) for meal in meals]


@router.get(
    "/{meal_id}",
    response_model=MealPublic,
    dependencies=[Depends(get_current_active_user)],
)
def read_meal(
    session: SessionDep,
    meal_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> MealPublic:
    meal = session.get(Meal, meal_id)
    if not meal:
        raise HTTPException(
            status_code=400, detail=f"Meal with id {meal_id} not found."
        )

    if meal.creator_id != current_user.id and current_user.is_admin == False:
        if meal.is_shared == False:
            raise HTTPException(
                status_code=400, detail="You don't have access to this meal."
            )
    return MealPublic.model_validate(meal)


@router.post(
    "/create-many",
    response_model=list[MealPublic],
    dependencies=[Depends(get_current_active_user)],
)
def create_meals(
    current_user: Annotated[User, Depends(get_current_active_user)],
    meals_in: list[MealCreate],
    session: SessionDep,
) -> list[MealPublic]:
    new_meals = []
    for meal in meals_in:
        new_meal = Meal.model_validate(meal, update={"creator_id": current_user.id})
        if new_meal.food_collection_id and new_meal.food_item_id != None:
            raise HTTPException(
                status_code=400,
                detail="Meal can include food item or food collection, not both.",
            )
        session.add(new_meal)
        session.commit()
        session.refresh(new_meal)
        new_meals.append(MealPublic.model_validate(new_meal))
    return new_meals


@router.post(
    "/",
    response_model=MealPublic,
    dependencies=[Depends(get_current_active_user)],
)
def create_meal(
    current_user: Annotated[User, Depends(get_current_active_user)],
    meal_in: MealCreate,
    session: SessionDep,
) -> MealPublic:
    new_meal = Meal.model_validate(meal_in, update={"creator_id": current_user.id})
    if new_meal.food_collection_id and new_meal.food_item_id != None:
        raise HTTPException(
            status_code=400,
            detail="Meal can include food item or food collection, not both.",
        )
    session.add(new_meal)
    session.commit()
    session.refresh(new_meal)
    return MealPublic.model_validate(new_meal)


@router.delete("/{meal_id}", dependencies=[Depends(get_current_active_user)])
def delete_meal(
    current_user: Annotated[User, Depends(get_current_active_user)],
    meal_id: int,
    session: SessionDep,
):
    meal = session.get(Meal, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Food item not found")
    if current_user.is_admin == False:
        if current_user.id != meal.creator_id:
            raise HTTPException(
                status_code=403, detail="Only creator or admin can delete meal"
            )
    session.delete(meal)
    session.commit()
    return {"ok": True}


@router.patch(
    "/update-many",
    response_model=list[MealPublic],
    dependencies=[Depends(get_current_active_user)],
)
def update_meals(
    current_user: Annotated[User, Depends(get_current_active_user)],
    meal_data: list[MealUpdate],
    session: SessionDep,
):
    updated_meals = []
    for meal in meal_data:
        meal_db = session.get(Meal, meal.id)
        if not meal_db:
            raise HTTPException(
                status_code=404, detail=f"Meal with id {meal.id} not found."
            )
        if current_user.is_admin == False:
            if current_user.id != meal_db.creator_id:
                raise HTTPException(
                    status_code=403, detail="Only creator or admin can update the meal."
                )
        meal_data = meal.model_dump(exclude_unset=True)
        meal_db.sqlmodel_update(meal_data)
        session.add(meal_db)
        session.commit()
        session.refresh(meal_db)
        updated_meals.append(meal_db)
    return updated_meals


@router.patch(
    "/{meal_id}",
    response_model=MealPublic,
    dependencies=[Depends(get_current_active_user)],
)
def update_meal(
    current_user: Annotated[User, Depends(get_current_active_user)],
    meal_id: int,
    meal_data: MealUpdate,
    session: SessionDep,
):
    meal_db = session.get(Meal, meal_id)
    if not meal_db:
        raise HTTPException(
            status_code=404, detail=f"Meal with id {meal_id} not found."
        )
    if current_user.is_admin == False:
        if current_user.id != meal_db.creator_id:
            raise HTTPException(
                status_code=403, detail="Only creator or admin can update the meal."
            )
    meal_data = meal_data.model_dump(exclude_unset=True)
    meal_db.sqlmodel_update(meal_data)
    session.add(meal_db)
    session.commit()
    session.refresh(meal_db)
    return meal_db
