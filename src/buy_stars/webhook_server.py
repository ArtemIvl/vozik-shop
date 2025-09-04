import uvicorn
from fastapi import FastAPI
from services.heleket_webhook import router as heleket_router
from api.external_routes import router as external_router

app = FastAPI()
app.include_router(heleket_router)
app.include_router(external_router)

if __name__ == "__main__":
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=8001)