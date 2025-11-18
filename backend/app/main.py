from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.modules.users.router import router as users_router
from app.modules.emails.router import router as emails_router
from app.modules.subscriptions.router import router as subscriptions_router
from app.modules.sends.router import router as sends_router
from app.modules.sends.router import router as sends_router


# =========================
#  Initialisation de l'app
# =========================
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# =========================
#  Configuration CORS
# =========================
# Liste des origines autorisées (depuis settings)
origins = [str(origin).rstrip('/') for origin in settings.BACKEND_CORS_ORIGINS]
print("CORS origins:", origins)

# IMPORTANT: lorsque allow_credentials=True, on ne peut PAS utiliser "*".
# Il faut lister explicitement les origines autorisées.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporaire pour debug
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
#  Inclusion des routes
# =========================
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(emails_router, prefix=settings.API_V1_STR)
app.include_router(subscriptions_router, prefix=settings.API_V1_STR)
app.include_router(sends_router, prefix=settings.API_V1_STR)
app.include_router(sends_router, prefix=settings.API_V1_STR)

# =========================
#  Route principale
# =========================
@app.get("/")
def root():
    return {"message": "🚀 Welcome to SendBulletin API — FastAPI backend is running!"}

# =========================
#  Lancement du serveur
# =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
