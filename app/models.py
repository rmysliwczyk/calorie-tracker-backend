import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

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


# FoodItem model


class FoodItemBase(SQLModel):
    name: str = Field(max_length=256)
    brand: Optional[str] = Field(default="", max_length=64)
    calories: Decimal = Field(default=0.0, ge=0, decimal_places=2)
    fats: Decimal = Field(default=0.0, ge=0, decimal_places=2)
    carbs: Decimal = Field(default=0.0, ge=0, decimal_places=2)
    protein: Decimal = Field(default=0.0, ge=0, decimal_places=2)
    portion_weight: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    barcode: str = Field(default="", max_length=64)


class FoodItem(FoodItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    edit_locked: bool = Field(default=True)
    creator_id: int = Field(foreign_key="user.id")
    meals: "Meal" = Relationship(cascade_delete=True)

class FoodItemPublic(SQLModel):
    id: int
    name: str
    brand: Optional[str]
    calories: Decimal
    fats: Decimal
    carbs: Decimal
    protein: Decimal
    portion_weight: Optional[Decimal]
    barcode: Optional[str]
    creator_id: int


class FoodItemCreate(FoodItemBase):
    pass


class FoodItemUpdate(SQLModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    calories: Optional[Decimal] = Field(default=0.0, ge=0, decimal_places=2)
    fats: Optional[Decimal] = Field(default=0.0, ge=0, decimal_places=2)
    carbs: Optional[Decimal] = Field(default=0.0, ge=0, decimal_places=2)
    protein: Optional[Decimal] = Field(default=0.0, ge=0, decimal_places=2)
    portion_weight: Optional[Decimal] = Field(default=0.0, ge=0, decimal_places=2)
    barcode: Optional[str] = Field(default="", max_length=64)
    edit_locked: bool = True


## Meal model

class MealBase(SQLModel):
    calories: Decimal = Field(default=0.0, ge=0, decimal_places=2)
    food_amount: Decimal = Field(default=0.0, ge=0, decimal_places=2)
    food_item_id: Optional[int] = Field(
        default=None, foreign_key="fooditem.id", ondelete="CASCADE"
    )
    created_at: date = Field(default_factory=datetime.now().date)
    is_shared: bool = Field(default=False)
    mealtime_id: int = Field(
        default=1, le=5
    )  # This could later on be exchanged for a foreign key to a custom mealtime model


class Meal(MealBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    food_item: "FoodItem" = Relationship(back_populates="meals")
    creator_id: int = Field(foreign_key="user.id")


class MealCreate(MealBase):
    pass


class MealPublic(MealBase):
    id: int
    food_item: Optional["FoodItemPublic"]


class MealUpdate(SQLModel):
    id: Optional[int] = None
    calories: Optional[Decimal] = None
    food_amount: Optional[Decimal] = Field(default=0, ge=0, decimal_places=2)
    food_item_id: Optional[int] = Field(
        default=None, foreign_key="fooditem.id", ondelete="CASCADE"
    )
    created_at: Optional[date] = Field(default_factory=datetime.now().date)
    is_shared: Optional[bool] = Field(default=False)
    mealtime_id: Optional[int] = Field(default=1, le=5)
