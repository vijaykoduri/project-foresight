from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import Role, User
from app.schemas.auth import RoleResponse, UserAdminUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    return db.query(User).options(joinedload(User.role)).all()


@router.get("/roles", response_model=list[RoleResponse])
def list_roles(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    return db.query(Role).all()


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    user = db.query(User).options(joinedload(User.role)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id and data.is_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
