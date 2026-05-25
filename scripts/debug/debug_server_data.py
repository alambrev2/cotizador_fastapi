import requests
import json


def debug_server():
    url = "http://127.0.0.1:8000/api/v1/products/"
    print(f"Consultando: {url}")

    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Registros encontrados: {len(data)}")
            print(json.dumps(data, indent=2))
        else:
            print("Error en la respuesta:", response.text)

    except Exception as e:
        print(f"Error de conexión: {e}")
        print("¿Está corriendo el servidor (uvicorn)?")


if __name__ == "__main__":
    debug_server()
