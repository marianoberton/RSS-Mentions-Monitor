#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.tasks import process_article_content
from app.storage import get_db_connection
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def force_content_processing():
    """Forzar el procesamiento de contenido de artículos pendientes."""
    print("=== FORZANDO PROCESAMIENTO DE CONTENIDO ===")
    
    # Verificar artículos sin procesar
    conn = get_db_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 0")
    unprocessed_count = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1")
    processed_count = cursor.fetchone()[0]
    
    print(f"Artículos sin procesar: {unprocessed_count}")
    print(f"Artículos procesados: {processed_count}")
    
    # Verificar menciones antes del procesamiento
    cursor = conn.execute("SELECT COUNT(*) FROM hits")
    hits_before = cursor.fetchone()[0]
    print(f"Menciones antes del procesamiento: {hits_before}")
    
    conn.close()
    
    # Ejecutar procesamiento de contenido múltiples veces para procesar más artículos
    print("\nEjecutando procesamiento de contenido...")
    for i in range(5):  # Procesar en lotes
        print(f"Lote {i+1}/5")
        try:
            process_article_content()
        except Exception as e:
            print(f"Error en lote {i+1}: {e}")
    
    # Verificar resultados
    print("\n=== RESULTADOS ===")
    conn = get_db_connection()
    
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 0")
    unprocessed_after = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1")
    processed_after = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM hits")
    hits_after = cursor.fetchone()[0]
    
    print(f"Artículos sin procesar después: {unprocessed_after} (antes: {unprocessed_count})")
    print(f"Artículos procesados después: {processed_after} (antes: {processed_count})")
    print(f"Menciones después: {hits_after} (antes: {hits_before})")
    print(f"Nuevas menciones detectadas: {hits_after - hits_before}")
    
    # Verificar menciones de candidatos específicos
    print("\n=== MENCIONES POR CANDIDATO ===")
    test_candidates = ['Diego Santilli', 'Facundo Manes', 'Sergio Massa']
    for candidate_name in test_candidates:
        cursor = conn.execute("""
            SELECT COUNT(h.id)
            FROM hits h
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            JOIN candidates c ON ck.candidate_id = c.id
            WHERE c.name = ?
        """, (candidate_name,))
        
        total_hits = cursor.fetchone()[0]
        print(f"  {candidate_name}: {total_hits} menciones totales")
    
    conn.close()
    print("\n=== PROCESAMIENTO COMPLETADO ===")

if __name__ == "__main__":
    force_content_processing()