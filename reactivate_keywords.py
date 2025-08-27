#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection
from datetime import datetime

def reactivate_keywords_for_active_candidates():
    """Reactivar todas las palabras clave para candidatos activos"""
    print("=== Reactivando Palabras Clave para Candidatos Activos ===")
    
    conn = get_db_connection()
    
    try:
        # 1. Obtener candidatos activos sin palabras clave activas
        cursor = conn.execute("""
            SELECT DISTINCT c.id, c.name
            FROM candidates c
            LEFT JOIN candidate_keywords ck ON c.id = ck.candidate_id AND ck.is_active = 1
            WHERE c.is_active = 1 AND ck.id IS NULL
            ORDER BY c.name
        """)
        candidates_without_active_keywords = cursor.fetchall()
        
        print(f"\n📊 Candidatos activos sin palabras clave activas: {len(candidates_without_active_keywords)}")
        
        total_reactivated = 0
        
        for candidate_id, candidate_name in candidates_without_active_keywords:
            print(f"\n🔄 Procesando: {candidate_name} (ID: {candidate_id})")
            
            # Obtener palabras clave inactivas para este candidato
            cursor = conn.execute("""
                SELECT id, keyword
                FROM candidate_keywords
                WHERE candidate_id = ? AND is_active = 0
            """, (candidate_id,))
            inactive_keywords = cursor.fetchall()
            
            if inactive_keywords:
                print(f"   📝 Palabras clave inactivas encontradas: {len(inactive_keywords)}")
                
                for keyword_id, keyword in inactive_keywords:
                    # Reactivar la palabra clave
                    conn.execute("""
                        UPDATE candidate_keywords
                        SET is_active = 1
                        WHERE id = ?
                    """, (keyword_id,))
                    
                    print(f"   ✅ Reactivada: '{keyword}'")
                    total_reactivated += 1
            else:
                print(f"   ⚠️ No se encontraron palabras clave inactivas")
                
                # Crear palabras clave básicas basadas en el nombre
                keywords_to_create = []
                
                # Agregar solo el nombre completo como keyword
                keywords_to_create.append(candidate_name)
                
                # NO agregar partes individuales del nombre para evitar keywords separadas
                
                # Crear las palabras clave
                for keyword in set(keywords_to_create):  # usar set para evitar duplicados
                    conn.execute("""
                        INSERT INTO candidate_keywords (candidate_id, keyword, created_utc, is_active)
                        VALUES (?, ?, ?, 1)
                    """, (candidate_id, keyword, datetime.utcnow().isoformat()))
                    
                    print(f"   ➕ Creada nueva palabra clave: '{keyword}'")
                    total_reactivated += 1
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n✅ COMPLETADO: {total_reactivated} palabras clave reactivadas/creadas")
        
        # 2. Verificar el estado final
        cursor = conn.execute("""
            SELECT COUNT(*) as total_active_keywords
            FROM candidate_keywords ck
            JOIN candidates c ON ck.candidate_id = c.id
            WHERE ck.is_active = 1 AND c.is_active = 1
        """)
        total_active_keywords = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT COUNT(DISTINCT c.id) as candidates_with_keywords
            FROM candidates c
            JOIN candidate_keywords ck ON c.id = ck.candidate_id
            WHERE c.is_active = 1 AND ck.is_active = 1
        """)
        candidates_with_keywords = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT COUNT(*) as total_active_candidates
            FROM candidates
            WHERE is_active = 1
        """)
        total_active_candidates = cursor.fetchone()[0]
        
        print(f"\n📈 ESTADO FINAL:")
        print(f"  • Total candidatos activos: {total_active_candidates}")
        print(f"  • Candidatos con palabras clave: {candidates_with_keywords}")
        print(f"  • Total palabras clave activas: {total_active_keywords}")
        
        if candidates_with_keywords == total_active_candidates:
            print(f"\n🎉 ¡ÉXITO! Todos los candidatos activos tienen palabras clave")
        else:
            print(f"\n⚠️ Aún faltan {total_active_candidates - candidates_with_keywords} candidatos por configurar")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    reactivate_keywords_for_active_candidates()