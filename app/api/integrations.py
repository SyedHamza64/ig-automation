from fastapi import APIRouter
from app.services import adspower_client

router = APIRouter()

@router.get("/adspower/status")
async def adspower_status():
    return await adspower_client.status()
