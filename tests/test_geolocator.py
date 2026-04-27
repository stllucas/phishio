from runtime.core.GeoLocator import get_location_by_ip

def test_geolocator_special_ips():
    loc_local = get_location_by_ip("127.0.0.1")
    assert isinstance(loc_local, dict)
    
    loc_invalido = get_location_by_ip("999.999.999.999")
    assert loc_invalido.get("estado") == "Desconhecido", "IPs inválidos devem retornar estado Desconhecido"
    assert loc_invalido.get("cidade") == "Desconhecido", "IPs inválidos devem retornar cidade Desconhecida"
