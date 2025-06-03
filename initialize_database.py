import os
import sys

from dotenv import load_dotenv
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, create_engine

from app.dependencies import get_password_hash
from app.models import *

load_dotenv()

DEFAULT_ADMIN_LOGIN = os.environ["DEFAULT_ADMIN_LOGIN"]
DEFAULT_ADMIN_PASSWORD = os.environ["DEFAULT_ADMIN_PASSWORD"]
DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)

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
    if isinstance(e.orig, UniqueViolation):
        print("No need to create default admin. It already exists!")
        sys.exit(0)
    print("Couldn't create default admin. Error details below:")
    print(e)
    sys.exit(1)
