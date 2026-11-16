import re
import os
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps

import bcrypt
import pymysql
from flask import Flask, flash, redirect, render_template, request, session, url_for
from pymysql.constants import CLIENT
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024      

UPLOAD_DIR = os.path.join(app.static_folder, "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}
os.makedirs(UPLOAD_DIR, exist_ok=True)

def format_price(value):
    return f"{value:,.2f} EGP"

app.jinja_env.filters["egp"] = format_price


def money(rows, *keys):
    """Format the given price columns of every row as text, e.g. 12.5 -> '12.50 EGP'."""
    for r in rows:
        for k in keys:
            if r[k] is not None:
                r[k] = format_price(r[k])
    return rows

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

EMAIL_PATTERN = re.compile(r"^[^@ ]+@[^@ .]+([.][^@ .]+)+$")


def get_db():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
                        database=DB_NAME, cursorclass=pymysql.cursors.DictCursor,
                        client_flag=CLIENT.FOUND_ROWS)


def run(sql, params=(), fetch=False):
    """Run one SQL statement. SELECT -> list of rows, otherwise -> rows matched."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        if fetch:
            return cur.fetchall()
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper



@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("books"))
    if request.method == "GET":
        return render_template("login.html", errors={}, email="")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    errors = {}
    if email == "":
        errors["email"] = "Email is required"
    elif not EMAIL_PATTERN.match(email):
        errors["email"] = "Email is not valid"
    if password == "":
        errors["password"] = "Password is required"
    if errors:
        return render_template("login.html", errors=errors, email=email)

    rows = run("SELECT user_id, name, password_hash FROM users WHERE email = %s", (email,), fetch=True)
    user = rows[0] if rows else None
    if user is None or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return render_template("login.html", errors={"form": "Invalid email or password"}, email=email)

    session["user_id"] = user["user_id"]
    session["name"] = user["name"]
    ensure_member(user["user_id"])          # every account is also a library member
    return redirect(url_for("books"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("books"))
    if request.method == "GET":
        return render_template("register.html", errors={}, name="", email="")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    errors = {}
    if name == "":
        errors["name"] = "Name is required"
    if email == "":
        errors["email"] = "Email is required"
    if password == "":
        errors["password"] = "Password is required"
    if confirm_password == "":
        errors["confirm_password"] = "Confirm password is required"
    elif password != confirm_password:
        errors["confirm_password"] = "Passwords do not match"
    if errors:
        return render_template("register.html", errors=errors, name=name, email=email)

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                    (email, name, password_hash))
        conn.commit()
        new_user_id = cur.lastrowid
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1062:
            return render_template("register.html", errors={"email": "Email Already Exists"},
                                name=name, email=email)
        raise
    finally:
        conn.close()

    session["user_id"] = new_user_id
    session["name"] = name
    ensure_member(new_user_id)              # every account is also a library member
    return redirect(url_for("books"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))



def image_error(file):
    if file and file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXT:
            return "Image must be png, jpg, jpeg, gif or webp"
    return None


def save_image(file):
    """Save an uploaded image with a random name and return that name (or None)."""
    if not file or not file.filename:
        return None
    name = uuid.uuid4().hex + "." + file.filename.rsplit(".", 1)[-1].lower()
    file.save(os.path.join(UPLOAD_DIR, name))
    return name


def remove_image(name):
    if name:
        path = os.path.join(UPLOAD_DIR, name)
        if os.path.exists(path):
            os.remove(path)



@app.route("/books")
@login_required
def books():
    rows = run("SELECT book_id, title, price, author_id, cover FROM book ORDER BY book_id", fetch=True)
    
    names = {a["author_id"]: a["name"] for a in run("SELECT author_id, name FROM author", fetch=True)}
    return render_template("books.html", books=rows, names=names)


def read_book_form():
    book = {"title": request.form.get("title", "").strip(),
            "price": request.form.get("price", "").strip(),
            "publish_year": request.form.get("publish_year", "").strip(),
            "author_id": request.form.get("author_id", "").strip(),
            "publisher_id": request.form.get("publisher_id", "").strip(),
            "category_id": request.form.get("category_id", "").strip()}
    errors = {}
    if book["title"] == "":
        errors["title"] = "Title is required"
    elif len(book["title"]) > 200:
        errors["title"] = "Title is too long (200 characters at most)"
    try:
        price = Decimal(book["price"])
        if not price.is_finite() or price < 0 or price > Decimal("99999999.99"):
            raise InvalidOperation
    except InvalidOperation:
        errors["price"] = "Price must be a number between 0 and 99999999.99"
    this_year = date.today().year
    if not (book["publish_year"].isdigit() and 1000 <= int(book["publish_year"]) <= this_year):
        errors["publish_year"] = f"Publish year must be a number between 1000 and {this_year}"
    if not book["author_id"].isdigit():
        errors["author_id"] = "Choose an author"
    if not book["publisher_id"].isdigit():
        errors["publisher_id"] = "Choose a publisher"
    if not book["category_id"].isdigit():
        errors["category_id"] = "Choose a category"
    return book, errors


@app.route("/books/add", methods=["GET", "POST"])
@app.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@login_required
def book_form(book_id=None):
    authors = run("SELECT author_id, name FROM author ORDER BY name", fetch=True)
    publishers = run("SELECT publisher_id, name FROM publisher ORDER BY name", fetch=True)
    categories = run("SELECT category_id, name FROM category ORDER BY name", fetch=True)
    book, errors = {"title": "", "price": "", "publish_year": "", "author_id": "",
                    "publisher_id": "", "category_id": "", "cover": None}, {}

    if book_id is not None:
        rows = run("SELECT title, price, publish_year, author_id, publisher_id, category_id, cover "
                "FROM book WHERE book_id = %s", (book_id,), fetch=True)
        if not rows:
            flash("Book not found.")
            return redirect(url_for("books"))
        book = rows[0]
    old_cover = book["cover"]
    remove_cover = False

    if request.method == "POST":
        file = request.files.get("cover")
        remove_cover = request.form.get("remove_cover") == "1" and book_id is not None
        book, errors = read_book_form()
        book["cover"] = old_cover
        if image_error(file):
            errors["cover"] = image_error(file)
        if not errors:
            saved = save_image(file)
            cover = saved or (None if remove_cover else old_cover)
            try:
                if book_id is None:
                    run("INSERT INTO book (title, price, publish_year, author_id, publisher_id, category_id, cover) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (book["title"], book["price"], book["publish_year"], book["author_id"],
                        book["publisher_id"], book["category_id"], cover))
                    flash("Book added.")
                else:
                    run("UPDATE book SET title = %s, price = %s, publish_year = %s, author_id = %s, "
                        "publisher_id = %s, category_id = %s, cover = %s WHERE book_id = %s",
                        (book["title"], book["price"], book["publish_year"], book["author_id"],
                        book["publisher_id"], book["category_id"], cover, book_id))
                    flash("Book updated.")
                if saved or remove_cover:
                    remove_image(old_cover)
                return redirect(url_for("books"))
            except pymysql.err.IntegrityError:
                remove_image(saved)
                errors["author_id"] = "The author, publisher or category does not exist"

    return render_template("book_form.html", book=book, errors=errors, authors=authors,
                        publishers=publishers, categories=categories, editing=book_id is not None,
                        remove_cover=remove_cover)


def back_url(next_page):
    """Where the Add publisher / Add category pages go back to."""
    return {"book": url_for("book_form"), "authors": url_for("authors")}.get(next_page, url_for("books"))


@app.route("/publishers/add", methods=["GET", "POST"])
@login_required
def publisher_form():
    publisher, errors = {"name": "", "country": ""}, {}
    if request.method == "POST":
        publisher = {"name": request.form.get("name", "").strip(),
                    "country": request.form.get("country", "").strip()}
        if publisher["name"] == "":
            errors["name"] = "Name is required"
        elif len(publisher["name"]) > 100:
            errors["name"] = "Name is too long (100 characters at most)"
        if len(publisher["country"]) > 50:
            errors["country"] = "Country is too long (50 characters at most)"
        if not errors:
            run("INSERT INTO publisher (name, country) VALUES (%s, %s)",
                (publisher["name"], publisher["country"] or None))
            flash("Publisher added.")
            return redirect(back_url(request.args.get("next")))
    return render_template("publisher_form.html", publisher=publisher, errors=errors, back=back_url(request.args.get("next")))


@app.route("/categories/add", methods=["GET", "POST"])
@login_required
def category_form():
    category, errors = {"name": ""}, {}
    if request.method == "POST":
        category = {"name": request.form.get("name", "").strip()}
        if category["name"] == "":
            errors["name"] = "Name is required"
        elif len(category["name"]) > 100:
            errors["name"] = "Name is too long (100 characters at most)"
        elif run("SELECT category_id FROM category WHERE LOWER(name) = LOWER(%s)", (category["name"],), fetch=True):
            errors["name"] = "This category already exists"
        if not errors:
            run("INSERT INTO category (name) VALUES (%s)", (category["name"],))
            flash("Category added.")
            return redirect(back_url(request.args.get("next")))
    return render_template("category_form.html", category=category, errors=errors, back=back_url(request.args.get("next")))


@app.route("/books/<int:book_id>/delete", methods=["POST"])
@login_required
def delete_book(book_id):
    rows = run("SELECT cover FROM book WHERE book_id = %s", (book_id,), fetch=True)
    deleted = run("DELETE FROM book WHERE book_id = %s", (book_id,))
    if rows:
        remove_image(rows[0]["cover"])
    flash("Book deleted." if deleted else "Book not found.")
    return redirect(url_for("books"))



@app.route("/authors")
@login_required
def authors():
    rows = run("SELECT author_id, name, country, photo FROM author ORDER BY author_id", fetch=True)

    def image_url(name):
        return url_for("static", filename="uploads/" + name) if name else None

    books_by_author = {}
    for b in run("SELECT title, price, author_id, cover FROM book ORDER BY title", fetch=True):
        books_by_author.setdefault(b["author_id"], []).append(
            {"title": b["title"], "price": format_price(b["price"]), "cover": image_url(b["cover"])})
    author_data = {a["author_id"]: {"name": a["name"], "country": a["country"] or "",
                                    "photo": image_url(a["photo"]),
                                    "books": books_by_author.get(a["author_id"], [])} for a in rows}
    publishers = run("SELECT publisher_id, name, country FROM publisher ORDER BY publisher_id", fetch=True)
    return render_template("authors.html", authors=rows, author_data=author_data, publishers=publishers)


@app.route("/authors/add", methods=["GET", "POST"])
@app.route("/authors/<int:author_id>/edit", methods=["GET", "POST"])
@login_required
def author_form(author_id=None):
    author, errors = {"name": "", "country": "", "photo": None}, {}

    if author_id is not None:
        rows = run("SELECT name, country, photo FROM author WHERE author_id = %s", (author_id,), fetch=True)
        if not rows:
            flash("Author not found.")
            return redirect(url_for("authors"))
        author = rows[0]
    old_photo = author["photo"]

    if request.method == "POST":
        file = request.files.get("photo")
        author = {"name": request.form.get("name", "").strip(),
                "country": request.form.get("country", "").strip(), "photo": old_photo}
        if author["name"] == "":
            errors["name"] = "Name is required"
        elif len(author["name"]) > 100:
            errors["name"] = "Name is too long (100 characters at most)"
        if len(author["country"]) > 50:
            errors["country"] = "Country is too long (50 characters at most)"
        if image_error(file):
            errors["photo"] = image_error(file)
        if not errors:
            saved = save_image(file)
            photo = saved or old_photo
            country = author["country"] or None
            if author_id is None:
                run("INSERT INTO author (name, country, photo) VALUES (%s, %s, %s)",
                    (author["name"], country, photo))
                flash("Author added.")
            else:
                run("UPDATE author SET name = %s, country = %s, photo = %s WHERE author_id = %s",
                    (author["name"], country, photo, author_id))
                flash("Author updated.")
            if saved:
                remove_image(old_photo)
            if author_id is None and request.args.get("next") == "book":
                return redirect(url_for("book_form"))      # back to the Add book form
            return redirect(url_for("authors"))

    return render_template("author_form.html", author=author, errors=errors, editing=author_id is not None)


@app.route("/authors/<int:author_id>/delete", methods=["POST"])
@login_required
def delete_author(author_id):
    photo = run("SELECT photo FROM author WHERE author_id = %s", (author_id,), fetch=True)
    covers = run("SELECT cover FROM book WHERE author_id = %s", (author_id,), fetch=True)

    deleted = run("DELETE FROM author WHERE author_id = %s", (author_id,))
    if deleted:
        for row in photo:
            remove_image(row["photo"])
        for row in covers:
            remove_image(row["cover"])
    flash("Author and their books deleted." if deleted else "Author not found.")
    return redirect(url_for("authors"))




def like_pattern(text):
    """'%text%' for LIKE, where the % and _ typed by the user are matched literally."""
    text = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return "%" + text + "%"


def read_price(text, default, label, errors):
    if text == "":
        return default
    try:
        value = Decimal(text)
        if not value.is_finite() or value < 0:
            raise InvalidOperation
        return value
    except InvalidOperation:
        errors[label] = "Enter a number (0 or more)"
        return default



@app.route("/search")
@login_required
def search():
    form = {"q": request.args.get("q", "").strip(),
            "min_price": request.args.get("min_price", "").strip(),
            "max_price": request.args.get("max_price", "").strip(),
            "category": request.args.get("category", "").strip()}
    errors = {}
    low = read_price(form["min_price"], Decimal("0"), "min_price", errors)
    high = read_price(form["max_price"], Decimal("99999999.99"), "max_price", errors)
    if not errors and low > high:
        errors["max_price"] = "Maximum price must not be smaller than the minimum"
    if form["category"] and not form["category"].isdigit():
        errors["category"] = "Choose a category from the list"

    categories = run("SELECT category_id, name FROM category ORDER BY name", fetch=True)
    results = []
    if not errors:
        sql = ("SELECT b.book_id, b.title, b.price, b.publish_year, a.name AS author, c.name AS category "
            "FROM book b "
            "JOIN author a ON b.author_id = a.author_id "
            "JOIN category c ON b.category_id = c.category_id "
            "WHERE b.title LIKE %s AND b.price BETWEEN %s AND %s")
        params = [like_pattern(form["q"]), low, high]
        if form["category"]:
            sql += " AND b.category_id = %s"
            params.append(form["category"])
        sql += " ORDER BY b.price ASC"
        results = money(run(sql, params, fetch=True), "price")
    return render_template("search.html", form=form, errors=errors, categories=categories, results=results)


@app.route("/catalogue")
@login_required
def catalogue():
    rows = run("SELECT b.book_id, b.title, b.price, b.publish_year, "
            "a.name AS author, p.name AS publisher, c.name AS category "
            "FROM book b "
            "JOIN author a ON b.author_id = a.author_id "
            "JOIN publisher p ON b.publisher_id = p.publisher_id "
            "JOIN category c ON b.category_id = c.category_id "
            "ORDER BY b.book_id", fetch=True)
    return render_template("catalogue.html", rows=money(rows, "price"))



@app.route("/reports")
@login_required
def reports():
    per_category = run("SELECT c.name AS category, COUNT(b.book_id) AS books, AVG(b.price) AS average_price "
                    "FROM category c LEFT JOIN book b ON b.category_id = c.category_id "
                    "GROUP BY c.category_id, c.name ORDER BY c.name", fetch=True)
    prolific = run("SELECT a.name AS author, COUNT(*) AS books "
                "FROM author a JOIN book b ON b.author_id = a.author_id "
                "GROUP BY a.author_id, a.name HAVING COUNT(*) >= 2 "
                "ORDER BY books DESC, a.name", fetch=True)
    totals = run("SELECT SUM(price) AS total_price, MIN(price) AS smallest_price, MAX(price) AS largest_price "
                "FROM book", fetch=True)
    cheapest = run("SELECT title FROM book ORDER BY price ASC, title LIMIT 1", fetch=True)
    priciest = run("SELECT title FROM book ORDER BY price DESC, title LIMIT 1", fetch=True)
    totals = money(totals, "total_price", "smallest_price", "largest_price")[0]
    if cheapest:
        totals["smallest_price"] += " (" + cheapest[0]["title"] + ")"
    if priciest:
        totals["largest_price"] += " (" + priciest[0]["title"] + ")"
    return render_template("reports.html",
                        per_category=money(per_category, "average_price"),
                        prolific=prolific,
                        totals=totals)

def ensure_member(user_id):
    """The library member of a website account: the member with the same email.
    If there is none yet, one is created from the account (name and email)."""
    sql = ("SELECT u.name, u.email, m.member_id FROM users u "
        "LEFT JOIN member m ON LOWER(m.email) = LOWER(u.email) WHERE u.user_id = %s")
    rows = run(sql, (user_id,), fetch=True)
    if not rows:
        return None
    if rows[0]["member_id"] is None:
        try:
            run("INSERT INTO member (name, email, join_date) VALUES (%s, %s, CURDATE())",
                (rows[0]["name"], rows[0]["email"]))
        except pymysql.err.IntegrityError:
            pass
        rows = run(sql, (user_id,), fetch=True)
    return rows[0]["member_id"]


def current_member_id():
    return ensure_member(session["user_id"])


# F2.4  Loans: JOIN and LEFT JOIN ... IS NULL.
@app.route("/loans")
@login_required
def loans():
    not_returned = run("SELECT l.loan_id, l.member_id, b.title AS book, m.name AS member, l.loan_date, l.return_date "
                    "FROM loan l JOIN book b ON l.book_id = b.book_id "
                    "JOIN member m ON l.member_id = m.member_id "
                    "WHERE l.return_date IS NULL ORDER BY l.loan_date", fetch=True)
    idle_members = run("SELECT m.member_id, m.name, m.email "
                    "FROM member m LEFT JOIN loan l ON l.member_id = m.member_id "
                    "WHERE l.loan_id IS NULL ORDER BY m.name", fetch=True)
    idle_books = run("SELECT b.book_id, b.title "
                    "FROM book b LEFT JOIN loan l ON l.book_id = b.book_id "
                    "WHERE l.loan_id IS NULL ORDER BY b.title", fetch=True)
    return render_template("loans.html", not_returned=not_returned, my_member_id=current_member_id(),
                        idle_members=idle_members, idle_books=idle_books)


# Loan a book (the loan icon of the Books page) and return it (button of the Loans page).
@app.route("/books/<int:book_id>/loan", methods=["GET", "POST"])
@login_required
def loan_book(book_id):
    rows = run("SELECT b.book_id, b.title, a.name AS author, c.name AS category "
            "FROM book b JOIN author a ON b.author_id = a.author_id "
            "JOIN category c ON b.category_id = c.category_id WHERE b.book_id = %s", (book_id,), fetch=True)
    if not rows:
        flash("Book not found.")
        return redirect(url_for("books"))
    book = rows[0]
    borrowed = bool(run("SELECT loan_id FROM loan WHERE book_id = %s AND return_date IS NULL",
                        (book_id,), fetch=True))
    my_member_id = current_member_id()      # first, because it creates the member of a new account
    members = run("SELECT member_id, name FROM member ORDER BY name", fetch=True)
    errors, member_id, loan_date = {}, str(my_member_id or ""), date.today().isoformat()

    if request.method == "POST":
        member_id = request.form.get("member_id", "").strip()
        loan_date = request.form.get("loan_date", "").strip()
        if borrowed:
            errors["member_id"] = "This book is already loaned"
        elif not member_id.isdigit():
            errors["member_id"] = "Choose a member"
        elif int(member_id) != my_member_id:
            owner = next((m["name"] for m in members if str(m["member_id"]) == member_id), None)
            errors["member_id"] = (f"Login as {owner} first to loan this book" if owner
                                else "This member does not exist")
        try:
            if date.fromisoformat(loan_date) > date.today():
                errors["loan_date"] = "Loan date cannot be in the future"
        except ValueError:
            errors["loan_date"] = "Choose a valid date"
        if not errors:
            try:
                run("INSERT INTO loan (book_id, member_id, loan_date) VALUES (%s, %s, %s)",
                    (book_id, member_id, loan_date))
                flash("Loan added.")
                return redirect(url_for("loans"))
            except pymysql.err.IntegrityError:
                errors["member_id"] = "This member does not exist"

    return render_template("loan_form.html", book=book, borrowed=borrowed, members=members,
                        errors=errors, member_id=member_id, loan_date=loan_date)


@app.route("/loans/<int:loan_id>/return", methods=["POST"])
@login_required
def return_loan(loan_id):
    member_id = current_member_id()
    if member_id is None:
        flash("You can only return your own loans.")
        return redirect(url_for("loans"))
    changed = run("UPDATE loan SET return_date = CURDATE() "
                "WHERE loan_id = %s AND member_id = %s AND return_date IS NULL", (loan_id, member_id))
    flash("Book returned." if changed else "You can only return your own loans that are not returned yet.")
    return redirect(url_for("loans"))



@app.route("/most-borrowed")
@login_required
def most_borrowed():
    top_books = run("SELECT b.title, COUNT(*) AS loans "
                    "FROM book b JOIN loan l ON l.book_id = b.book_id "
                    "GROUP BY b.book_id, b.title ORDER BY loans DESC, b.title LIMIT 3", fetch=True)
    top_member = run("SELECT m.name, COUNT(*) AS loans "
                    "FROM member m JOIN loan l ON l.member_id = m.member_id "
                    "GROUP BY m.member_id, m.name ORDER BY loans DESC, m.name LIMIT 1", fetch=True)
    return render_template("most_borrowed.html", top_books=top_books, top_member=top_member)



@app.route("/authors-books")
@login_required
def authors_books():
    counts = run("SELECT a.name AS author, a.country, COUNT(b.book_id) AS books "
                "FROM author a LEFT JOIN book b ON b.author_id = a.author_id "
                "GROUP BY a.author_id, a.name, a.country ORDER BY books DESC, a.name", fetch=True)
    same_country = run("SELECT b.title, a.name AS author, p.name AS publisher, a.country "
                    "FROM book b JOIN author a ON b.author_id = a.author_id "
                    "JOIN publisher p ON b.publisher_id = p.publisher_id "
                    "WHERE a.country = p.country ORDER BY b.title", fetch=True)
    return render_template("authors_books.html", counts=counts, same_country=same_country)


if __name__ == "__main__":
    app.run(debug=True)
