from .utils import cache_get, cache_set, cache_delete, CACHE_TTL

SEMINAR_LIST_KEY = "seminar:list"
SEMINAR_ITEM_KEY = "seminar:item:{pk}"


def get_seminar_list():
    return cache_get(SEMINAR_LIST_KEY)


def set_seminar_list(data, timeout=CACHE_TTL):
    cache_set(SEMINAR_LIST_KEY, data, timeout)


def get_seminar_item(pk: str):
    return cache_get(SEMINAR_ITEM_KEY.format(pk=pk))


def set_seminar_item(pk: str, data, timeout=CACHE_TTL):
    cache_set(SEMINAR_ITEM_KEY.format(pk=pk), data, timeout)


def invalidate_seminar(pk: str = None):
    cache_delete(SEMINAR_LIST_KEY)
    if pk:
        cache_delete(SEMINAR_ITEM_KEY.format(pk=pk))