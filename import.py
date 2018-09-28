import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine("mysql+pymysql://bartix997:zxszxs321@localhost:3306/project1")
db = scoped_session(sessionmaker(bind=engine))


def main():
    file = open('books.txt', 'r')
    f = csv.reader(file, 'excel-tab')
    print("id, goodread_id, isbn, isbn13, authors, publication_year, title, rating, rating_count, url, small_url")
    for b_id, g_id, isbn, isbn13, authors, year, title, rating, r_count, image_url, small_image_url in f:
        db.execute(
            "INSERT INTO `books` (`id`, `goodreads_book_id`, `isbn`, `isbn13`, `authors`, `original_publication_year`, `original_title`, `average_rating`, `ratings_count`, `image_url`, `small_image_url`) VALUES (NULL, :g_id, :isbn, :isbn13, :authors, :year, :title, :rating, :r_count, :image_url, :small_image_url)",
            {"g_id": int(g_id), "isbn": isbn, "isbn13": isbn13, "authors": authors, "year": int(float(year)), "title": title,
             "rating": float(rating), "r_count": int(r_count), "image_url": image_url, "small_image_url": small_image_url})
        # print(int(b_id), int(g_id), isbn, isbn13, authors, int(float(year)), title, float(rating), int(r_count), image_url, small_image_url)

    db.commit()


if __name__ == '__main__':
    main()
