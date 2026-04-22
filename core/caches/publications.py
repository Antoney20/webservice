from .utils import cache_get, cache_set, cache_delete, CACHE_TTL

PUBLICATION_LIST_KEY = "publication:list"
PUBLICATION_ITEM_KEY = "publication:item:{pk}"


def get_publication_list():
    return cache_get(PUBLICATION_LIST_KEY)


def set_publication_list(data, timeout=CACHE_TTL):
    cache_set(PUBLICATION_LIST_KEY, data, timeout)


def get_publication_item(pk: str):
    return cache_get(PUBLICATION_ITEM_KEY.format(pk=pk))


def set_publication_item(pk: str, data, timeout=CACHE_TTL):
    cache_set(PUBLICATION_ITEM_KEY.format(pk=pk), data, timeout)


def invalidate_publication(pk: str = None):
    cache_delete(PUBLICATION_LIST_KEY)
    if pk:
        cache_delete(PUBLICATION_ITEM_KEY.format(pk=pk))