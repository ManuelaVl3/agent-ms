from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, species

app = FastAPI(
    title="Agent-MS",
    description="API para identificar especies animales usando Gemini AI",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(health.router)
app.include_router(species.router)

@app.get("/")
async def root():
    """Endpoint raíz con información básica de la API"""
    return {
        "message": "Agent-MS API está funcionando",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "identify_species": "/species/identify"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
