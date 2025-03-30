import uvicorn
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from src.logger_config import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.tasks.cleanup_links import delete_expired_links, delete_unused_links

from fastapi import FastAPI
from src.auth.router import router as router_auth
from src.links.router import router as router_links


scheduler = AsyncIOScheduler()  # Глобальный шедулер


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Добавление задач в шедулер
    scheduler.add_job(
        delete_expired_links,
        trigger="interval",
        minutes=5,
        id="cleanup_expired_links",
        replace_existing=True
    )
    scheduler.add_job(
        delete_unused_links,
        trigger="interval",
        hours=12,
        id="cleanup_unused_links",
        replace_existing=True
    )
    scheduler.start()
    logger.info("The task scheduler is running")
    
    try:
        yield
    finally:
        scheduler.shutdown()
        logger.info("The task scheduler is stopped")


app = FastAPI(title="Short Link Service", lifespan=lifespan)

app.include_router(router_auth, prefix="/auth", tags=["auth"])
app.include_router(router_links, prefix="/links", tags=["links"])

@app.get("/")
def read_root():
    return {"message": "Hello from Short Links Service!"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", reload=True, host="0.0.0.0", log_level="debug")