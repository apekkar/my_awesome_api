from typing import List, Optional

from pydantic import BaseModel


class Author(BaseModel):
    first_name: str
    last_name: str
    biography: Optional[str] = None


class Book(BaseModel):
    title: str
    authors: List[Author]


class Review(BaseModel):
    borrower_id: int
    rating: int
    comment: Optional[str] = None


class Borrower(BaseModel):
    first_name: str
    last_name: str
    email: str


class Loan(BaseModel):
    library_card_id: int
