"""Módulo de geolocalização para obtenção de dados geográficos via IP."""
import logging
import ipaddress
import geoip2.database
import geoip2.errors
from core.Config import DATA_DIR

logger = logging.getLogger(__name__)

GEOIP_DB_PATH = DATA_DIR / 'GeoLite2-City.mmdb'


def is_private_ip(ip: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback
    except ValueError:
        return False


def get_location_by_ip(ip_address: str) -> dict:
    """
    Busca os dados geográficos de um IP localmente usando o banco MaxMind GeoLite2.
    Retorna um dicionário padronizado para o Firestore.
    """
    if is_private_ip(ip_address) or ip_address == "localhost":
        return {"estado": "Local", "cidade": "Local", "pais": "Local"}

    try:
        if not GEOIP_DB_PATH.exists():
            logger.warning(
                f"Banco GeoIP não encontrado em {GEOIP_DB_PATH}. Retornando 'Desconhecido'.")
            return {"estado": "Desconhecido", "cidade": "Desconhecido", "pais": "Desconhecido"}

        with geoip2.database.Reader(GEOIP_DB_PATH) as reader:
            response = reader.city(ip_address)
            return {
                "estado": response.subdivisions.most_specific.name or "Desconhecido",
                "cidade": response.city.name or "Desconhecido",
                "pais": response.country.name or "Desconhecido"
            }
    except geoip2.errors.AddressNotFoundError:
        logger.warning(
            f"IP {ip_address} não encontrado no banco GeoIP (provavelmente interno ou não mapeado).")
    except Exception as e:
        logger.error(
            f"Erro ao resolver localização para o IP {ip_address}: {e}")

    return {"estado": "Desconhecido", "cidade": "Desconhecido", "pais": "Desconhecido"}
