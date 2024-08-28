from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class Author(BaseModel):
    id: Optional[int]
    first_name: str
    last_name: str
    biography: Optional[str] = None
    book_ids: Optional[List[int]] = []

    class Config:
        from_attributes = True
        annotations = True


class Book(BaseModel):
    id: Optional[int]
    title: str
    published_date: Optional[date] = None
    authors: Optional[List["Author"]] = []
    loan: Optional["Loan"] = None
    reviews: Optional[List["Review"]] = []

    class Config:
        from_attributes = True
        annotations = True


class Review(BaseModel):
    id: Optional[int]
    book_id: int
    borrower_id: int
    rating: int
    comment: Optional[str] = None
    review_date: date

    class Config:
        from_attributes = True
        annotations = True


class Borrower(BaseModel):
    id: Optional[int]
    first_name: str
    last_name: str
    email: str
    library_card: Optional["LibraryCard"] = None
    reviews: Optional[List["Review"]] = []

    class Config:
        from_attributes = True
        annotations = True


class LibraryCard(BaseModel):
    id: Optional[int]
    issue_date: Optional[date] = None
    borrower_id: Optional[int] = None
    loans: Optional[List["Loan"]] = []

    class Config:
        from_attributes = True
        annotations = True


class Loan(BaseModel):
    id: Optional[int]
    book_id: Optional[int]
    library_card_id: Optional[int]
    loan_date: Optional[date]

    class Config:
        from_attributes = True
        annotations = True
