"""Утилиты пагинации, общие для всех приложений проекта.

Вынесены в отдельный модуль, чтобы не дублировать код инициализации
``Paginator`` в каждом view.
"""
from django.core.paginator import Page, Paginator

PAGE_QUERY_PARAM = "page"


def paginate(request, queryset, per_page: int) -> Page:
    """Вернуть объект страницы для переданного queryset.

    Использование:
        page_obj = paginate(request, queryset, PER_PAGE)
        context = {
            "items": page_obj.object_list,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
        }
    """
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get(PAGE_QUERY_PARAM))
