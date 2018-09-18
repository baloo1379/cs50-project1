import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine("mysql+pymysql://bartix997:zxszxs321@localhost:3306/project1")
db = scoped_session(sessionmaker(bind=engine))


def main():
    file = open('books.csv')
    f = csv.reader(file, 'excel-tab')
    for b_id, books_count, isbn, authors, year, title in f:
        db.execute(
            "INSERT INTO books (books_count, isbn, authors, year, title) VALUES (:books_count, :isbn, :authors, :year, :title)",
            {"books_count": int(books_count), "isbn": isbn, "authors": authors, "year": int(float(year)), "title": title})
        print(f"Added book: {int(b_id)}, {int(books_count)}, {isbn}, {authors}, {int(float(year))}, {title}")
    db.commit()


if __name__ == '__main__':
    main()
