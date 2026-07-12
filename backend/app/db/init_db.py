from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.models.role import Role

async def seed_default_admin(db: AsyncSession):
    # Check if user with default admin email already exists
    stmt = select(User).where(User.email == settings.default_admin_email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        return
        
    # Look up the role_id for "fleet_manager"
    role_stmt = select(Role).where(Role.name == "fleet_manager")
    role_result = await db.execute(role_stmt)
    role = role_result.scalar_one_or_none()
    
    if not role:
        raise ValueError("Role 'fleet_manager' not found. Please ensure database is seeded.")
        
    # Create the default admin user
    default_admin = User(
        full_name="Default Admin",
        email=settings.default_admin_email,
        hashed_password=hash_password(settings.default_admin_password),
        role_id=role.id,
        is_active=True
    )
    
    db.add(default_admin)
    await db.commit()
