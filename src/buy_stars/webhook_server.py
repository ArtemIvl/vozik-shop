import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.heleket_webhook import router as heleket_router
from api.external_routes import router as external_router
from db.session import init_models

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(heleket_router)
app.include_router(external_router)


@app.on_event("startup")
async def _startup() -> None:
    await init_models()

if __name__ == "__main__":
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=8001)
