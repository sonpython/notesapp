"""Generic pagination schema for paginated API responses."""

from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.

    Attributes:
        items: List of items for current page
        total: Total count of items across all pages
        limit: Maximum items per page
        offset: Number of items skipped
    """
    items: List[T]
    total: int
    limit: int
    offset: int

    model_config = {"from_attributes": True}
