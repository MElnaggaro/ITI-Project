"""Version-neutral route composition for the platform API."""

from fastapi import APIRouter

from api.routes import (
    auth,
    chat,
    conversations,
    database_connections,
    database_schema,
    files,
    health,
    knowledge_bases,
    messages,
    permissions,
    roles,
    tenants,
    users,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(roles.router)
api_router.include_router(tenants.router)
api_router.include_router(users.router)
api_router.include_router(database_connections.router)
api_router.include_router(database_schema.router)
api_router.include_router(files.router)
api_router.include_router(knowledge_bases.router)
api_router.include_router(conversations.router)
api_router.include_router(messages.router)
api_router.include_router(chat.router)
api_router.include_router(permissions.router)
