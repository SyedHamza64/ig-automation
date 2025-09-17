import sys, asyncio

# Must come before Playwright or any FastAPI router that uses asyncio subprocess
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.accounts import router as accounts_router
from app.api.templates import router as templates_router
from app.api.targets import router as targets_router
from app.api.auth import router as auth_router
from app.api.integrations import router as integrations_router
from app.api.profiles import router as profiles_router
from app.api.engine import router as engine_router
from .api.actions import router as actions_router

app = FastAPI(title="IG Automation API")
app.include_router(health_router,      prefix="/health",       tags=["health"])
app.include_router(auth_router)
app.include_router(integrations_router, prefix="/integrations", tags=["integrations"])
app.include_router(profiles_router,     prefix="/profiles",     tags=["profiles"])
app.include_router(accounts_router,    prefix="/accounts",     tags=["accounts"])
app.include_router(templates_router,   prefix="/templates",    tags=["templates"])
app.include_router(targets_router,     prefix="/targets",      tags=["targets"])
app.include_router(engine_router,      prefix="/engine",       tags=["engine"])
app.include_router(actions_router)
