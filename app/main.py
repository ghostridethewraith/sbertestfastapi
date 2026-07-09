from fastapi import FastAPI

from app.routes import router

app = FastAPI(title="IP Service")
app.include_router(router)
