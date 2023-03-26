from typing import Optional

from fastapi import APIRouter, Depends
import sys
from pydantic import BaseModel
from sqlalchemy.orm import Session
import models
from TodoApp.Router.auth import get_current_user, get_user_exception
from TodoApp.database import SessionLocal

sys.path.append("..")
router = APIRouter(tags=["address"], prefix="/address", responses={404: {"description": "Not Found"}})


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class Address(BaseModel):
    address1: str
    city: str
    state: str
    apt_number: Optional[str]

@router.post("/create")
def create_address(address: Address, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()
    address_model = models.Address()
    address_model.address1 = address.address1
    address_model.city = address.city
    address_model.state = address.state
    address_model.apt_num = address.apt_number
    db.add(address_model)
    db.flush()
    user_model = db.query(models.Users).filter(models.Users.id == user.get("id")).first()
    user_model.address_id = address_model.id
    db.add(user_model)
    db.commit()

@router.get("/read")
def read_address(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_model = db.query(models.Address).filter(models.Address.id == user.get("address_id")).first()
    return user_model
