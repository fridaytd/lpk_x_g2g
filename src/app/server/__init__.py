from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import config
from .routes.g2g.router import router as g2g_router
from .routes import lapak

app = FastAPI(title=config.APP_TITLE)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(g2g_router)
app.include_router(lapak.router)


@app.get("/")
async def hello() -> str:
    return f"Hello from {config.APP_TITLE}"
