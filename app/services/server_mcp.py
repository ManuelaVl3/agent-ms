import asyncio
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional, Dict, Any
from datetime import datetime

import asyncpg
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context

class Species(BaseModel):
    id: int
    common_name: str
    scientific_name: str
    created_at: datetime
    updated_at: datetime

class Location(BaseModel):
    id: int
    longitude: float
    latitude: float
    location: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class Register(BaseModel):
    id: int
    user_id: int
    species_id: int
    location_id: int
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class RegisterImage(BaseModel):
    id: int
    register_id: int
    image_url: str
    image_order: int = 0
    created_at: datetime

class RegisterWithDetails(BaseModel):
    id: int
    user_id: int
    species: Species
    location: Location
    description: Optional[str] = None
    images: List[RegisterImage] = []
    created_at: datetime
    updated_at: datetime

@dataclass
class AppContext:
    db_pool: asyncpg.Pool

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    print("🔌 Conectando a la base de datos PostgreSQL observations_db...")
    print(f"   Host: 127.0.0.1:5432")
    print(f"   Database: observations_db")
    print(f"   User: postgres")
    
    try:
        pool = await asyncpg.create_pool(
            user="postgres",
            password="1234",
            database="observations_db",
            host="127.0.0.1",
            port=5432,
        )
        print("✅ Pool de conexiones a PostgreSQL observations_db creado.")
        yield AppContext(db_pool=pool)
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        raise
    finally:
        if 'pool' in locals() and pool:
            await pool.close()
            print("🔌 Pool de conexiones a PostgreSQL observations_db cerrado.")

mcp = FastMCP("ObservationsServer", lifespan=app_lifespan)

@mcp.tool()
async def get_all_observations(ctx: Context) -> List[RegisterWithDetails]:
    """
    Devuelve todas las observaciones con detalles completos.
    """
    print("🔍 Ejecutando get_all_observations...")
    pool: asyncpg.Pool = ctx.request_context.lifespan_context.db_pool
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                r.id, r.user_id, r.species_id, r.location_id, r.description, r.created_at, r.updated_at,
                s.common_name, s.scientific_name, s.created_at as species_created_at, s.updated_at as species_updated_at,
                l.longitude, l.latitude, l.location as location_name, l.created_at as location_created_at, l.updated_at as location_updated_at
            FROM registers r
            JOIN species s ON r.species_id = s.id
            JOIN locations l ON r.location_id = l.id
            ORDER BY r.created_at DESC
        """)
        
        result = []
        for row in rows:
            # Obtener imágenes para este registro
            image_rows = await conn.fetch("SELECT * FROM register_images WHERE register_id = $1 ORDER BY image_order", row['id'])
            images = [RegisterImage(**img_row) for img_row in image_rows]
            
            # Crear objeto con detalles completos
            register_detail = RegisterWithDetails(
                id=row['id'],
                user_id=row['user_id'],
                species=Species(
                    id=row['species_id'],
                    common_name=row['common_name'],
                    scientific_name=row['scientific_name'],
                    created_at=row['species_created_at'],
                    updated_at=row['species_updated_at']
                ),
                location=Location(
                    id=row['location_id'],
                    longitude=row['longitude'],
                    latitude=row['latitude'],
                    location=row['location_name'],
                    created_at=row['location_created_at'],
                    updated_at=row['location_updated_at']
                ),
                description=row['description'],
                images=images,
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            result.append(register_detail)
        
        print(f"📊 Encontradas {len(result)} observaciones totales")
        return result

@mcp.tool()
async def get_observations_by_species(name: str, ctx: Context) -> List[RegisterWithDetails]:
    """
    Devuelve todas las observaciones de una especie específica (por nombre común o científico).
    """
    print(f"🔍 Ejecutando get_observations_by_species con nombre: {name}")
    pool: asyncpg.Pool = ctx.request_context.lifespan_context.db_pool
    async with pool.acquire() as conn:
        print(f"📊 Ejecutando query para especies que contengan: {name}")
        
        rows = await conn.fetch("""
        SELECT 
            r.id, r.user_id, r.species_id, r.location_id, r.description, 
            r.created_at, r.updated_at,
            s.common_name, s.scientific_name, 
            s.created_at AS species_created_at, s.updated_at AS species_updated_at,
            l.longitude, l.latitude, l.location AS location_name,
            l.created_at AS location_created_at, l.updated_at AS location_updated_at
        FROM registers r
        JOIN species s ON r.species_id = s.id
        JOIN locations l ON r.location_id = l.id
        WHERE 
            unaccent(lower(s.common_name)) LIKE unaccent(lower($1))
            OR unaccent(lower(s.scientific_name)) LIKE unaccent(lower($1))
        ORDER BY r.created_at DESC;
        """, f"%{name}%")
        
        result = []
        for row in rows:
            image_rows = await conn.fetch("SELECT * FROM register_images WHERE register_id = $1 ORDER BY image_order", row['id'])
            images = [RegisterImage(**img_row) for img_row in image_rows]
            
            register_detail = RegisterWithDetails(
                id=row['id'],
                user_id=row['user_id'],
                species=Species(
                    id=row['species_id'],
                    common_name=row['common_name'],
                    scientific_name=row['scientific_name'],
                    created_at=row['species_created_at'],
                    updated_at=row['species_updated_at']
                ),
                location=Location(
                    id=row['location_id'],
                    longitude=row['longitude'],
                    latitude=row['latitude'],
                    location=row['location_name'],
                    created_at=row['location_created_at'],
                    updated_at=row['location_updated_at']
                ),
                description=row['description'],
                images=images,
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            result.append(register_detail)
        
        print(f"📊 Encontradas {len(result)} observaciones para especies que contienen '{name}'")
        return result

@mcp.tool()
async def get_observations_by_user(user_id: int, ctx: Context) -> List[RegisterWithDetails]:
    """
    Devuelve todas las observaciones de un usuario específico.
    """
    print(f"🔍 Ejecutando get_observations_by_user con user_id: {user_id}")
    pool: asyncpg.Pool = ctx.request_context.lifespan_context.db_pool
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                r.id, r.user_id, r.species_id, r.location_id, r.description, r.created_at, r.updated_at,
                s.common_name, s.scientific_name, s.created_at as species_created_at, s.updated_at as species_updated_at,
                l.longitude, l.latitude, l.location as location_name, l.created_at as location_created_at, l.updated_at as location_updated_at
            FROM registers r
            JOIN species s ON r.species_id = s.id
            JOIN locations l ON r.location_id = l.id
            WHERE r.user_id = $1
            ORDER BY r.created_at DESC
        """, user_id)
        
        result = []
        for row in rows:
            image_rows = await conn.fetch("SELECT * FROM register_images WHERE register_id = $1 ORDER BY image_order", row['id'])
            images = [RegisterImage(**img_row) for img_row in image_rows]
            
            register_detail = RegisterWithDetails(
                id=row['id'],
                user_id=row['user_id'],
                species=Species(
                    id=row['species_id'],
                    common_name=row['common_name'],
                    scientific_name=row['scientific_name'],
                    created_at=row['species_created_at'],
                    updated_at=row['species_updated_at']
                ),
                location=Location(
                    id=row['location_id'],
                    longitude=row['longitude'],
                    latitude=row['latitude'],
                    location=row['location_name'],
                    created_at=row['location_created_at'],
                    updated_at=row['location_updated_at']
                ),
                description=row['description'],
                images=images,
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            result.append(register_detail)
        
        print(f"📊 Encontradas {len(result)} observaciones para el usuario {user_id}")
        return result

if __name__ == "__main__":
    print("🚀 Iniciando servidor MCP para observations_db...")
    mcp.run()
