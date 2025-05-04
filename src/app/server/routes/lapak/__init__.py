from fastapi import APIRouter

router = APIRouter(prefix="/lapak", tags=["Lapak"])


@router.get("/")
async def hello_from_lapak() -> str:
    return "Hello from Lapak webhook"
