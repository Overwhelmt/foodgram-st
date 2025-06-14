from rest_framework.pagination import PageNumberPagination
from foodgram.constants import PAGINATION_DEFAULT_LIMIT


class CustomPageNumberPagination(PageNumberPagination):
    page_size = PAGINATION_DEFAULT_LIMIT
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        response.data.update({
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
        })
        return response