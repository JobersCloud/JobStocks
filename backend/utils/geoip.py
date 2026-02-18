import requests
import time
import ipaddress

_cache = {}  # ip -> {data, ts}
CACHE_TTL = 3600  # 1 hora


def _is_private_ip(ip):
    """Verifica si una IP es privada o local."""
    try:
        return ipaddress.ip_address(ip).is_private
    except (ValueError, TypeError):
        return True


def get_location(ip):
    """Resuelve IP a ubicacion via ip-api.com. Retorna dict o None."""
    if not ip or ip in ('127.0.0.1', '::1', 'localhost'):
        return {'ciudad': 'Local', 'pais': 'Local', 'pais_codigo': 'LO'}

    if _is_private_ip(ip):
        return {'ciudad': 'Red privada', 'pais': 'Local', 'pais_codigo': 'LO'}

    # Cache
    cached = _cache.get(ip)
    if cached and (time.time() - cached['ts']) < CACHE_TTL:
        return cached['data']

    try:
        resp = requests.get(
            f'http://ip-api.com/json/{ip}?fields=status,country,countryCode,regionName,city,lat,lon,isp',
            timeout=3
        )
        if resp.status_code == 200:
            j = resp.json()
            if j.get('status') == 'success':
                data = {
                    'ciudad': j.get('city', ''),
                    'region': j.get('regionName', ''),
                    'pais': j.get('country', ''),
                    'pais_codigo': j.get('countryCode', ''),
                    'lat': j.get('lat'),
                    'lon': j.get('lon'),
                    'isp': j.get('isp', '')
                }
                _cache[ip] = {'data': data, 'ts': time.time()}
                return data
    except Exception:
        pass
    return None
