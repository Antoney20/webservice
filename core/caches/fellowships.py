from .utils import cache_get, cache_set, cache_delete, CACHE_TTL

FELLOWSHIP_LIST_KEY = "fellowship:list"
FELLOWSHIP_ITEM_KEY = "fellowship:item:{pk}"


def get_fellowship_list():
    return cache_get(FELLOWSHIP_LIST_KEY)


def set_fellowship_list(data, timeout=CACHE_TTL):
    cache_set(FELLOWSHIP_LIST_KEY, data, timeout)


def get_fellowship_item(pk: str):
    return cache_get(FELLOWSHIP_ITEM_KEY.format(pk=pk))


def set_fellowship_item(pk: str, data, timeout=CACHE_TTL):
    cache_set(FELLOWSHIP_ITEM_KEY.format(pk=pk), data, timeout)


def invalidate_fellowship(pk: str = None):
    cache_delete(FELLOWSHIP_LIST_KEY)
    if pk:
        cache_delete(FELLOWSHIP_ITEM_KEY.format(pk=pk))