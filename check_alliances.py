#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.storage import get_all_electoral_alliances

def main():
    try:
        alliances = get_all_electoral_alliances()
        print(f"Alianzas encontradas: {len(alliances)}")
        
        if alliances:
            for alliance in alliances:
                print(f"- ID: {alliance['id']}, Nombre: {alliance['display_name']}")
        else:
            print("No hay alianzas registradas en la base de datos")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()