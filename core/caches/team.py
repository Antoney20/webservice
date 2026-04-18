from .utils import cache_get, cache_set, cache_delete, CACHE_TTL

TEAM_LIST_KEY = "team:list"
TEAM_ITEM_KEY = "team:item:{pk}"


def get_team_list():
    return cache_get(TEAM_LIST_KEY)


def set_team_list(data, timeout=CACHE_TTL):
    cache_set(TEAM_LIST_KEY, data, timeout)


def get_team_item(pk: str):
    return cache_get(TEAM_ITEM_KEY.format(pk=pk))


def set_team_item(pk: str, data, timeout=CACHE_TTL):
    cache_set(TEAM_ITEM_KEY.format(pk=pk), data, timeout)


def invalidate_team(pk: str = None):
    cache_delete(TEAM_LIST_KEY)
    if pk:
        cache_delete(TEAM_ITEM_KEY.format(pk=pk))