from uuid import UUID
from fastapi import Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    result = await db.execute(select(User).options(selectinload(User.role)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_roles(*roles: str):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.name not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of roles: {', '.join(roles)}",
            )
        return user
    return Depends(checker)


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.limit = page_size
