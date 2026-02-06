# main.py (更新)
from fastapi import FastAPI
from app.api.api import api_router
from app.core.config import settings
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
load_dotenv()  # 加载环境变量
app = FastAPI(title=settings.PROJECT_NAME)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(api_router, prefix=settings.API_V1_STR)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8057)