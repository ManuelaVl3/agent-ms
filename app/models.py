from pydantic import BaseModel, Field
from typing import List, Optional

class SpeciesRecommendation(BaseModel):
    commonName: str = Field(..., description="Nombre común del animal")
    scientificName: str = Field(..., description="Nombre científico del animal")
    confidence: int = Field(..., ge=0, le=100, description="Porcentaje de confianza (0-100)")

class SpeciesIdentification(BaseModel):
    suggestions: List[SpeciesRecommendation] = Field(..., min_items=3, max_items=3, description="Lista de 3 recomendaciones de especies ordenadas por confianza")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Estado del servicio")
    service: str = Field(..., description="Nombre del servicio")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Descripción del error")
