import os

from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, create_engine

from app.dependencies import get_password_hash
from app.models import *

load_dotenv()

DEFAULT_ADMIN_LOGIN = os.environ["DEFAULT_ADMIN_LOGIN"]
DEFAULT_ADMIN_PASSWORD = os.environ["DEFAULT_ADMIN_PASSWORD"]

POSTGRES_USERNAME = os.environ["POSTGRES_USERNAME"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_DATABASE_NAME = os.environ["POSTGRES_DATABASE_NAME"]


POSTGRES_URL = f"postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DATABASE_NAME}"

engine = create_engine(POSTGRES_URL)

SQLModel.metadata.create_all(engine)
try:
    with Session(engine) as session:
        new_user = User.model_validate(
            {
                "username": DEFAULT_ADMIN_LOGIN,
                "hashed_password": get_password_hash(DEFAULT_ADMIN_PASSWORD),
                "is_admin": True,
            }
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
except IntegrityError as e:
    print("Couldn't create default admin. Error details below:")
    print(e)
