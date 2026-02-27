from fastapi import APIRouter, Depends

from app.api.v1 import auth, users, organizations, products, sections, terminal_groups, orders, groups, files
from app.api.dependencies import get_current_active_user


api_router = APIRouter()

# Authentication routes (unprotected)
api_router.include_router(auth.public_router, prefix="/auth", tags=["authentication"])

# Protected routes (require valid token)
protected_router = APIRouter(dependencies=[Depends(get_current_active_user)])

protected_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
protected_router.include_router(users.router, prefix="/users", tags=["users"])
protected_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
protected_router.include_router(groups.router, prefix="/groups", tags=["groups"])
protected_router.include_router(products.router, prefix="/products", tags=["products"])
protected_router.include_router(terminal_groups.router, prefix="/terminal-groups", tags=["terminal-groups"])
protected_router.include_router(sections.router, prefix="/sections", tags=["sections"])
protected_router.include_router(orders.router, prefix="/orders", tags=["orders"])
protected_router.include_router(files.router, prefix="/files", tags=["files"])

api_router.include_router(protected_router)

