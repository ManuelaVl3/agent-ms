from fastapi import APIRouter, File, UploadFile, HTTPException
from app.models import SpeciesIdentification, ErrorResponse
from app.services.gemini_service import GeminiService
import io

router = APIRouter(prefix="/species", tags=["species"])

gemini_service = GeminiService()

@router.post("/identify", response_model=SpeciesIdentification)
async def identify_species(file: UploadFile = File(...)):
    # Validar tipo de archivo
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=400, 
            detail="Solo se permiten archivos JPEG y PNG"
        )
    
    try:
        image_data = await file.read()
        
        if len(image_data) == 0:
            raise HTTPException(
                status_code=400,
                detail="El archivo está vacío"
            )
        
        result = gemini_service.identify_species(image_data)
        
        return SpeciesIdentification(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )
