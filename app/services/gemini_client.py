import asyncio
import sys
import os
import json
import re

from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def setup_gemini():
    """Configurar Gemini directamente"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY no está configurada")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

def process_query_with_gemini(query: str):
    """Procesar consulta con Gemini directamente"""
    model = setup_gemini()
    
    prompt = f"""
    Eres un asistente especializado en consultas sobre observaciones de especies animales.
    
    Analiza esta consulta: "{query}"
    
    Puedes usar estas herramientas que devuelven observaciones completas con especies, ubicaciones e imágenes:
    1. GetAllObservations - Obtener todas las observaciones
    2. GetObservationsBySpecies - Buscar observaciones por nombre de especie (común o científico)
    3. GetObservationsByUser - Obtener observaciones de un usuario específico
    
    Si la consulta es sobre obtener todas las observaciones, responde: {{"tool": "GetAllObservations", "args": {{}}}}
    Si la consulta es sobre buscar observaciones por especie (nombre común o científico), responde: {{"tool": "GetObservationsBySpecies", "args": {{"name": "término de búsqueda"}}}}
    Si la consulta es sobre observaciones de un usuario específico, responde: {{"tool": "GetObservationsByUser", "args": {{"user_id": número}}}}
    
    Si la consulta NO es sobre observaciones de especies, responde: {{"error": "No puedo procesar esa solicitud. Mi función es ayudarte a consultar información sobre observaciones de especies animales."}}
    
    Responde ÚNICAMENTE con el JSON correspondiente.
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        cleaned_response = re.sub(r'```json\s*\n?(.*?)\n?```', r'\1', response_text, flags=re.DOTALL)
        cleaned_response = re.sub(r'```\s*\n?(.*?)\n?```', r'\1', cleaned_response, flags=re.DOTALL)
        
        result = json.loads(cleaned_response.strip())
        return result
        
    except Exception as e:
        return {"error": f"Error procesando consulta: {str(e)}"}

TOOL_NAME_MAP = {
    "GetAllObservations": "get_all_observations",
    "GetObservationsBySpecies": "get_observations_by_species",
    "GetObservationsByUser": "get_observations_by_user"
}

async def main(prompt):
    """Función principal que usa Gemini directamente"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "server_mcp.py")
    server_params = StdioServerParameters(command=sys.executable, args=[server_path])

    print("Cliente Observations MCP (usando Gemini directo) iniciado.")
    print(f"🔧 Usando servidor MCP en: {server_path}")

    async with stdio_client(server_params) as (read, write):
        print("✅ Cliente stdio conectado")
        async with ClientSession(read, write) as session:
            print("✅ Sesión MCP creada")
            await session.initialize()
            print("✅ Sesión MCP inicializada")
            
            try:
                print(f"🤖 Procesando consulta: {prompt}")
                
                gemini_response = process_query_with_gemini(prompt)
                print(f"🤖 Respuesta de Gemini: {gemini_response}")
                
                if "error" in gemini_response:
                    return gemini_response["error"]
                
                if "tool" in gemini_response:
                    tool_name = gemini_response["tool"]
                    tool_args = gemini_response.get("args", {})
                    
                    tool_name_on_server = TOOL_NAME_MAP.get(tool_name)
                    
                    if not tool_name_on_server:
                        print(f"❌ Error: Herramienta desconocida: {tool_name}")
                        return f"Herramienta desconocida: {tool_name}"

                    print(f"🔧 Llamando a herramienta: {tool_name_on_server} con args: {tool_args}")
                    
                    result = await session.call_tool(tool_name_on_server, arguments=tool_args)
                    print(f"📥 Resultado del servidor: {result}")

                    if result.isError:
                        print(f"❌ Error del servidor: {result.content}")
                        return f"Error del servidor: {result.content}"
                    elif result.structuredContent:
                        print("✅ Respuesta estructurada obtenida")
                        response_data = result.structuredContent
                        response_data["tool_used"] = tool_name_on_server
                        return response_data
                    else:
                        print("✅ Respuesta de texto obtenida")
                        return {"data": result.content, "tool_used": tool_name_on_server}
                else:
                    return "No se pudo procesar la consulta"
                    
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                return f"Error inesperado: {str(e)}"
