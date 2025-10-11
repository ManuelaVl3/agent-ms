import google.generativeai as genai
import os
import json
import re
from typing import Dict, Any
from PIL import Image
import io

class GeminiService:
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no está configurada")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def identify_species(self, image_data: bytes) -> Dict[str, Any]:
        try:
            # Procesar la imagen
            image = Image.open(io.BytesIO(image_data))
            
            prompt = """Identifica la especie animal en la imagen. Responde ÚNICAMENTE en formato JSON con exactamente 3 recomendaciones ordenadas por confianza.

IMPORTANTE: Asigna porcentajes de confianza reales basados en qué tan seguro estás de cada identificación.

{
    "recomendaciones": [
        {
            "nombre_comun": "nombre común en español",
            "nombre_cientifico": "Género especie",
            "confianza": [porcentaje real de confianza 0-100]
        },
        {
            "nombre_comun": "segunda opción más probable",
            "nombre_cientifico": "Género especie", 
            "confianza": [porcentaje real de confianza 0-100]
        },
        {
            "nombre_comun": "tercera opción más probable",
            "nombre_cientifico": "Género especie",
            "confianza": [porcentaje real de confianza 0-100]
        }
    ]
}

Si no puedes identificar la especie: {"error": "No se pudo identificar la especie"}"""
            
            # Generar respuesta con Gemini
            response = self.model.generate_content([prompt, image])
            response_text = response.text.strip()
            
            # Procesar la respuesta
            return self._parse_response(response_text)
            
        except Exception as e:
            raise Exception(f"Error al procesar la imagen con Gemini: {str(e)}")
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        cleaned_response = self._clean_markdown_json(response_text)
        
        try:
            result = json.loads(cleaned_response)
            
            if "error" in result:
                raise ValueError("No se pudo identificar la especie")
            
            if "recomendaciones" not in result:
                raise ValueError("Formato de respuesta inválido")
            
            return result
            
        except json.JSONDecodeError:
            if "error" in cleaned_response.lower():
                raise ValueError("No se pudo identificar la especie")
            raise ValueError("Error al procesar la respuesta de la IA")
    
    
    def _clean_markdown_json(self, text: str) -> str:
        """Limpia bloques de código markdown de la respuesta"""
        # Remover bloques de código markdown
        cleaned = re.sub(r'```json\s*\n?(.*?)\n?```', r'\1', text, flags=re.DOTALL)
        cleaned = re.sub(r'```\s*\n?(.*?)\n?```', r'\1', cleaned, flags=re.DOTALL)
        return cleaned.strip()
