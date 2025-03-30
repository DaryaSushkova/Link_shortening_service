from fastapi import APIRouter
from src.auth.manager import auth_router, register_router


router = APIRouter()
router.include_router(auth_router, prefix="/jwt", tags=["auth"])
router.include_router(register_router, prefix="", tags=["auth"])