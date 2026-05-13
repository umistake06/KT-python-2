from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from . import models, database, auth

router = APIRouter(prefix="", tags=["posts"])
templates = Jinja2Templates(directory="templates")

def get_current_user(request: Request, db: Session = Depends(database.get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER, 
            headers={"Location": "/login"}
        )
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.get("/")
def index(request: Request, db: Session = Depends(database.get_db)):
    posts = db.query(models.Post).order_by(models.Post.created_at.desc()).all()
    current_user = None
    if "user_id" in request.session:
        current_user = db.query(models.User).filter(models.User.id == request.session["user_id"]).first()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "posts": posts,
            "current_user": current_user
        }
    )

@router.get("/posts/new")
def create_post_page(request: Request, current_user: models.User = Depends(get_current_user)):
    # Зависимость get_current_user уже проверила авторизацию
    return templates.TemplateResponse(
        request=request,
        name="create_post.html",
        context={"current_user": current_user}
    )

@router.post("/posts/new")
def create_post_submit(
    request: Request,
    title: str = Form(...),
    body: str = Form(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    new_post = models.Post(
        title=title,
        body=body,
        author_id=current_user.id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return RedirectResponse(url="/", status_code=303)

@router.get("/posts/{post_id}")
def view_post(request: Request, post_id: int, db: Session = Depends(database.get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    current_user = None
    if "user_id" in request.session:
        current_user = db.query(models.User).filter(models.User.id == request.session["user_id"]).first()
    
    return templates.TemplateResponse(
        request=request,
        name="view_post.html",
        context={
            "post": post,
            "current_user": current_user
        }
    )

@router.get("/posts/{post_id}/edit")
def edit_post_page(
    request: Request, 
    post_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к редактированию этого поста")

    return templates.TemplateResponse(
        request=request,
        name="edit_post.html",
        context={
            "post": post,
            "current_user": current_user
        }
    )

@router.post("/posts/{post_id}/edit")
def edit_post_submit(
    request: Request,
    post_id: int,
    title: str = Form(...),
    body: str = Form(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")

    post.title = title
    post.body = body
    db.commit()
    return RedirectResponse(url=f"/posts/{post_id}", status_code=303)

@router.post("/posts/{post_id}/delete")
def delete_post(
    request: Request,
    post_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")

    db.delete(post)
    db.commit()
    return RedirectResponse(url="/", status_code=303)