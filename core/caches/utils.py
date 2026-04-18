from django.core.cache import cache

CACHE_TTL = 60 * 60 #  1hr


def cache_get(key: str):
    return cache.get(key)


def cache_set(key: str, value, timeout=CACHE_TTL):
    cache.set(key, value, timeout)


def cache_delete(key: str):
    cache.delete(key)


def cache_delete_pattern(pattern: str):
    try:
        cache.delete_pattern(pattern)
    except AttributeError:
        pass