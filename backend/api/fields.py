import base64
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class Base64ImageField(serializers.ImageField):
    """Поле для обработки изображений в формате base64."""
    
    def to_internal_value(self, base64_data):
        if not isinstance(base64_data, str):
            return super().to_internal_value(base64_data)
            
        if not base64_data.startswith('data:image'):
            raise ValidationError('Некорректный формат изображения. Ожидается base64 строка.')
        
        try:
            header, encoded_data = base64_data.split(';base64,')
            file_extension = header.split('/')[-1]
            
            decoded_file = base64.b64decode(encoded_data)
            file_name = f'uploaded_image.{file_extension}'
            
            return ContentFile(decoded_file, name=file_name)
            
        except (ValueError, IndexError, TypeError, base64.binascii.Error) as error:
            raise ValidationError(f'Ошибка обработки изображения: {str(error)}') from error