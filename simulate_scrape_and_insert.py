#!/usr/bin/env python3
import requests
import unicodedata
from bs4 import BeautifulSoup
from datetime import datetime
import json

# Categorías de Wikipedia que vamos a scrapeaer
WIKI_CATEGORIES = [
    "https://es.wikipedia.org/wiki/Categoría:Actores_de_teatro_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Actrices_de_teatro_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Actores_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Actrices_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Directores_de_teatro_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Dramaturgos_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Dramaturgas_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Escenógrafos_de_México",
    "https://es.wikipedia.org/wiki/Categoría:Productores_de_teatro_de_México",
    # "https://es.wikipedia.org/wiki/Categoría:Teatro_de_México",
]

with open('.jwt') as f:
    TOKEN = ''.join(f.read().split())

HEADERS = {
    'Authorization': f'Bearer {TOKEN}'
}


def capitalize_name(name):
    return ' '.join(w.capitalize() for w in name.strip().split())

def remove_accents(input_str):
    return ''.join(
        c for c in unicodedata.normalize('NFD', input_str)
        if unicodedata.category(c) != 'Mn'
    )

def guess_gender(name):
    common_female = {
        'maria', 'guadalupe', 'juana', 'veronica', 'patricia', 'ana', 'laura', 'rosa', 'carmen', 'elena',
        'teresa', 'isabel', 'adriana', 'paola', 'leticia', 'claudia', 'jessica', 'fernanda', 'alejandra', 'angelica',
        'beatriz', 'josefina', 'alondra', 'natalia', 'diana', 'martha', 'luisa', 'karla', 'viviana', 'monica',
        'silvia', 'andrea', 'gabriela', 'irene', 'esther', 'noemi', 'aurora', 'lucia', 'mayra', 'araceli',
        'denisse', 'nancy', 'lorena', 'valeria', 'melissa', 'ximena', 'marcela', 'susana', 'berenice', 'fatima',
        'alicia', 'rebeca', 'daniela', 'edith', 'yolanda', 'paty', 'eugenia', 'marisol', 'sandra', 'guillermina',
        'ale', 'graciela', 'margarita', 'carolina', 'rosario', 'tamara', 'francisca', 'nayeli', 'reina', 'irma',
        'marlen', 'rosalia', 'rosana', 'betsabe', 'cecilia', 'jacqueline', 'flor', 'vianey', 'elisa', 'roxana',
        'karina', 'lizbeth', 'julieta', 'estefania', 'yesenia', 'lourdes', 'selene', 'mariana', 'america', 'socorro',
        'consuelo', 'itzel', 'gema', 'milagros', 'yanet', 'milena', 'cintia', 'elvira', 'perla', 'evangelina'
    }

    common_male = {
        'jose', 'juan', 'luis', 'carlos', 'manuel', 'antonio', 'pedro', 'miguel', 'jesus', 'jorge',
        'fernando', 'andres', 'roberto', 'felipe', 'rafael', 'vicente', 'emilio', 'daniel', 'oscar', 'jaime',
        'alejandro', 'ricardo', 'eduardo', 'sergio', 'martin', 'julio', 'francisco', 'alberto', 'adrian', 'gustavo',
        'cristian', 'ivan', 'victor', 'rodrigo', 'alvaro', 'armando', 'marco', 'ramon', 'hector', 'erik',
        'angel', 'gerardo', 'bryan', 'hugo', 'edgar', 'israel', 'fidel', 'gonzalo', 'ismael', 'enrique',
        'salvador', 'aleks', 'fabian', 'elias', 'noe', 'genaro', 'tomas', 'moises', 'abel', 'gilberto',
        'jonathan', 'alan', 'omar', 'david', 'ulises', 'gael', 'sebastian', 'axel', 'renato', 'ezequiel',
        'benjamin', 'diego', 'nicolas', 'franco', 'eduard', 'eliot', 'alejo', 'milton', 'bruno', 'mateo',
        'jared', 'mauricio', 'leonardo', 'julian', 'esteban', 'abraham', 'santiago', 'edson', 'dario', 'edwin',
        'matias', 'lazaro', 'lalo', 'luisangel', 'ian', 'yael', 'cristobal', 'josue'
    }

    name_parts = name.strip().lower().split()
    if not name_parts:
        return 'M'

    first = remove_accents(name_parts[0])
    if first in common_female:
        return 'F'
    if first in common_male:
        return 'M'
    if first.endswith('a'):
        return 'F'
    if first.endswith(('o', 'el', 'e')):
        return 'M'
    return 'M'

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

def get_existing_people(headers):

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

def insert_person(person, headers):
    url = 'https://back.todoteatro.mx/admin/people'
    response = requests.post(url, headers=headers, data=person)
    if response.status_code == 201:
        print(f"✅ Insertado: {person['artistic_name']}")
    else:
        print(f"❌ Error al insertar {person['artistic_name']}: {response.status_code} {response.text}")


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
existing = get_existing_people(HEADERS)

# 🧾 Filtrar nuevos
to_insert = [p for p in scraped if p['artistic_name'].strip().lower() not in existing]

# 📊 Mostrar resultados
print(f"\n🔎 Personas encontradas en Wikipedia: {len(scraped)}")
print(f"🧾 Ya existen en la BD: {len(scraped) - len(to_insert)}")
print(f"🆕 Se insertarían: {len(to_insert)}")

# 💾 Guardar en archivo JSON
with open('nombres.json', 'w', encoding='utf-8') as f:
    json.dump(to_insert, f, ensure_ascii=False, indent=2)
print("\n📁 Archivo 'nombres.json' guardado correctamente.")

# 🚀 Insertar personas una por una
for person in to_insert:
    insert_person(person, HEADERS)

