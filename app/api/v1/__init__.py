from fastapi import APIRouter

from app.api.v1 import auth, users, organizations, products, sections, terminal_groups, orders, groups, files


api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(groups.router, prefix="/groups", tags=["groups"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(terminal_groups.router, prefix="/terminal-groups", tags=["terminal-groups"])
api_router.include_router(sections.router, prefix="/sections", tags=["sections"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(files.router, prefix="/files", tags=["files"])

