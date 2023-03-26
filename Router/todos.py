import sys

from starlette import status
from starlette.responses import RedirectResponse

sys.path.append("...")
from fastapi import Depends, APIRouter, Request, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
import models
from database import engine, SessionLocal
from .auth import get_current_user, get_password_encrypted, verify_password
from enum import Enum
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["todos"], prefix="/todo")
models.Base.metadata.create_all(bind=engine)


class Activities(str, Enum):
    fun = "Fun"
    high_priority = "High_Priority"
    game = "Games"


templates = Jinja2Templates(directory="templates")


class Todo(BaseModel):
    title: str
    description: str
    priority: int
    complete: bool


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get("/all-todos", response_class=HTMLResponse)
async def read_all_todos(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    todos_model = db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()

    return templates.TemplateResponse("home.html", {"request": request, "todos": todos_model, "user": user})


@router.get("/add-todo", response_class=HTMLResponse)
async def create_todo(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("add-todo.html", {"request": request, "user": user})


@router.post("/add-todo", response_class=HTMLResponse)
async def create_todo(request: Request, title: str = Form(...), description: str = Form(...), priority: int = Form(...),
                      db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    user_model = models.Todos()
    user_model.title = title
    user_model.description = description
    user_model.priority = priority
    user_model.complete = False
    user_model.owner_id = user.get("id")
    user_model.activity_type = "None"
    db.add(user_model)
    db.commit()
    return RedirectResponse(url="/todo/all-todos", status_code=status.HTTP_302_FOUND)


@router.get("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo_model, "user": user})


@router.get("/change_password", response_class=HTMLResponse)
async def change_password(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("change_password.html", {"request": request})


@router.post("/change_password", response_class=HTMLResponse)
async def change_password(request: Request, username: str = Form(...), password: str = Form(...),
                          new_password: str = Form(...), db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    password_model = db.query(models.Users).filter(models.Users.id == user.get("id")).first()
    if username == password_model.user_name and verify_password(password, password_model.hash_password):
        password_model.hash_password = get_password_encrypted(new_password)
        db.add(password_model)
        db.commit()
        msg = "success"
        return RedirectResponse(url="/todo/all-todos", status_code=status.HTTP_302_FOUND)
    msg = "failed"
    return templates.TemplateResponse("change_password.html", {"request": request, "msg": msg})


@router.post("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int, title: str = Form(...), description: str = Form(...),
                    priority: int = Form(...), db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    todo.title = title
    todo.description = description
    todo.priority = priority
    todo.complete = False
    db.add(todo)
    db.commit()
    return RedirectResponse(url="/todo/all-todos", status_code=status.HTTP_302_FOUND)


@router.get("/delete/{todo_id}")
async def delete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(
        models.Todos.owner_id == user.get("id")).first()

    if todo is None:
        return RedirectResponse(url="/todo/all-todos", status_code=status.HTTP_302_FOUND)
    db.query(models.Todos).filter(models.Todos.id == todo_id).delete()
    db.commit()
    return RedirectResponse(url="/todo/all-todos", status_code=status.HTTP_302_FOUND)


@router.get("/complete/{todo_id}", response_class=HTMLResponse)
async def complete(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    todo.complete = not todo.complete

    db.add(todo)
    db.commit()
    return RedirectResponse(url="/todo/all-todos", status_code=status.HTTP_302_FOUND)
