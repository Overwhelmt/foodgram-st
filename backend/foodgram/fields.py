import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Принимает картинку в base64 и отдаёт абсолютный URL."""

    def to_internal_value(self, data):
        if isinstance(data, str):
            if not data or ';base64,' not in data:
                raise serializers.ValidationError(
                    'Загрузите корректное изображение в формате base64.'
                )
            header, encoded = data.split(';base64,')
            ext = header.split('/')[-1].lower()
            if ext == 'jpeg':
                ext = 'jpg'
            try:
                decoded = base64.b64decode(encoded)
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    'Не удалось декодировать изображение.'
                )
            data = ContentFile(decoded, name=f'{uuid.uuid4()}.{ext}')
        return super().to_internal_value(data)

    def to_representation(self, value):
        if not value:
            return None
        url = value.url
        request = self.context.get('request')
        if request is None:
            return url
        return request.build_absolute_uri(url)
