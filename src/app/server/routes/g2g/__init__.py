from fastapi import APIRouter

router = APIRouter(prefix="/g2g", tags=["G2G"])


@router.get("/")
async def hello_from_g2g() -> str:
    return "Hello from G2G webhook"
