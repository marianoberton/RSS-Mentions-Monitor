#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para poblar la base de datos con secciones electorales de la Provincia de Buenos Aires
y catálogo de cargos políticos.
"""

import sqlite3
import logging
from datetime import datetime
from app.storage import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 8 Secciones Electorales de la Provincia de Buenos Aires
SECCIONES_ELECTORALES_PBA = [
    {
        "numero": 1,
        "nombre": "Primera Sección Electoral",
        "descripcion": "Zona Norte del Gran Buenos Aires",
        "municipios": ["Vicente López", "San Isidro", "San Fernando", "Tigre", "Escobar", "Pilar", "José C. Paz", "Malvinas Argentinas", "San Miguel", "Hurlingham", "Ituzaingó", "Tres de Febrero", "Morón", "General San Martín"]
    },
    {
        "numero": 2,
        "nombre": "Segunda Sección Electoral",
        "descripcion": "Zona Oeste del Gran Buenos Aires",
        "municipios": ["La Matanza", "Merlo", "Moreno", "General Rodríguez", "Luján", "Marcos Paz"]
    },
    {
        "numero": 3,
        "nombre": "Tercera Sección Electoral",
        "descripcion": "Zona Sur del Gran Buenos Aires",
        "municipios": ["Almirante Brown", "Avellaneda", "Berazategui", "Esteban Echeverría", "Ezeiza", "Florencio Varela", "Lanús", "Lomas de Zamora", "Quilmes"]
    },
    {
        "numero": 4,
        "nombre": "Cuarta Sección Electoral",
        "descripcion": "Zona Centro-Este",
        "municipios": ["Berisso", "Brandsen", "Ensenada", "La Plata", "Magdalena", "Presidente Perón", "San Vicente"]
    },
    {
        "numero": 5,
        "nombre": "Quinta Sección Electoral",
        "descripcion": "Zona Centro-Norte",
        "municipios": ["Campana", "Exaltación de la Cruz", "San Antonio de Areco", "San Andrés de Giles", "Zárate", "Baradero", "Ramallo", "San Pedro", "Arrecifes", "Capitán Sarmiento", "Carmen de Areco", "Pergamino", "Rojas", "Salto", "Colón", "San Nicolás"]
    },
    {
        "numero": 6,
        "nombre": "Sexta Sección Electoral",
        "descripcion": "Zona Centro-Oeste",
        "municipios": ["25 de Mayo", "9 de Julio", "Alberti", "Bragado", "Carlos Casares", "Carlos Tejedor", "Chivilcoy", "General Arenales", "General Pinto", "General Viamonte", "General Villegas", "Junín", "Leandro N. Alem", "Lincoln", "Mercedes", "Pehuajó", "Rivadavia", "Trenque Lauquen"]
    },
    {
        "numero": 7,
        "nombre": "Séptima Sección Electoral",
        "descripcion": "Zona Sur-Oeste",
        "municipios": ["Adolfo Alsina", "Bahía Blanca", "Coronel de Marina Leonardo Rosales", "Coronel Dorrego", "Coronel Pringles", "Coronel Suárez", "Daireaux", "Guaminí", "Hipólito Yrigoyen", "Monte Hermoso", "Patagones", "Pellegrini", "Puán", "Saavedra", "Tornquist", "Tres Lomas", "Villarino"]
    },
    {
        "numero": 8,
        "nombre": "Octava Sección Electoral",
        "descripcion": "Zona Centro-Sur",
        "municipios": ["Ayacucho", "Azul", "Benito Juárez", "Bolívar", "Castelli", "Chascomús", "Dolores", "General Alvarado", "General Belgrano", "General Guido", "General Juan Madariaga", "General La Madrid", "General Lavalle", "General Paz", "Laprida", "Las Flores", "Lobería", "Lobos", "Maipú", "Mar Chiquita", "Monte", "Necochea", "Olavarría", "Partido de la Costa", "Pinamar", "Punta Indio", "Rauch", "Roque Pérez", "Saladillo", "San Cayetano", "Tandil", "Tapalqué", "Tordillo", "Villa Gesell"]
    }
]

# Catálogo de cargos políticos
CATALOGO_CARGOS = [
    # Cargos Legislativos únicamente
    {"nombre": "Diputado Provincial", "nivel": "Provincial", "tipo": "Legislativo", "descripcion": "Miembro de la Legislatura Provincial"},
    {"nombre": "Diputado Nacional", "nivel": "Nacional", "tipo": "Legislativo", "descripcion": "Miembro de la Cámara de Diputados de la Nación"},
    {"nombre": "Senador Provincial", "nivel": "Provincial", "tipo": "Legislativo", "descripcion": "Miembro del Senado Provincial (donde existe)"}
]

def create_electoral_tables():
    """Crea las tablas necesarias para secciones electorales y cargos."""
    conn = get_db_connection()
    
    try:
        with conn:
            # Tabla de secciones electorales
            conn.execute("""
                CREATE TABLE IF NOT EXISTS electoral_sections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero INTEGER NOT NULL UNIQUE,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    provincia TEXT DEFAULT 'Buenos Aires',
                    municipios TEXT, -- JSON string con lista de municipios
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de catálogo de cargos
            conn.execute("""
                CREATE TABLE IF NOT EXISTS political_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    nivel TEXT NOT NULL, -- Nacional, Provincial, Municipal
                    tipo TEXT NOT NULL, -- Ejecutivo, Legislativo, Judicial, etc.
                    descripcion TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para optimizar consultas
            conn.execute("CREATE INDEX IF NOT EXISTS idx_electoral_sections_numero ON electoral_sections(numero)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_electoral_sections_provincia ON electoral_sections(provincia)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_political_positions_nivel ON political_positions(nivel)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_political_positions_tipo ON political_positions(tipo)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_political_positions_active ON political_positions(is_active)")
            
            logger.info("Tablas de datos electorales creadas exitosamente")
            
    except Exception as e:
        logger.error(f"Error creando tablas electorales: {e}")
        raise
    finally:
        conn.close()

def seed_electoral_sections():
    """Pobla la tabla de secciones electorales con datos de PBA."""
    conn = get_db_connection()
    
    try:
        with conn:
            # Verificar si ya existen datos
            cursor = conn.execute("SELECT COUNT(*) FROM electoral_sections")
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                logger.info(f"Ya existen {existing_count} secciones electorales. Actualizando datos...")
                # Limpiar datos existentes para actualizar
                conn.execute("DELETE FROM electoral_sections")
            
            # Insertar secciones electorales
            for seccion in SECCIONES_ELECTORALES_PBA:
                import json
                municipios_json = json.dumps(seccion['municipios'], ensure_ascii=False)
                
                conn.execute("""
                    INSERT INTO electoral_sections (numero, nombre, descripcion, municipios)
                    VALUES (?, ?, ?, ?)
                """, (
                    seccion['numero'],
                    seccion['nombre'],
                    seccion['descripcion'],
                    municipios_json
                ))
            
            logger.info(f"Insertadas {len(SECCIONES_ELECTORALES_PBA)} secciones electorales de PBA")
            
    except Exception as e:
        logger.error(f"Error poblando secciones electorales: {e}")
        raise
    finally:
        conn.close()

def seed_political_positions():
    """Pobla la tabla de cargos políticos."""
    conn = get_db_connection()
    
    try:
        with conn:
            # Verificar si ya existen datos
            cursor = conn.execute("SELECT COUNT(*) FROM political_positions")
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                logger.info(f"Ya existen {existing_count} cargos políticos. Actualizando datos...")
                # Limpiar datos existentes para actualizar
                conn.execute("DELETE FROM political_positions")
            
            # Insertar cargos políticos
            for cargo in CATALOGO_CARGOS:
                conn.execute("""
                    INSERT INTO political_positions (nombre, nivel, tipo, descripcion)
                    VALUES (?, ?, ?, ?)
                """, (
                    cargo['nombre'],
                    cargo['nivel'],
                    cargo['tipo'],
                    cargo['descripcion']
                ))
            
            logger.info(f"Insertados {len(CATALOGO_CARGOS)} cargos políticos")
            
    except Exception as e:
        logger.error(f"Error poblando cargos políticos: {e}")
        raise
    finally:
        conn.close()

def update_candidates_with_electoral_data():
    """Actualiza la tabla de candidatos para incluir referencias a secciones electorales y cargos."""
    conn = get_db_connection()
    
    try:
        with conn:
            # Verificar si las columnas ya existen
            cursor = conn.execute("PRAGMA table_info(candidates)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Agregar columna de cargo político si no existe
            if 'political_position_id' not in columns:
                conn.execute("""
                    ALTER TABLE candidates 
                    ADD COLUMN political_position_id INTEGER 
                    REFERENCES political_positions(id)
                """)
                logger.info("Agregada columna political_position_id a candidates")
            
            # Agregar columna de sección electoral si no existe (ya existe electoral_section)
            if 'electoral_section_id' not in columns:
                conn.execute("""
                    ALTER TABLE candidates 
                    ADD COLUMN electoral_section_id INTEGER 
                    REFERENCES electoral_sections(id)
                """)
                logger.info("Agregada columna electoral_section_id a candidates")
            
            # Crear índices para las nuevas columnas
            conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_political_position ON candidates(political_position_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_candidates_electoral_section_id ON candidates(electoral_section_id)")
            
            logger.info("Tabla de candidatos actualizada con referencias electorales")
            
    except Exception as e:
        logger.error(f"Error actualizando tabla de candidatos: {e}")
        raise
    finally:
        conn.close()

def show_electoral_summary():
    """Muestra un resumen de los datos electorales cargados."""
    conn = get_db_connection()
    
    try:
        with conn:
            # Resumen de secciones electorales
            cursor = conn.execute("SELECT COUNT(*) FROM electoral_sections")
            sections_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM political_positions")
            positions_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM candidates")
            candidates_count = cursor.fetchone()[0]
            
            print("\n" + "="*60)
            print("RESUMEN DE DATOS ELECTORALES CARGADOS")
            print("="*60)
            print(f"📍 Secciones Electorales PBA: {sections_count}")
            print(f"🏛️  Cargos Políticos: {positions_count}")
            print(f"👤 Candidatos Registrados: {candidates_count}")
            print("="*60)
            
            # Mostrar secciones electorales
            print("\n🗳️  SECCIONES ELECTORALES:")
            cursor = conn.execute("SELECT numero, nombre, descripcion FROM electoral_sections ORDER BY numero")
            for row in cursor.fetchall():
                print(f"  {row[0]}. {row[1]} - {row[2]}")
            
            # Mostrar cargos por nivel
            print("\n🏛️  CARGOS POLÍTICOS POR NIVEL:")
            cursor = conn.execute("""
                SELECT nivel, COUNT(*) as cantidad 
                FROM political_positions 
                GROUP BY nivel 
                ORDER BY cantidad DESC
            """)
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]} cargos")
            
            print("\n✅ Datos electorales cargados exitosamente")
            
    except Exception as e:
        logger.error(f"Error mostrando resumen electoral: {e}")
    finally:
        conn.close()

def main():
    """Función principal para ejecutar el seed de datos electorales."""
    logger.info("Iniciando seed de datos electorales de PBA")
    
    try:
        # 1. Crear tablas
        create_electoral_tables()
        
        # 2. Poblar secciones electorales
        seed_electoral_sections()
        
        # 3. Poblar cargos políticos
        seed_political_positions()
        
        # 4. Actualizar tabla de candidatos
        update_candidates_with_electoral_data()
        
        # 5. Mostrar resumen
        show_electoral_summary()
        
        logger.info("Seed de datos electorales completado exitosamente")
        
    except Exception as e:
        logger.error(f"Error en el proceso de seed electoral: {e}")
        raise

if __name__ == "__main__":
    main()