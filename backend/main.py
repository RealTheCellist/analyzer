import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import stocks, analysis, news, board
from services.data_fetcher import init_stock_cache
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_stock_cache()
    yield


app = FastAPI(title="Stock Analyzer API", lifespan=lifespan)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(stocks.router, prefix="/api/stocks")
app.include_router(analysis.router, prefix="/api/analysis")
app.include_router(news.router, prefix="/api/news")
app.include_router(board.router, prefix="/api/board")
