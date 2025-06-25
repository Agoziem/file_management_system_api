from fastapi import APIRouter
from app.api.v1.notifications.routes import notification_router
from fastapi import APIRouter
from app.api.v1.auth.routes.oauth_routes import oauth_router
from app.api.v1.auth.routes.routes import auth_router
from app.api.v1.auth.routes.user_routes import user_router
from app.api.v1.auth.routes.two_factor_routes import twoFA_router
from app.core.templates import email_preview_router
from app.api.v1.files.routes import file_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["authentication"])
router.include_router(twoFA_router, prefix="/auth", tags=["authentication (2FA)"])
router.include_router(oauth_router, prefix="/auth", tags=["authentication (oauth)"])
router.include_router(user_router, prefix="/user", tags=["user"])


router.include_router(email_preview_router, prefix="/preview/email", tags=["email preview"])
router.include_router(
    notification_router, prefix="/notifications", tags=["notifications"])

router.include_router(file_router, prefix="/files", tags=["files"])
