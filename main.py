from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from .routers_auth import router as auth_router
from .routers_post import router as post_router
from . import database, models

app = FastAPI(title="Блог с авторизацией | КП ПАЙТОН")

app.add_middleware(SessionMiddleware, secret_key="super-secret-key-for-kp-python-blog-2026-change-me!")

app.include_router(auth_router)
app.include_router(post_router)

@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=database.engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)