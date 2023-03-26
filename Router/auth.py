import sys

sys.path.append("..")
from datetime import timedelta, datetime
from typing import Optional
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form
from starlette.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import models
from database import engine, SessionLocal
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["auth"], prefix="/auth")

templates = Jinja2Templates(directory="templates")

SECRET_KEY = 'ba6d8bd0f10fde517a01fd8e251f637e'
ALGORITHM = 'HS256'
ACCESS_EXPIRE_TOKEN_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(username: str, user_id: int,
                        expires_delta: Optional[timedelta] = None):
    encode = {"sub": username, "id": user_id}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user_exception():
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

async def get_current_user(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            await logout(request)
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=404, detail="error")

models.Base.metadata.create_all(bind=engine)

@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def login_page(request: Request, email: str = Form(...), password: str = Form(...),
                     db: Session = Depends(get_db)):
    try:
        foam_data = {"username": email, "password": password}
        response1 = RedirectResponse(url="/todo/all-todos", status_code=status.HTTP_302_FOUND)
        validate_user_cookie = await login_for_user_token(response=response1, form_data=foam_data, db=db)
        if not validate_user_cookie:
            msg = "Incorrect username or password"
            return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
        return response1
    except HTTPException:
        msg = "Unknown Error"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    msg = "Logout Successful"
    response = templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    response.delete_cookie(key="access_token")
    return response and RedirectResponse(url="/auth/login")
@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
async def register(request: Request, db: Session = Depends(get_db), email: str = Form(...),
                   username: str = Form(...), firstname: str = Form(...), lastname: str = Form(...),
                   password: str = Form(...), password2: str = Form(...)):
    validation1 = db.query(models.Users).filter(models.Users.user_name == username).first()
    validation2 = db.query(models.Users).filter(models.Users.email == email).first()

    if password != password2 or validation1 is not None or validation2 is not None:
        msg = "Invalid registration"
        return templates.TemplateResponse("register.html", {"request": request, "msg": msg})
    user_model = models.Users()
    user_model.user_name = username
    user_model.email = email
    user_model.first_name = firstname
    user_model.last_name = lastname
    hash_password = get_password_encrypted(password)
    user_model.hash_password = hash_password
    user_model.is_active = True
    db.add(user_model)
    db.commit()
    msg = "User successfully created"
    return templates.TemplateResponse("register.html", {"request": request, "msg": msg})


@router.get("/all_users")
async def all_users(db: Session = Depends(get_db)):
    user_model = db.query(models.Users).all()
    return user_model

def get_password_encrypted(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str, db):
    user = db.query(models.Users).filter(models.Users.user_name == username).first()
    if not user:
        return False
    if not verify_password(password, user.hash_password):
        return False
    return user

@router.post("/token")
async def login_for_user_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(),
                               db: Session = Depends(get_db)):
    user = authenticate_user(form_data.get("username"), form_data.get("password"), db)
    if not user:
        return False
    token = create_access_token(user.user_name, user.id, expires_delta=timedelta(minutes=60))
    response.set_cookie(key="access_token", value=token, httponly=True)
    return True

def success():
    raise HTTPException(status_code=status.HTTP_201_CREATED, detail="Successful")
