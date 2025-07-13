#!/usr/bin/env python3
import requests
import json
import time

INPUT_FILE = "cartelera_personas_limpio_final_v2.json"
API_URL = "https://back.todoteatro.mx/admin/people"

# Leer token desde .jwt
with open(".jwt", encoding="utf-8") as f:
    TOKEN = f.read().strip()

HEADERS = {
    "Authorization": f"Bearer {TOKEN}"
}

# Cargar personas desde archivo
with open(INPUT_FILE, encoding="utf-8") as f:
    people = json.load(f)

# Limpiar logs previos
open("duplicados.log", "w").close()
open("errores.log", "w").close()

inserted, duplicated, failed = 0, 0, 0

for person in people:
    try:
        response = requests.post(API_URL, headers=HEADERS, data=person)
        if response.status_code == 201:
            inserted += 1
        elif response.status_code == 422 and "already exists" in response.text.lower():
            duplicated += 1
            with open("duplicados.log", "a", encoding="utf-8") as log:
                log.write(f"{person['artistic_name']}\n")
        else:
            failed += 1
            with open("errores.log", "a", encoding="utf-8") as log:
                log.write(f"{person['artistic_name']} -> {response.status_code}: {response.text}\n")
    except Exception as e:
        failed += 1
        with open("errores.log", "a", encoding="utf-8") as log:
            log.write(f"{person['artistic_name']} -> EXCEPTION: {str(e)}\n")
    time.sleep(0.25)

# Resumen
print("\n✅ Inserción completada")
print(f"🆕 Insertadas: {inserted}")
print(f"⏭️  Duplicadas: {duplicated}")
print(f"❌ Fallidas: {failed}")
