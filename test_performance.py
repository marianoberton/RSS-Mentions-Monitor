#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testing de performance del sistema RSS Mentions Monitor
Mide tiempos de respuesta de APIs y operaciones de base de datos
"""

import sqlite3
import requests
import time
import statistics
from datetime import datetime

def test_database_performance():
    """Mide performance de consultas a la base de datos"""
    print("=== TESTING DE PERFORMANCE - BASE DE DATOS ===")
    
    conn = sqlite3.connect('data/mentions.db')
    cursor = conn.cursor()
    
    # Test 1: Consulta simple de conteo
    start_time = time.time()
    cursor.execute("SELECT COUNT(*) FROM articles")
    result = cursor.fetchone()
    db_count_time = time.time() - start_time
    print(f"Conteo de artículos: {result[0]} artículos en {db_count_time:.4f}s")
    
    # Test 2: Búsqueda FTS5
    start_time = time.time()
    cursor.execute("SELECT COUNT(*) FROM articles_fts WHERE articles_fts MATCH 'Milei'")
    result = cursor.fetchone()
    fts_search_time = time.time() - start_time
    print(f"Búsqueda FTS5 'Milei': {result[0]} resultados en {fts_search_time:.4f}s")
    
    # Test 3: JOIN complejo
    start_time = time.time()
    cursor.execute("""
        SELECT a.title, a.site, a.published_utc 
        FROM articles a 
        JOIN articles_fts af ON a.id = af.rowid 
        WHERE af.articles_fts MATCH 'Milei' 
        ORDER BY a.published_utc DESC 
        LIMIT 10
    """)
    results = cursor.fetchall()
    join_time = time.time() - start_time
    print(f"JOIN con FTS5 (10 resultados): {len(results)} resultados en {join_time:.4f}s")
    
    # Test 4: Consulta de feeds
    start_time = time.time()
    cursor.execute("SELECT name, last_success_utc, error_count FROM feed_state ORDER BY last_success_utc DESC")
    feeds = cursor.fetchall()
    feeds_time = time.time() - start_time
    print(f"Consulta de feeds: {len(feeds)} feeds en {feeds_time:.4f}s")
    
    conn.close()
    
    return {
        'db_count': db_count_time,
        'fts_search': fts_search_time,
        'join_query': join_time,
        'feeds_query': feeds_time
    }

def test_api_performance():
    """Mide performance de endpoints de la API"""
    print("\n=== TESTING DE PERFORMANCE - API ENDPOINTS ===")
    
    base_url = "http://127.0.0.1:5000"
    endpoints = [
        ("/", "Página principal"),
        ("/api/candidates", "API candidatos"),
        ("/api/stats", "API estadísticas"),
        ("/api/detailed-stats", "API estadísticas detalladas"),
        ("/api/electoral-sections", "API secciones electorales")
    ]
    
    api_times = {}
    
    for endpoint, description in endpoints:
        times = []
        print(f"\nTesting {description} ({endpoint})...")
        
        # Realizar 5 requests para obtener promedio
        for i in range(5):
            try:
                start_time = time.time()
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                request_time = time.time() - start_time
                
                if response.status_code == 200:
                    times.append(request_time)
                    print(f"  Request {i+1}: {request_time:.4f}s (Status: {response.status_code})")
                else:
                    print(f"  Request {i+1}: ERROR - Status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  Request {i+1}: ERROR - {str(e)}")
                
            time.sleep(0.1)  # Pequeña pausa entre requests
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            api_times[endpoint] = {
                'avg': avg_time,
                'min': min_time,
                'max': max_time,
                'samples': len(times)
            }
            print(f"  Promedio: {avg_time:.4f}s | Min: {min_time:.4f}s | Max: {max_time:.4f}s")
        else:
            print(f"  No se pudieron obtener mediciones válidas")
    
    return api_times

def test_concurrent_performance():
    """Simula carga concurrente básica"""
    print("\n=== TESTING DE PERFORMANCE - CARGA CONCURRENTE ===")
    
    import threading
    import queue
    
    base_url = "http://127.0.0.1:5000"
    endpoint = "/api/stats"
    num_threads = 5
    requests_per_thread = 3
    
    results_queue = queue.Queue()
    
    def worker():
        thread_times = []
        for _ in range(requests_per_thread):
            try:
                start_time = time.time()
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                request_time = time.time() - start_time
                
                if response.status_code == 200:
                    thread_times.append(request_time)
                    
            except requests.exceptions.RequestException:
                pass
                
        results_queue.put(thread_times)
    
    print(f"Ejecutando {num_threads} threads con {requests_per_thread} requests cada uno...")
    
    start_time = time.time()
    threads = []
    
    for _ in range(num_threads):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    total_time = time.time() - start_time
    
    # Recopilar resultados
    all_times = []
    while not results_queue.empty():
        thread_times = results_queue.get()
        all_times.extend(thread_times)
    
    if all_times:
        avg_time = statistics.mean(all_times)
        total_requests = len(all_times)
        requests_per_second = total_requests / total_time
        
        print(f"Total de requests exitosos: {total_requests}")
        print(f"Tiempo total: {total_time:.4f}s")
        print(f"Tiempo promedio por request: {avg_time:.4f}s")
        print(f"Requests por segundo: {requests_per_second:.2f} req/s")
        
        return {
            'total_requests': total_requests,
            'total_time': total_time,
            'avg_request_time': avg_time,
            'requests_per_second': requests_per_second
        }
    else:
        print("No se pudieron completar requests concurrentes")
        return None

def generate_performance_report(db_times, api_times, concurrent_results):
    """Genera reporte de performance"""
    print("\n=== REPORTE DE PERFORMANCE ===")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n📊 PERFORMANCE DE BASE DE DATOS:")
    for operation, time_taken in db_times.items():
        status = "✅ EXCELENTE" if time_taken < 0.1 else "⚠️ ACEPTABLE" if time_taken < 0.5 else "❌ LENTO"
        print(f"  {operation}: {time_taken:.4f}s - {status}")
    
    print("\n🌐 PERFORMANCE DE API:")
    for endpoint, metrics in api_times.items():
        avg_time = metrics['avg']
        status = "✅ RÁPIDO" if avg_time < 0.5 else "⚠️ ACEPTABLE" if avg_time < 2.0 else "❌ LENTO"
        print(f"  {endpoint}: {avg_time:.4f}s promedio - {status}")
    
    if concurrent_results:
        print("\n🔄 PERFORMANCE CONCURRENTE:")
        rps = concurrent_results['requests_per_second']
        status = "✅ EXCELENTE" if rps > 10 else "⚠️ ACEPTABLE" if rps > 5 else "❌ BAJO"
        print(f"  Requests por segundo: {rps:.2f} - {status}")
        print(f"  Tiempo promedio: {concurrent_results['avg_request_time']:.4f}s")
    
    print("\n📈 RECOMENDACIONES:")
    slow_db_ops = [op for op, time in db_times.items() if time > 0.5]
    slow_apis = [ep for ep, metrics in api_times.items() if metrics['avg'] > 2.0]
    
    if slow_db_ops:
        print(f"  - Optimizar consultas de BD: {', '.join(slow_db_ops)}")
    if slow_apis:
        print(f"  - Optimizar endpoints: {', '.join(slow_apis)}")
    if concurrent_results and concurrent_results['requests_per_second'] < 5:
        print("  - Considerar optimizaciones de concurrencia")
    if not slow_db_ops and not slow_apis and (not concurrent_results or concurrent_results['requests_per_second'] >= 10):
        print("  - ✅ El sistema muestra buen rendimiento general")

def main():
    print("🚀 INICIANDO TESTING DE PERFORMANCE")
    print("=====================================")
    
    try:
        # Test de base de datos
        db_times = test_database_performance()
        
        # Test de API
        api_times = test_api_performance()
        
        # Test concurrente
        concurrent_results = test_concurrent_performance()
        
        # Generar reporte
        generate_performance_report(db_times, api_times, concurrent_results)
        
    except Exception as e:
        print(f"❌ Error durante testing de performance: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()