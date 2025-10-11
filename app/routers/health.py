from fastapi import APIRouter
from app.models import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])

@router.get("", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="agent-ms"
    )
