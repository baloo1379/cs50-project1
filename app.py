from flask import Flask, flash, request, session, redirect, render_template, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from passlib.hash import pbkdf2_sha256
from flask_cors import CORS
import math
import requests
import goodreads

app = Flask(__name__)

engine = create_engine("mysql+pymysql://bartix997:zxszxs321@localhost:3306/project1")
db = scoped_session(sessionmaker(engine))

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
CORS(app)


class Book:
    def __init__(self, b_id, g_id, isbn, isbn13, authors, year, title, rating, ratings_count, url, small_url):
        self.id = b_id
        self.g_id = g_id
        self.isbn = isbn
        self.isbn13 = int(float(isbn13))
        self.authors = authors
        self.year = year
        self.title = title
        self.rating = rating
        self.ratings_count = ratings_count
        self.url = url
        self.small_url = small_url

    def trim_authors(self):
        authors_len = len(self.authors)
        if authors_len > 2:
            del self.authors[2:]
        self.authors = ", ".join(self.authors)
        if authors_len > 2:
            self.authors = self.authors + " and more"


class Review:

    def __init__(self, r_id, b_id, u_id, date, time, review, rating):
        self.id = r_id
        self.b_id = b_id
        self.u_id = u_id
        self.date = date
        self.time = time
        self.review = review
        self.rating = rating


@app.route('/')
def index():
    if not session.get("logged_in"):
        return render_template("welcome.html")
    else:
        return render_template("index.html", username=session["user_name"])


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "GET":
        if session.get("logged_in"):
            flash("You are already logged in")
            return redirect(url_for('index'), "303")
        else:
            return render_template("register.html")
    if request.method == "POST":
        username = request.form.get("username")
        pass1 = request.form.get("pass")
        pass2 = request.form.get("pass2")

        if pass1 != pass2 or pass1 is None or pass2 is None:
            flash("Password don't match")
            return redirect(url_for('register'), "303")

        hash = pbkdf2_sha256.hash(pass1)
        db.execute("INSERT INTO users (username, password) VALUES (:name, :hash)",
                   {"name": username, "hash": hash})
        db.commit()
        flash("Register successful")
        return redirect(url_for('register'), "303")


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "GET":
        if session.get("logged_in"):
            flash("You are already logged in")
            return redirect(url_for('index'), "303")
        else:
            return render_template("login.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        res = db.execute("SELECT id, password FROM users WHERE username LIKE :name", {"name": username}).fetchone()
        db_hash = res.password
        user_id = res.id

        if not res:
            flash("User not found")
            return redirect(url_for('login'), "303")

        # db_hash = db_hash[0].encode("utf-8")
        if pbkdf2_sha256.verify(password, db_hash):
            session["logged_in"] = True
            session["user_id"] = user_id
            session["user_name"] = username
            flash("Logged in successful")
            return redirect(url_for('index'), "303")
        else:
            flash("Invalid password")
            return redirect(url_for('login'), "303")


@app.route('/logout')
def logout():
    session["logged_in"] = False
    session["user_id"] = None
    flash("Logout successful")
    return redirect("http://127.0.0.1:5000")


@app.route('/search', methods=["GET"])
def search():
    if request.method == "GET":
        if not session.get("logged_in"):
            flash("You are not logged in")
            return redirect(url_for('index'), "303")
        else:
            query = request.args.get('q')
            page = request.args.get('page')
            if query is None:
                return render_template("search.html", message="No results.")
            text = f"%{query}%".lower()
            # finding how many pages prepare
            pages_res = db.execute(
                "SELECT id FROM books WHERE LOWER(original_title) LIKE :title OR LOWER(authors) LIKE :authors OR original_publication_year LIKE :year ORDER BY id",
                {"title": text, "authors": text, "year": text}).fetchall()
            pages = math.ceil(len(pages_res) / 10)

            if page is None or int(page) <= 0:
                off = int(0)
                page = int(1)
            else:
                off = 10 * (int(page) - 1)

            res = db.execute(
                "SELECT * FROM books WHERE LOWER(original_title) LIKE :title OR LOWER(authors) LIKE :authors OR original_publication_year LIKE :year ORDER BY id LIMIT 10 OFFSET :offset",
                {"title": text, "authors": text, "year": text, "offset": off}).fetchall()
            books = []
            for b_id, g_id, isbn, isbn13, authors, year, title, rating, r_count, image_url, small_image_url in res:
                new_book = Book(b_id, g_id, isbn, isbn13, authors.split(', '), year, title, rating, r_count, image_url, small_image_url)
                new_book.trim_authors()
                books.append(new_book)

            return render_template("search.html", results=books, page=int(page), query=query, pages=int(pages), username=session["user_name"])

    elif request.method == "POST":
        return redirect(url_for('index'), 303)


@app.route('/autocomplete/<string:text>')
def autocomplete(text):
    text = f"%{text}%".lower()
    result = db.execute(
        "SELECT * FROM books WHERE LOWER(books.original_title) LIKE :text OR LOWER(books.authors) LIKE :text OR books.original_publication_year LIKE :text ORDER BY id LIMIT 10",
        {"text": text}).fetchall()
    response = []
    for row in result:
        response.append([row.original_title, row.authors, row.original_publication_year])
    return jsonify(response)


@app.route('/book/<int:book_id>', methods=["GET"])
def book(book_id):
    if not session.get("logged_in"):
        flash("You are not logged in")
        return redirect(url_for('index'), "303")
    else:
        res = db.execute("SELECT * FROM books WHERE id LIKE :id", {"id": book_id}).fetchone()
        reviews = db.execute(
            "SELECT reviews.review, users.username, reviews.date, reviews.time, reviews.user_id, reviews.rating FROM reviews LEFT JOIN users ON reviews.user_id = users.id WHERE reviews.book_id LIKE :id",
            {"id": book_id}).fetchall()

        b_id, g_id, isbn, isbn13, authors, year, title, rating, r_count, image_url, small_image_url = res
        current_book = Book(b_id, g_id, isbn, isbn13, authors, year, title, rating, r_count, image_url, small_image_url)

        res = requests.get("https://www.goodreads.com/book/review_counts.json",
                           params={"key": goodreads.key(), "isbns": current_book.isbn13})
        # print(int(float(current_book.isbn13)), res)
        if res.status_code == 200:
            rating_available = True
            data = res.json()
            current_book.rating = float(data['books'][0]['average_rating'])
        else:
            res = requests.get("https://www.goodreads.com/book/review_counts.json",
                               params={"key": goodreads.key(), "isbns": current_book.isbn})
            if res.status_code == 200:
                rating_available = True
                data = res.json()
                current_book.rating = float(data['books'][0]['average_rating'])
            else:
                rating_available = False

        allowed = True
        for rev in reviews:
            if rev.user_id == session["user_id"]:
                allowed = False

        return render_template('book.html', id=book_id, book=current_book, reviews=reviews, allowed=allowed, username=session["user_name"], ra=rating_available)


@app.route('/review', methods=["POST"])
def review():
    if not session.get("logged_in"):
        flash("You are not logged in")
        return redirect(url_for('index'), "303")
    else:
        user_id = int(session["user_id"])
        book_id = int(request.form.get("book_id"))
        review = request.form.get("review")
        rating = float(request.form.get("rating"))
        db.execute(
            "INSERT INTO `reviews` (`id`, `book_id`, `user_id`, `date`, `time`, `review`, `rating`) VALUES (NULL, :book_id, :user_id, CURRENT_DATE(), CURRENT_TIME(), :review, :rating)",
            {"book_id": book_id, "user_id": user_id, "review": review, "rating": rating})
        db.commit()
        return redirect(url_for('book', book_id=book_id), "303")


@app.route('/api/isbn/<int:q_isbn>')
def isbn(q_isbn):
    q_isbn = f"%{q_isbn}%".lower()
    res = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn LIMIT 1", {"isbn": q_isbn}).fetchone()
    if res is None:
        return jsonify(
            {
                "error_code": 404,
                "error_message": "Not Found"
            }
        ), 404

    b_id, g_id, isbn, isbn13, authors, year, title, rating, r_count, image_url, small_image_url = res
    book = Book(b_id, g_id, isbn, isbn13, authors, year, title, rating, r_count, image_url, small_image_url)
    result = {
        "title": book.title,
        "author": book.authors,
        "year": book.year,
        "isbn": book.isbn,
        "isbn13": book.isbn13,
        "review_count": book.ratings_count,
        "average_score": book.rating
    }
    return jsonify(result)


if __name__ == '__main__':
    app.run()
