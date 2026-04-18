from .utils import cache_get, cache_set, cache_delete, CACHE_TTL

INTERNSHIP_LIST_KEY = "internship:list"
INTERNSHIP_ITEM_KEY = "internship:item:{pk}"


def get_internship_list():
    return cache_get(INTERNSHIP_LIST_KEY)


def set_internship_list(data, timeout=CACHE_TTL):
    cache_set(INTERNSHIP_LIST_KEY, data, timeout)


def get_internship_item(pk: str):
    return cache_get(INTERNSHIP_ITEM_KEY.format(pk=pk))


def set_internship_item(pk: str, data, timeout=CACHE_TTL):
    cache_set(INTERNSHIP_ITEM_KEY.format(pk=pk), data, timeout)


def invalidate_internship(pk: str = None):
    cache_delete(INTERNSHIP_LIST_KEY)
    if pk:
        cache_delete(INTERNSHIP_ITEM_KEY.format(pk=pk))