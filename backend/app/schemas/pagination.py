"""Generic pagination schema for paginated API responses."""

from typing import Generic, TypeVar

from pydantic import BaseModel

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
    items: list[T]
    total: int
    limit: int
    offset: int

    model_config = {"from_attributes": True}
