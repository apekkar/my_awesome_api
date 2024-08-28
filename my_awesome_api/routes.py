from datetime import date
from typing import Generator, List

import models.request as request
import models.response as response
import models.sqlalchemy as sql
import resources as resources
import settings as settings
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import parse_obj_as
from sqlalchemy.orm import Session as SQLSession

router = APIRouter()


@router.get("/authors/{author_id}", response_model=response.Author)
def get_author(
    author_id: int, session: SQLSession = Depends(resources.database_session)
):
    author = session.query(sql.Author).filter(sql.Author.id == author_id).first()
    if author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return response.Author.model_validate(author)


@router.get("/books/{book_id}", response_model=response.Book)
def get_book(book_id: int, session: SQLSession = Depends(resources.database_session)):
    book = session.query(sql.Book).filter(sql.Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return response.Book.model_validate(book)


@router.get("/books/available/", response_model=List[response.Book])
def get_available_books(session: SQLSession = Depends(resources.database_session)):
    # Query to get books that do not have any loans
    subquery = session.query(sql.Loan.book_id).subquery()
    available_books = (
        session.query(sql.Book)
        .outerjoin(subquery, sql.Book.id == subquery.c.book_id)
        .filter(subquery.c.book_id == None)
        .limit(10)
        .all()
    )
    return parse_obj_as(List[response.Book], available_books)


@router.post(
    "/books/{book_id}/loan",
    response_model=response.Loan,
    status_code=status.HTTP_201_CREATED,
)
def create_loan(
    book_id: int,
    loan: request.Loan,
    session: SQLSession = Depends(resources.database_session),
):
    book = session.query(sql.Book).filter(sql.Book.id == book_id).first()
    library_card = (
        session.query(sql.LibraryCard)
        .filter(sql.LibraryCard.id == loan.library_card_id)
        .first()
    )

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not library_card:
        raise HTTPException(status_code=404, detail="Library Card not found")

    # Check if the book is already loaned out
    existing_loan = session.query(sql.Loan).filter(sql.Loan.book_id == book_id).first()
    if existing_loan:
        raise HTTPException(status_code=409, detail="Book is already on loan")

    new_loan = sql.Loan(
        book_id=book_id,
        library_card_id=library_card.id,
        loan_date=date.today(),
    )
    session.add(new_loan)
    session.flush()
    return response.Loan.model_validate(new_loan)


@router.post(
    "/books/{book_id}/reviews",
    response_model=response.Review,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    book_id: int,
    review: request.Review,
    session: SQLSession = Depends(resources.database_session),
):
    book = session.query(sql.Book).filter(sql.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    new_review = sql.Review(
        book_id=book_id,
        borrower_id=review.borrower_id,
        comment=review.comment,
        rating=review.rating,
        review_date=date.today(),
    )
    session.add(new_review)
    session.flush()
    return response.Review.model_validate(new_review)


@router.get("/borrowers/{borrower_id}", response_model=response.Borrower)
def get_borrower(
    borrower_id: int, session: SQLSession = Depends(resources.database_session)
):
    borrower = (
        session.query(sql.Borrower).filter(sql.Borrower.id == borrower_id).first()
    )
    if borrower is None:
        raise HTTPException(status_code=404, detail="Borrower not found")
    return response.Borrower.model_validate(borrower)


@router.get("/library-cards/{library_card_id}", response_model=response.LibraryCard)
def get_library_card(
    library_card_id: int, session: SQLSession = Depends(resources.database_session)
):
    library_card = (
        session.query(sql.LibraryCard)
        .filter(sql.LibraryCard.id == library_card_id)
        .first()
    )
    if library_card is None:
        raise HTTPException(status_code=404, detail="Library Card not found")
    return response.LibraryCard.model_validate(library_card)


@router.get("/loans/{loan_id}", response_model=response.Loan)
def get_loan(loan_id: int, session: SQLSession = Depends(resources.database_session)):
    loan = session.query(sql.Loan).filter(sql.Loan.id == loan_id).first()
    if loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
    return response.Loan.model_validate(loan)


@router.delete("/loans/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(
    loan_id: int, session: SQLSession = Depends(resources.database_session)
):
    loan = session.query(sql.Loan).filter(sql.Loan.id == loan_id).first()
    if loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
    session.delete(loan)
    session.commit()
    return None


@router.get("/loans", response_model=List[response.Loan])
def list_loans_for_borrower(
    library_card_id: int, session: SQLSession = Depends(resources.database_session)
):
    # Fetch loans associated with the borrower's library card
    loans = (
        session.query(sql.Loan)
        .filter(sql.Loan.library_card_id == library_card_id)
        .all()
    )
    return parse_obj_as(List[response.Loan], loans)
