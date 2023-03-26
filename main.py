from fastapi import FastAPI, status
from starlette.staticfiles import StaticFiles

import models
from database import engine
from Router import auth, todos
from starlette.responses import RedirectResponse


app = FastAPI()

@app.get("/")
async def redirect():
    return RedirectResponse(url="/todo/all-todos", status_code=status.HTTP_302_FOUND)

app.include_router(auth.router)
app.include_router(todos.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
models.Base.metadata.create_all(bind=engine)




