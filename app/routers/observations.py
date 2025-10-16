from fastapi import APIRouter, HTTPException
from app.services.gemini_client import main
import asyncio

router = APIRouter(prefix="/observations", tags=["observations"])

@router.post("/query")
async def leer_consulta(request_data: dict):
    """
    Endpoint para consultar información sobre observaciones de especies animales.
    
    Utiliza Gemini AI para interpretar consultas en lenguaje natural y devuelve
    información estructurada de la base de datos observations_db.
    
    Ejemplos de consultas válidas:
    - "dame todas las especies"
    - "busca especies que contengan 'águila'"
    - "muéstrame todos los registros"
    - "obtén registros del usuario 123"
    - "dame registros de la especie 5"
    - "muéstrame todas las ubicaciones"
    """
    
    if not request_data or "consulta" not in request_data:
        raise HTTPException(
            status_code=400,
            detail="El cuerpo de la solicitud debe ser un JSON con la clave 'consulta'"
        )
    
    try:
        resultado = await main(request_data.get("consulta"))
        return {"data": resultado}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando consulta: {str(e)}"
        )

@router.get("/")
async def observations_info():
    """
    Información sobre el endpoint de observaciones
    """
    return {
        "message": "Endpoint de consultas de observaciones de especies animales",
        "description": "Utiliza Gemini AI para interpretar consultas en lenguaje natural sobre observaciones",
        "endpoint": "POST /observations/query",
        "examples": [
            "dame todas las especies",
            "busca especies que contengan 'águila'",
            "muéstrame todos los registros",
            "obtén registros del usuario 123",
            "dame registros de la especie 5",
            "muéstrame todas las ubicaciones"
        ]
    }
