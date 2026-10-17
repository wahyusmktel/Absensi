"""
Titik Masuk Utama Aplikasi FastAPI (PresensiPintar).
Mengonfigurasi Middleware keamanan, routing static CoreUI, template engine, dan database lifecycle.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.auth import router as api_auth_router
from app.core.config import settings
from app.core.init_db import init_db
from app.routers.web_routes import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Siklus hidup aplikasi: inisialisasi basis data dan super admin saat aplikasi dimulai.
    """
    print(f"🚀 Memulai {settings.APP_NAME} v{settings.APP_VERSION}...")
    try:
        await init_db()
        print("✅ Database terinisialisasi dengan sukses.")
    except Exception as e:
        print(f"❌ Gagal menginisialisasi database: {e}")
    yield
    print(f"🛑 Menghentikan {settings.APP_NAME}...")


# Inisialisasi Aplikasi FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Middleware CORS untuk keamanan request
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mounting folder Static Files CoreUI
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Registrasi Router
app.include_router(web_router)
app.include_router(api_auth_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
