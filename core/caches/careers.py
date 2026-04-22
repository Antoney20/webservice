from .utils import cache_get, cache_set, cache_delete, CACHE_TTL

CAREER_LIST_KEY = "career:list"
CAREER_ITEM_KEY = "career:item:{pk}"


def get_career_list():
    return cache_get(CAREER_LIST_KEY)


def set_career_list(data, timeout=CACHE_TTL):
    cache_set(CAREER_LIST_KEY, data, timeout)


def get_career_item(pk: str):
    return cache_get(CAREER_ITEM_KEY.format(pk=pk))


def set_career_item(pk: str, data, timeout=CACHE_TTL):
    cache_set(CAREER_ITEM_KEY.format(pk=pk), data, timeout)


def invalidate_career(pk: str = None):
    cache_delete(CAREER_LIST_KEY)
    if pk:
        cache_delete(CAREER_ITEM_KEY.format(pk=pk))