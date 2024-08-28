from database import Base
from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

# Many-to-Many relationship table
book_author_table = Table(
    "book_author",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id")),
    Column("author_id", Integer, ForeignKey("authors.id")),
)


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    biography = Column(Text, nullable=True)

    # Many-to-Many relationship with Book
    books = relationship("Book", secondary=book_author_table, back_populates="authors")

    @hybrid_property
    def book_ids(self):
        return [book.id for book in self.books]

    def __repr__(self):
        return f"<Author(id={self.id}, name='{self.first_name} {self.last_name}')>"


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, index=True)
    published_date = Column(Date, nullable=True)

    # One-to-One relationship with Loan (a book can have only one active loan)
    loan = relationship(
        "Loan", back_populates="book", uselist=False, cascade="all, delete-orphan"
    )

    authors = relationship(
        "Author", secondary=book_author_table, back_populates="books"
    )

    # One-to-Many relationship with Review
    reviews = relationship("Review", back_populates="book")

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}')>"


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    borrower_id = Column(Integer, ForeignKey("borrowers.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    review_date = Column(Date, nullable=False)

    # Many-to-One relationship with Book
    book = relationship("Book", back_populates="reviews")
    borrower = relationship("Borrower", back_populates="reviews")

    def __repr__(self):
        return (
            f"<Review(id={self.id}, book_id={self.book_id}, borrower_id={self.borrower_id}, "
            f"rating={self.rating}, review_date={self.review_date})>"
        )


class Borrower(Base):
    __tablename__ = "borrowers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)

    # One-to-One relationship with LibraryCard
    library_card = relationship("LibraryCard", back_populates="borrower", uselist=False)

    # One-to-Many relationship with Review
    reviews = relationship("Review", back_populates="borrower")

    def __repr__(self):
        return f"<Borrower(id={self.id}, name='{self.first_name} {self.last_name}')>"


class LibraryCard(Base):
    __tablename__ = "library_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_date = Column(Date, nullable=True)
    borrower_id = Column(Integer, ForeignKey("borrowers.id"))
    borrower = relationship("Borrower", back_populates="library_card")
    loans = relationship("Loan", back_populates="library_card")

    def __repr__(self):
        return f"<LibraryCard(id={self.id}, issue_date={self.issue_date}, borrower_id={self.borrower_id})>"


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    book_id = Column(
        Integer, ForeignKey("books.id"), unique=True, nullable=False
    )  # Ensures one active loan per book
    library_card_id = Column(Integer, ForeignKey("library_cards.id"), nullable=False)
    loan_date = Column(Date)

    book = relationship("Book", back_populates="loan")
    library_card = relationship("LibraryCard", back_populates="loans")

    def __repr__(self):
        return f"<Loan(id={self.id}, book_id={self.book_id}, library_card_id={self.library_card_id}, loan_date={self.loan_date})>"
