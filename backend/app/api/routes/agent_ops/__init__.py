from fastapi import APIRouter

from app.api.routes.agent_ops import runs

router = APIRouter()
router.include_router(runs.router)