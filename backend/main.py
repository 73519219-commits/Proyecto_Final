from app.core.config import settings
from app.main import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.api_host, port=settings.api_port, reload=True)
