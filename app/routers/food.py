from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import col, select

from app.dependencies import SessionDep, get_current_active_user
from app.models import (
    FoodCollection,
    FoodCollectionPublic,
    FoodItem,
    FoodItemPublic,
)

router = APIRouter(prefix="/food", tags=["food"])


@router.get(
    "/combined/",
    response_model=list[dict[str, Any]],
    dependencies=[Depends(get_current_active_user)],
)
def read_food_collections_and_items(
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
    name: str = "",
    barcode: str = "",
) -> list[dict[str, Any]]:
    # Query FoodCollections
    collection_query = select(FoodCollection)
    if name:
        collection_query = collection_query.where(
            col(FoodCollection.name).ilike(f"%{name}%")
        )
    collections = session.exec(collection_query.offset(offset).limit(limit)).all()
    collections_result = [
        {"type": "collection", **FoodCollectionPublic.model_validate(fc).model_dump()}
        for fc in collections
    ]

    # Query FoodItems
    item_query = select(FoodItem)
    if name:
        item_query = item_query.where(col(FoodItem.name).ilike(f"%{name}%"))
    if barcode:
        item_query = item_query.where(col(FoodItem.barcode).ilike(f"%{barcode}%"))
    items = session.exec(item_query.offset(offset).limit(limit)).all()
    items_result = [
        {"type": "item", **FoodItemPublic.model_validate(item).model_dump()}
        for item in items
    ]

    # Combine and return
    return collections_result + items_result
