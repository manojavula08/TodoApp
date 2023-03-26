from fastapi import APIRouter, Depends, HTTPException, status
import sys
import models
from pydantic import BaseModel
from sqlalchemy.orm import Session
from Router import auth
from database import SessionLocal, engine

sys.path.append("..")

router = APIRouter(tags=["users"], prefix="/users")
models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class User_verify(BaseModel):
    user_name: str
    password: str
    new_password: str


@router.get("/all_users")
async def get_all_users(db: Session = Depends(get_db)):
    user = db.query(models.Users).all()
    return user


@router.post("/get_Id_query")
async def get_by_Id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    return user


@router.post("/get_Id_path/{user_id}")
async def get_by_Id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    return user


@router.put("/change_password")
async def change_password(user_verification: User_verify, user: dict = Depends(auth.get_current_user),
                          db: Session = Depends(get_db)):
    if user is None:
        return auth.get_user_exception()
    user1 = db.query(models.Users).filter(models.Users.id == user.get("id")).first()
    if user1.user_name == user_verification.user_name and auth.verify_password(user_verification.password,
                                                                               user1.hash_password):
        user1.hash_password = auth.get_password_encrypted(user_verification.new_password)
        db.add(user1)
        db.commit()
        return HTTPException(status_code=status.HTTP_200_OK, detail="Updated")
    return HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="User not changed")


@router.delete("/delete")
async def delete_user(user: dict = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    user_model = db.query(models.Users).filter(models.Users.id == user.get("id")).first()
    if user_model is None:
        raise auth.HTTPException
    db.query(models.Users).filter(models.Users.id == user.get("id")).delete()
    db.commit()
    return HTTPException(status_code=status.HTTP_200_OK, detail="User Deleted.")
