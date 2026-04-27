from unittest.mock import patch
from runtime.core.GeoLocator import get_location_by_ip


def test_geolocator_special_ips():
    loc_local = get_location_by_ip("127.0.0.1")
    assert isinstance(loc_local, dict)

    loc_invalido = get_location_by_ip("999.999.999.999")
    assert loc_invalido.get(
        "estado") == "Desconhecido", "IPs inválidos devem retornar estado Desconhecido"
    assert loc_invalido.get(
        "cidade") == "Desconhecido", "IPs inválidos devem retornar cidade Desconhecida"


def test_geolocator_database_failure():
    """Simula uma falha na biblioteca externa de leitura do banco de dados MaxMind."""
    with patch('geoip2.database.Reader') as mock_reader:
        mock_reader.return_value.__enter__.return_value.city.side_effect = Exception(
            "Erro simulado do disco")

        loc_erro = get_location_by_ip("8.8.8.8")
        assert loc_erro.get(
            "estado") == "Desconhecido", "A API não deve quebrar mesmo se o disco falhar."
