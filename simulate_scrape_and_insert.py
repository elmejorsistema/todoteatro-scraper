import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

# Categorías de Wikipedia que vamos a scrapeaer
WIKI_CATEGORIES = [
    # Actuación
    "https://es.wikipedia.org/wiki/Categoría:Actores_de_teatro_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Actrices_de_teatro_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Actores_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Actrices_de_México",

    # Dirección y dramaturgia
    "https://es.wikipedia.org/wiki/Categoría:Directores_de_teatro_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Dramaturgos_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Dramaturgas_de_México",

    # Escenografía y producción
    "https://es.wikipedia.org/wiki/Categoría:Escenógrafos_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Productores_de_teatro_de_México",

    # Genéricas
    "https://es.wikipedia.org/wiki/Categoría:Teatro_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Personas_del_teatro_en_México",
]

def capitalize_name(name):
    return ' '.join(w.capitalize() for w in name.strip().split())

def guess_gender(name):
    # Listas de nombres comunes
    common_female = {
        'maría', 'guadalupe', 'fernanda', 'ana', 'rosa', 'teresa', 'isabel',
        'josefina', 'carmen', 'beatriz', 'claudia', 'luisa', 'patricia',
        'salma', 'verónica', 'irene', 'martha', 'alondra', 'diana', 'natalia',
        'xóchitl', 'leticia', 'susana', 'marcela'
    }

    common_male = {
        'josé', 'juan', 'luis', 'carlos', 'manuel', 'antonio', 'pedro',
        'miguel', 'jesús', 'jorge', 'fernando', 'andrés', 'roberto',
        'felipe', 'rafael', 'vicente', 'emilio', 'daniel', 'oscar', 'jaime'
    }

    name_parts = name.strip().lower().split()
    if not name_parts:
        return 'O'

    # Usamos el primer nombre (antes de cualquier apellido)
    first = name_parts[0]

    if first in common_female:
        return 'F'
    if first in common_male:
        return 'M'

    # Heurística de terminación sobre el primer nombre
    if first.endswith('a'):
        return 'F'
    if first.endswith('o') or first.endswith('el') or first.endswith('e'):
        return 'M'

    return 'O'

def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def scrape_wikipedia_category(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error al acceder a {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    people = []

    for li in soup.select('#mw-pages li'):
        name = li.get_text(strip=True)
        if name:
            people.append({
                'artistic_name': capitalize_name(name),
                'gender': guess_gender(name),
                'subscription_active': '2025-12-31',
                'created_at': now(),
                'updated_at': now()
            })

    return people

def get_existing_people():
    with open('.jwt') as f:
        token = ''.join(f.read().split())  # limpiar caracteres invisibles

    headers = {
        'Authorization': f'Bearer {token}'
    }

    url = 'https://back.todoteatro.mx/admin/people'
    all_people = []
    page = 1

    while True:
        response = requests.get(f'{url}?page={page}', headers=headers)
        if response.status_code != 200:
            print(f'❌ Error al obtener página {page}: {response.status_code}')
            break

        data = response.json()
        all_people.extend(data['data'])

        if not data['next_page_url']:
            break
        page += 1

    return set(p['artistic_name'].strip().lower() for p in all_people if p.get('artistic_name'))

# 🔹 Inicia el proceso
scraped = []
for url in WIKI_CATEGORIES:
    print(f"🔍 Scrapeando: {url}")
    scraped.extend(scrape_wikipedia_category(url))

# 🔄 Eliminar duplicados entre categorías
seen = set()
filtered_scraped = []
for person in scraped:
    key = person['artistic_name'].strip().lower()
    if key not in seen:
        filtered_scraped.append(person)
        seen.add(key)
scraped = filtered_scraped

# 🔎 Obtener existentes en backend
existing = get_existing_people()

# 🧾 Filtrar nuevos
to_insert = [p for p in scraped if p['artistic_name'].strip().lower() not in existing]

# 📊 Mostrar resultados
print(f"\n🔎 Personas encontradas en Wikipedia: {len(scraped)}")
print(f"🧾 Ya existen en la BD: {len(scraped) - len(to_insert)}")
print(f"🆕 Se insertarían: {len(to_insert)}\n")

print(json.dumps(to_insert, indent=2, ensure_ascii=False))
