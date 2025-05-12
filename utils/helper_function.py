from enum import Enum


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"
    
def paginate(items, page: int, limit: int):
    start = (page - 1) * limit
    end = start + limit
    total_items = len(items)
    total_pages = (total_items + limit - 1) // limit if total_items > 0 else 1

    # Ensure start and end are within bounds
    start = min(start, total_items)
    end = min(end, total_items)
    
    return {
        "items": items[start:end],
        "meta": {
            "page": page,
            "limit": limit,
            "total_items": total_items,
            "total_pages": total_pages,
        },
    }


def sort_items(items, sort_by: str, order: SortOrder):
    reverse = order == SortOrder.DESC
    return sorted(items, key=lambda x: getattr(x, sort_by), reverse=reverse)

def filter_items(items, **filters):
    result = items
    for key, value in filters.items():
        if value is not None:
            result = [item for item in result if str(getattr(item, key)).lower() == str(value).lower()]
    return result
