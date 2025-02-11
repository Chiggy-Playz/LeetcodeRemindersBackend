from app.main import app
from app.settings import settings
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        app=app,
        port=settings.port,
        host="0.0.0.0",
    )
