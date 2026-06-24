from .utils import cache_get, cache_set, cache_delete, CACHE_TTL
 
SITE_IMAGE_LIST_KEY = "site_image:list"
SITE_IMAGE_ITEM_KEY = "site_image:item:{pk}"
 
 
def get_site_image_list():
    return cache_get(SITE_IMAGE_LIST_KEY)
 
 
def set_site_image_list(data, timeout=CACHE_TTL):
    cache_set(SITE_IMAGE_LIST_KEY, data, timeout)
 
 
def get_site_image_item(pk: str):
    return cache_get(SITE_IMAGE_ITEM_KEY.format(pk=pk))
 
 
def set_site_image_item(pk: str, data, timeout=CACHE_TTL):
    cache_set(SITE_IMAGE_ITEM_KEY.format(pk=pk), data, timeout)
 
 
def invalidate_site_image(pk: str = None):
    cache_delete(SITE_IMAGE_LIST_KEY)
    if pk:
        cache_delete(SITE_IMAGE_ITEM_KEY.format(pk=pk))
 
 