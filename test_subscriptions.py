#!/usr/bin/env python3
from app.storage import get_db_connection

def test_subscriptions():
    conn = get_db_connection()
    
    # Verificar suscripciones
    result = conn.execute('SELECT * FROM candidate_subscriptions').fetchall()
    print(f'Suscripciones: {len(result)}')
    
    for row in result:
        print(f'ID: {row[0]}, Candidato: {row[1]}, Chat: {row[2]}, Activa: {row[3]}')
    
    # Verificar relación con candidatos
    result = conn.execute('''
        SELECT cs.id, c.name, cs.telegram_chat_id, cs.is_active
        FROM candidate_subscriptions cs
        JOIN candidates c ON cs.candidate_id = c.id
    ''').fetchall()
    
    print('\nSuscripciones con nombres de candidatos:')
    for row in result:
        print(f'Suscripción {row[0]}: {row[1]} -> Chat {row[2]} (Activa: {row[3]})')
    
    conn.close()

if __name__ == '__main__':
    test_subscriptions()