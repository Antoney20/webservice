from config.models import SiteImage
from config.serializers import SiteImageSerializer
from core.caches.images import (
    get_site_image_list, set_site_image_list,
    get_site_image_item, set_site_image_item,
    invalidate_site_image,
)
 
 
class SiteImageService:
    @staticmethod
    def list():
        data = get_site_image_list()
        if data is None:
            qs = SiteImage.objects.select_related("uploaded_by")
            data = SiteImageSerializer(qs, many=True).data
            set_site_image_list(data)
        return data
 
    @staticmethod
    def get(pk: str):
        data = get_site_image_item(pk)
        if data is None:
            obj = SiteImage.objects.select_related("uploaded_by").get(pk=pk)
            data = SiteImageSerializer(obj).data
            set_site_image_item(pk, data)
        return data
 
    @staticmethod
    def create(validated_data, user):
        obj = SiteImage.objects.create(uploaded_by=user, **validated_data)
        invalidate_site_image()
        return obj
 
    @staticmethod
    def delete(obj: SiteImage):
        pk = str(obj.pk)
        if obj.image:
            obj.image.delete(save=False)        # remove the file too
        obj.delete()
        invalidate_site_image(pk=pk)
 

    @staticmethod
    def update(obj, validated_data):
        for k, v in validated_data.items():
            setattr(obj, k, v)
        obj.save()
        invalidate_site_image(pk=str(obj.pk))
        return obj