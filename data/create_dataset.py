import os
import sys
from pathlib import Path

# Add my_awesome_api to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / "my_awesome_api"))

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List

from coolname import generate as generate_random_title
from names_generator import generate_name

import my_awesome_api.models.sqlalchemy as sql
from my_awesome_api.database import SQLDatabase
from my_awesome_api.models.sqlalchemy import Base
from my_awesome_api.resources import get_database, get_secret_cache

# logging.basicConfig()
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def count_batcher(count: int, subtract: int) -> int:
    while count > 0:
        if count >= subtract:
            yield subtract
        elif count < subtract:
            yield count
        else:
            break
        count -= subtract


def generate_random_date(start_year: int, end_year: int) -> datetime:
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    delta_days = (end_date - start_date).days
    random_days = random.randint(0, delta_days)
    random_date = start_date + timedelta(days=random_days)
    return random_date


def generate_prefixed_email(*, prefix: str, total_amount: int, index: int) -> str:
    if not type(prefix) is str and type(total_amount) is int and type(index) is int:
        raise ValueError("Invalid argument type.")
    if not (total_amount >= 0 and index >= 0 and index <= total_amount):
        raise ValueError("Index condition failed: index >= 0 and index < total_amount")
    return f"{prefix}_{str(index).zfill(len(str(total_amount)))}@my_awesome_email.com"


async def populate_database(
    database: SQLDatabase,
    *,
    batch_size: int = 1000,
    authors_amount: int = 500,
    books_amount: int = 5000,
    loans_amount: int = 1000,
    borrowers_amount: int = 10000,
    reviews_amount: int = 1000,
):
    """
    Serialize given SQL Database in batches to not run out of memory.
    * batch_size defines how many items are being handled and commited in one transaction
    """
    total_authors: int = 0
    total_books: int = 0
    total_borrowers: int = 0
    total_loans: int = 0
    total_reviews: int = 0

    batch_index = 1

    print(f"Serializing Authors in one batch size of: {authors_amount}")
    with database.create_session() as session:
        authors: List[sql.Author] = serialize_authors(
            session, authors_amount, total_authors
        )
        total_authors += len(authors)

    print(
        f"Serializing Borrowers, Books, Reviews & Loans in batch size of: {batch_size}"
    )
    for batch in count_batcher(borrowers_amount, batch_size):
        with database.create_session() as session:
            print(f"********* BATCH NO: {batch_index} *********")
            print(f"********* BATCH SIZE: {batch} *********")
            borrowers: List[sql.Borrower] = serialize_borrowers(
                session, batch, total_borrowers
            )
            total_borrowers += len(borrowers)

            remaining_books = books_amount - total_books
            books_to_create = min(batch, remaining_books)
            books: List[sql.Book] = serialize_books(
                session, batch, books_to_create, authors
            )
            total_books += len(books)

            remaining_loans = loans_amount - total_loans
            loans_to_create = min(batch, remaining_loans)
            loans: List[sql.Loan] = serialize_loans(
                session, loans_to_create, total_loans, books, borrowers
            )

            remaining_reviews = reviews_amount - total_reviews
            reviews_to_create = min(batch, remaining_reviews)
            reviews = serialize_reviews(
                session, reviews_to_create, total_reviews, borrowers, books
            )
            total_reviews += len(reviews)

            total_loans += len(loans)

            batch_index += 1

    print(
        "Serialization finished! "
        + f"total of authors: {total_authors} "
        + f"total of books: {total_books} "
        + f"total of borrowers: {total_borrowers} "
        + f"total of loans: {total_loans} "
    )


def serialize_authors(session, authors_amount: int, total_authors: int):
    authors: List[sql.Author] = []
    index = 0
    index += total_authors
    for _ in range(authors_amount):
        first_name, last_name = generate_name(style="capital").split()
        author = sql.Author(
            first_name=first_name,
            last_name=last_name,
            biography="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        )
        authors.append(author)
        index += 1
    session.add_all(authors)
    session.flush()
    return authors


def serialize_books(
    session, books_amount: int, total_books: int, authors: List[sql.Author]
):
    books: List[sql.Book] = []
    index = 0
    index += total_books
    for _ in range(books_amount):
        random_num_of_authors = random.randint(1, 3)
        randomly_selected_authors: List[sql.Author] = random.sample(
            authors, random_num_of_authors
        )
        random_title = " ".join(generate_random_title())
        random_date = generate_random_date(1800, 2024)
        book = sql.Book(title=random_title, published_date=random_date)
        book.authors.extend(randomly_selected_authors)
        books.append(book)
        index += 1
    session.add_all(books)
    session.flush()
    return books


def serialize_borrowers(session, borrowers_amount: int, total_borrowers: int):
    borrowers: List[sql.Borrower] = []
    borrower_count = total_borrowers + borrowers_amount
    index = 0
    index += total_borrowers
    for _ in range(borrowers_amount):
        random_first_name, random_last_name = generate_name(style="capital").split()
        random_issue_date = generate_random_date(1950, 2024)
        prefixed_email = generate_prefixed_email(
            prefix="borrower", total_amount=borrower_count, index=index
        )
        borrower = sql.Borrower(
            first_name=random_first_name,
            last_name=random_last_name,
            email=prefixed_email,
            library_card=sql.LibraryCard(issue_date=random_issue_date),
        )
        borrowers.append(borrower)
        index += 1
    session.add_all(borrowers)
    session.flush()
    return borrowers


def serialize_loans(
    session,
    loans_amount: int,
    total_loans: int,
    books: List[sql.Book],
    borrowers: List[sql.Borrower],
):
    loans: List[sql.Loan] = []
    start_index = total_loans
    end_index = start_index + loans_amount

    # Ensure the end_index does not exceed the length of books
    end_index = min(end_index, len(books))
    if start_index > len(books):
        raise ValueError(
            "Not enough books available for the requested number of loans."
        )

    books_to_use = books[start_index:end_index]
    available_books = books_to_use.copy()  # Create a copy for manipulation

    for _ in range(len(books_to_use)):
        selected_book = random.choice(available_books)
        available_books.remove(
            selected_book
        )  # Remove the selected book from available_books
        selected_borrower = random.choice(borrowers)
        loan_date = generate_random_date(1990, 2024)
        loan = sql.Loan(
            book_id=selected_book.id,
            library_card_id=selected_borrower.library_card.id,
            loan_date=loan_date,
        )
        loans.append(loan)

    session.add_all(loans)
    session.flush()
    return loans


def serialize_reviews(
    session,
    reviews_amount: int,
    total_reviews: int,
    borrowers: List[sql.Borrower],
    books: List[sql.Book],
) -> List[sql.Review]:
    reviews = []

    # Determine the index range for book selection based on total reviews
    start_index = total_reviews
    end_index = start_index + reviews_amount

    # Make sure the end index does not exceed the number of books
    end_index = min(end_index, len(books))

    if start_index > len(books):
        raise ValueError(
            "Not enough books available for the requested number of reviews."
        )

    books_to_use = books[start_index:end_index]
    borrowers_to_use = borrowers[start_index:end_index]

    for _ in range(len(books_to_use)):
        selected_book = random.choice(books_to_use)
        selected_borrower = random.choice(borrowers_to_use)
        comment = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
        rating = random.randint(1, 5)
        review_date = generate_random_date(1990, 2024)
        review = sql.Review(
            book_id=selected_book.id,
            borrower_id=selected_borrower.id,
            comment=comment,
            rating=rating,
            review_date=review_date,
        )
        reviews.append(review)

    session.add_all(reviews)
    session.flush()
    return reviews


if __name__ == "__main__":
    # When run locally we do not use aws secrets manager to fetch database secrets
    if os.getenv("ENV") == "local":
        aws_secret_cache = None
    else:
        # If your account access requires AWS PROFILE we need to provide it here
        aws_secret_cache = get_secret_cache(
            region=os.getenv("MY_AWS_REGION"),
            use_profile=os.getenv("MY_AWS_PROFILE", None),
        )
    # When populating the database from local machine do not use AWS RDS Proxy
    db: SQLDatabase = get_database(use_proxy=False, use_secret_cache=aws_secret_cache)
    Base.metadata.create_all(db.engine)
    asyncio.run(
        populate_database(
            db,
            batch_size=int(os.getenv("DATASET_BATCH_SIZE")),
            authors_amount=int(os.getenv("DATASET_AUTHORS_AMOUNT")),
            books_amount=int(os.getenv("DATASET_BOOKS_AMOUNT")),
            loans_amount=int(os.getenv("DATASET_LOANS_AMOUNT")),
            borrowers_amount=int(os.getenv("DATASET_BORROWERS_AMOUNT")),
            reviews_amount=int(os.getenv("DATASET_REVIEWS_AMOUNT")),
        )
    )
