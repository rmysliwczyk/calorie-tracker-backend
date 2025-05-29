from collections import Counter
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import col, select

from app.dependencies import SessionDep, get_current_active_user
from app.models import (
    FoodCollection,
    FoodCollectionCreate,
    FoodCollectionPublic,
    FoodCollectionUpdate,
    FoodItem,
    Ingredient,
    User,
)

router = APIRouter(prefix="/foodcollections", tags=["foodcollections"])


def check_duplicate_ingredients(ingredients):
    food_item_ids = [ingredient.food_item_id for ingredient in ingredients]
    duplicates = [item for item, count in Counter(food_item_ids).items() if count > 1]
    if duplicates:
        raise HTTPException(
            status_code=400,
            detail=f"Duplicate food_item_id(s) in ingredients: {duplicates}",
        )


def calculate_nutritional_values(ingredients: list[Ingredient]) -> dict:
    nutritional_values = {
        "calories": Decimal(0),
        "fats": Decimal(0),
        "carbs": Decimal(0),
        "protein": Decimal(0),
        "total_weight": Decimal(0),
    }

    for ingredient in ingredients:
        multiplier = ingredient.amount / 100
        nutritional_values["calories"] += multiplier * ingredient.food_item.calories
        nutritional_values["fats"] += multiplier * ingredient.food_item.fats
        nutritional_values["carbs"] += multiplier * ingredient.food_item.carbs
        nutritional_values["protein"] += multiplier * ingredient.food_item.protein
        nutritional_values["total_weight"] += ingredient.amount

    total_weight = nutritional_values["total_weight"] or Decimal(
        1
    )  # avoid division by zero

    for key, value in nutritional_values.items():
        if key != "total_weight":
            nutritional_values[key] = round((value / total_weight) * 100, 2)

    return nutritional_values


@router.get(
    "/{food_collection_id}",
    response_model=FoodCollectionPublic,
    dependencies=[Depends(get_current_active_user)],
)
def read_food_collection(
    food_collection_id: int, session: SessionDep
) -> FoodCollectionPublic:
    food_collection = session.get(FoodCollection, food_collection_id)
    if not food_collection:
        raise HTTPException(status_code=404, detail="Food collection not found")
    return FoodCollectionPublic.model_validate(food_collection)


@router.post(
    "/",
    response_model=FoodCollectionPublic,
    dependencies=[Depends(get_current_active_user)],
)
def create_food_collection(
    current_user: Annotated[User, Depends(get_current_active_user)],
    food_collection_in: FoodCollectionCreate,
    session: SessionDep,
) -> FoodCollectionPublic:
    check_duplicate_ingredients(food_collection_in.ingredients)
    # This is just to generate the primary key id initialy
    new_food_collection = FoodCollection(name=food_collection_in.name, portion_weight=food_collection_in.portion_weight, creator_id=current_user.id)  # type: ignore
    session.add(new_food_collection)
    session.flush()

    # Here will be the ingredients and food items that go into the food collection
    ingredients = []

    for ingredient in food_collection_in.ingredients:
        food_item = session.get(FoodItem, ingredient.food_item_id)
        if not food_item:
            raise HTTPException(status_code=404, detail="Food item not found")
        new_ingredient = Ingredient(
            food_item_id=food_item.id,
            amount=ingredient.amount,
            food_collection_id=new_food_collection.id,
            food_item=food_item,
            food_collection=new_food_collection,
        )
        ingredients.append(new_ingredient)

    nutritional_values = calculate_nutritional_values(ingredients)

    new_food_collection.ingredients = ingredients
    new_food_collection.calories = nutritional_values["calories"]
    new_food_collection.fats = nutritional_values["fats"]
    new_food_collection.carbs = nutritional_values["carbs"]
    new_food_collection.protein = nutritional_values["protein"]
    new_food_collection.total_weight = nutritional_values["total_weight"]

    session.commit()
    return FoodCollectionPublic.model_validate(new_food_collection)


@router.get(
    "/",
    response_model=list[FoodCollectionPublic],
    dependencies=[Depends(get_current_active_user)],
)
def read_food_collections(
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
    name: str = "",
) -> list[FoodCollectionPublic]:
    query = select(FoodCollection)
    if name:
        query = query.where(col(FoodCollection.name).ilike(f"%{name}%"))
    collections = session.exec(query.offset(offset).limit(limit)).all()
    return [FoodCollectionPublic.model_validate(fc) for fc in collections]


@router.patch(
    "/{food_collection_id}",
    response_model=FoodCollectionPublic,
    dependencies=[Depends(get_current_active_user)],
)
def update_food_collection(
    current_user: Annotated[User, Depends(get_current_active_user)],
    food_collection_id: int,
    food_collection_data: FoodCollectionUpdate,
    session: SessionDep,
):
    food_collection = session.get(FoodCollection, food_collection_id)
    if not food_collection:
        raise HTTPException(status_code=404, detail="Food collection not found")
    if current_user.is_admin is False and food_collection.creator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only creator or admin can update food collection"
        )

    update_data = food_collection_data.model_dump(exclude_unset=True)
    if (
        hasattr(food_collection_data, "ingredients")
        and food_collection_data.ingredients != None
    ):
        check_duplicate_ingredients(food_collection_data.ingredients)
        # Remove old ingredients
        food_collection.ingredients.clear()
        session.flush()
        # Add new ingredients
        ingredients = []
        for ingredient in food_collection_data.ingredients:
            food_item = session.get(FoodItem, ingredient.food_item_id)
            if not food_item:
                raise HTTPException(status_code=404, detail="Food item not found")
            new_ingredient = Ingredient(
                food_item_id=food_item.id,
                amount=ingredient.amount,
                food_collection_id=food_collection.id,
                food_item=food_item,
                food_collection=food_collection,
            )
            ingredients.append(new_ingredient)
        food_collection.ingredients = ingredients
        nutritional_values = calculate_nutritional_values(ingredients)
        food_collection.calories = nutritional_values["calories"]
        food_collection.fats = nutritional_values["fats"]
        food_collection.carbs = nutritional_values["carbs"]
        food_collection.protein = nutritional_values["protein"]
        food_collection.total_weight = nutritional_values["total_weight"]

    # Update other fields
    for field in ["name", "portion_weight"]:
        if field in update_data:
            setattr(food_collection, field, update_data[field])

    session.add(food_collection)
    session.commit()
    session.refresh(food_collection)
    return FoodCollectionPublic.model_validate(food_collection)


@router.delete(
    "/{food_collection_id}",
    dependencies=[Depends(get_current_active_user)],
)
def delete_food_collection(
    current_user: Annotated[User, Depends(get_current_active_user)],
    food_collection_id: int,
    session: SessionDep,
):
    food_collection = session.get(FoodCollection, food_collection_id)
    if not food_collection:
        raise HTTPException(status_code=404, detail="Food collection not found")
    if current_user.is_admin is False and food_collection.creator_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only creator or admin can delete food collection"
        )
    session.delete(food_collection)
    session.commit()
    return {"ok": True}
