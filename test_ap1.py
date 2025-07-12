import requests

# Cargar token
with open('.jwt') as f:
    token = f.read().strip()

headers = {
    'Authorization': f'Bearer {token}'
}

url = 'https://back.todoteatro.mx/admin/people'  # Puedes probar también /admin/roles o /admin/venues

response = requests.get(url, headers=headers)

if response.status_code == 200:
    print('✅ Conexión exitosa, se recibieron datos:')
    print(response.json())
else:
    print(f'❌ Error {response.status_code}:', response.text)
