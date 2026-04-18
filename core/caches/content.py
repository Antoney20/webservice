from .utils import cache_get, cache_set, cache_delete, CACHE_TTL

CONTENT_LIST_KEY = "content:list"
CONTENT_ITEM_KEY = "content:item:{pk}"


def get_content_list():
    return cache_get(CONTENT_LIST_KEY)


def set_content_list(data, timeout=CACHE_TTL):
    cache_set(CONTENT_LIST_KEY, data, timeout)


def invalidate_content_list():
    cache_delete(CONTENT_LIST_KEY)


def get_content_item(pk: str):
    return cache_get(CONTENT_ITEM_KEY.format(pk=pk))


def set_content_item(pk: str, data, timeout=CACHE_TTL):
    cache_set(CONTENT_ITEM_KEY.format(pk=pk), data, timeout)


def invalidate_content_item(pk: str):
    cache_delete(CONTENT_ITEM_KEY.format(pk=pk))


def invalidate_content(pk: str = None):
    invalidate_content_list()
    if pk:
        invalidate_content_item(pk)