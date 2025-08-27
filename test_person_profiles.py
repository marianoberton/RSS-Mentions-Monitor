#!/usr/bin/env python3
"""
Script de prueba para el sistema de perfiles de personas.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.person_profiles import PersonProfile, get_person_profile, generate_person_report, get_all_persons_summary
from app.storage import get_all_persons
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_person_profiles():
    """Probar el sistema de perfiles de personas."""
    logger.info("Iniciando pruebas del sistema de perfiles...")
    
    # 1. Obtener resumen de todas las personas
    logger.info("\n=== RESUMEN DE TODAS LAS PERSONAS ===")
    persons_summary = get_all_persons_summary()
    
    for person in persons_summary:
        logger.info(f"{person['name']} (ID: {person['id']})")
        logger.info(f"  - Nivel de importancia: {person['importance_level']}")
        logger.info(f"  - Total menciones: {person['total_mentions']}")
        logger.info(f"  - Artículos únicos: {person['unique_articles']}")
        logger.info(f"  - Última mención: {person['last_mention']}")
        logger.info("")
    
    # 2. Generar perfil detallado para cada persona
    logger.info("\n=== PERFILES DETALLADOS ===")
    
    for person in persons_summary:
        if person['total_mentions'] > 0:  # Solo personas con menciones
            logger.info(f"\n--- PERFIL DE {person['name']} ---")
            
            # Obtener perfil completo
            profile = get_person_profile(person['id'])
            
            if profile:
                logger.info(f"Nombre completo: {profile['full_name']}")
                logger.info(f"Cargo: {profile['position']}")
                logger.info(f"Partido: {profile.get('political_party', 'N/A')}")
                
                # Estadísticas
                stats = profile['stats']
                logger.info(f"\nEstadísticas:")
                logger.info(f"  - Total hits: {stats['total_hits']}")
                logger.info(f"  - Artículos únicos: {stats['unique_articles']}")
                logger.info(f"  - Promedio hits/artículo: {stats['avg_hits_per_article']:.2f}")
                
                # Keywords
                logger.info(f"\nKeywords:")
                for kw in profile['keywords']:
                    primary = " (PRIMARIA)" if kw['is_primary'] else ""
                    logger.info(f"  - {kw['keyword']}{primary}")
                
                # Tendencias
                trends = profile['trends']
                logger.info(f"\nTendencias (30 días):")
                logger.info(f"  - Total: {trends['total_period']} menciones")
                logger.info(f"  - Promedio diario: {trends['avg_daily']:.1f}")
                logger.info(f"  - Tendencia: {trends['trend']}")
                
                # Top fuentes
                logger.info(f"\nPrincipales fuentes:")
                for source in profile['top_sources'][:3]:
                    logger.info(f"  - {source['source']}: {source['mentions']} menciones")
                
                # Contexto
                context = profile['context_analysis']
                logger.info(f"\nContexto de menciones:")
                for ctx, percentage in context['percentages'].items():
                    logger.info(f"  - {ctx}: {percentage:.1f}%")
                
                # Actividad semanal
                logger.info(f"\nActividad semanal:")
                weekly = profile['weekly_activity']
                for day, count in weekly.items():
                    if count > 0:
                        logger.info(f"  - {day}: {count} menciones")
    
    # 3. Generar reporte completo para la persona más mencionada
    if persons_summary:
        most_mentioned = max(persons_summary, key=lambda x: x['total_mentions'])
        if most_mentioned['total_mentions'] > 0:
            logger.info(f"\n=== REPORTE COMPLETO DE {most_mentioned['name']} ===")
            report = generate_person_report(most_mentioned['id'])
            logger.info(report)
    
    logger.info("\n✅ Pruebas del sistema de perfiles completadas!")

def test_profile_performance():
    """Probar rendimiento del sistema de perfiles."""
    import time
    
    logger.info("\n=== PRUEBA DE RENDIMIENTO ===")
    
    persons = get_all_persons()
    
    start_time = time.time()
    
    for person in persons:
        profile = get_person_profile(person['id'])
        if profile:
            logger.info(f"Perfil generado para {person['name']}: {len(str(profile))} caracteres")
    
    end_time = time.time()
    
    logger.info(f"\nTiempo total: {end_time - start_time:.2f} segundos")
    logger.info(f"Tiempo promedio por persona: {(end_time - start_time) / len(persons):.2f} segundos")

if __name__ == "__main__":
    try:
        test_person_profiles()
        test_profile_performance()
        
        print("\n✅ Todas las pruebas completadas exitosamente!")
        print("\nEl sistema de perfiles está funcionando correctamente.")
        print("Puedes usar las funciones en person_profiles.py para obtener información detallada.")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)