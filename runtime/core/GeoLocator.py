import requests

def get_location_by_ip(ip_address: str) -> dict:
    """
    Busca os dados geográficos de um IP.
    Retorna um dicionário padronizado para o Firestore.
    """
    # IP local ou de loopback
    if ip_address in ["127.0.0.1", "localhost", "::1"]:
        return {"estado": "Local", "cidade": "Local", "pais": "Local"}

    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}?fields=status,country,regionName,city", timeout=3)
        data = response.json()
        
        if data.get("status") == "success":
            return {
                "estado": data.get("regionName", "Desconhecido"),
                "cidade": data.get("city", "Desconhecido"),
                "pais": data.get("country", "Desconhecido")
            }
    except requests.RequestException:
        pass # Falha silenciosa para não travar a API principal

    return {"estado": "Desconhecido", "cidade": "Desconhecido", "pais": "Desconhecido"}