
# Lab 4: Library Management Application 

A Flask and MySQL web application for managing a small library: its **authors**, **publishers**, **categories**, **books**, **members** and their **loans**. Users register, log in, manage books and authors, borrow and return books, and use search pages and reports built with `WHERE`, `JOIN`, `LEFT JOIN`, `GROUP BY`, `HAVING`, `ORDER BY` and `LIMIT`.

## 1. Team Members

Team Member 1: Youssef Ashraf Attia  2304083

Team Member 2: Mohamed Abdellatief   2304027

Team Member 3: <name and id>

We worked together on the database design and SQL scripts, the implementation of the website (back end, front end, and database integration), testing, and debugging. The website continues our Lab 3 application: the login, register, books and authors pages are kept and extended, and new search, report and loan pages were added.

## 2. Project Idea

The library keeps six kinds of records:

- **Authors:** an ID, a name, a country, and an optional photo.
- **Publishers:** an ID, a name, and a country.
- **Categories:** an ID and a name.
- **Books:** an ID, a title, a price, a publish year, an optional cover, and the author, publisher and category of the book.
- **Members:** an ID, a name, an email, and a join date.
- **Loans:** a loan ID, the book, the member, the loan date, and the return date.

Every book belongs to one author, one publisher and one category, and each of them can have many books. A loan connects one member with one book, so members and books are in a many-to-many relationship through the `loan` table. All relationships are implemented with **foreign keys**, so the database guarantees that a row can never point to a row that does not exist.

- When an author is deleted, all of the author's books are deleted too (`ON DELETE CASCADE`).
- When a book is deleted, all of its loans are deleted too (`ON DELETE CASCADE`).
- `loan.return_date` is `NULL` while the book is still borrowed.

## 3. Technologies Used

- Back end: Python, Flask
- Front end: HTML, CSS, JavaScript
- Database: MySQL
- Database connector: PyMySQL
- Password hashing: bcrypt
- Environment configuration: python-dotenv (`.env`)

## 4. Project Structure

```text
lab4-<student-id>/
├── problem2_DDL.sql
├── problem2_DML.sql
├── problem2_Queries.sql
├── README.md
└── website/
    ├── app.py
    ├── requirements.txt
    ├── .env.example
    ├── static/
    │   ├── css/style.css
    │   ├── js/
    │   │   ├── login.js
    │   │   ├── register.js
    │   │   └── library.js
    │   └── uploads/          (created automatically, holds the uploaded images)
    └── templates/
        ├── base.html
        ├── macros.html
        ├── login.html
        ├── register.html
        ├── books.html
        ├── book_form.html
        ├── authors.html
        ├── author_form.html
        ├── publisher_form.html
        ├── category_form.html
        ├── loan_form.html
        ├── search.html
        ├── catalogue.html
        ├── reports.html
        ├── loans.html
        ├── most_borrowed.html
        └── authors_books.html
```

## 5. Database

| File | What it does |
| --- | --- |
| `problem2_DDL.sql` | Creates the `library` database with the `author`, `publisher`, `category`, `book`, `member` and `loan` tables (primary keys, foreign keys and `ON DELETE CASCADE`), and a `users` table used only by the login and register pages |
| `problem2_DML.sql` | Inserts the seed data: 5 authors, 3 publishers, 3 categories, 10 books, 5 members and 12 loans |
| `problem2_Queries.sql` | The SQL of every search page, each query with a comment `-- F2.1` ... `-- F2.6` before it, so it can be run in the MySQL client |

The DDL script starts with `DROP DATABASE IF EXISTS library`, so it can be re-run at any time. **Warning:** this deletes the existing `library` database and all its data before recreating it, so after re-running it you must register a new account.

The seed data contains the cases needed to test every query: two authors from the same country, an author with no books, authors with several books, an author and a publisher from the same country, books priced between 15 and 20, books that were never borrowed, a member with no loans, and loans that are not returned yet.

## 6. Setup and Run from a Fresh Machine

### Requirements

Install Python 3, MySQL Server, and Git. During setup, make sure the Python and MySQL commands are available from the terminal.

### Step 1 — Get the project

Clone the GitHub repository, or download and extract its ZIP file. Open a terminal in the project folder.

```bash
git clone <GITHUB_REPOSITORY_URL>
cd <PROJECT_FOLDER>
```

### Step 2 — Create the database

1. Start MySQL Server.
2. Open MySQL Workbench or a MySQL terminal using an account allowed to create databases.
3. Run the DDL script first and then the DML script.

From a terminal where the MySQL client is installed:

```bash
mysql -u root -p < problem2_DDL.sql
mysql -u root -p < problem2_DML.sql
```

To run all the search queries by hand (optional):

```bash
mysql -u root -p library < problem2_Queries.sql
```

In MySQL Workbench: `File > Open SQL Script`, choose the file, and run the whole script with the first lightning icon.

### Step 3 — Create and activate a virtual environment (recommended)

Open a terminal inside the `website` folder.

**Windows Command Prompt:**

```bat
py -m venv .venv
.venv\Scripts\activate
```

**Windows PowerShell:**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### Step 4 — Install Python packages

```bash
python -m pip install -r requirements.txt
```

### Step 5 — Configure environment variables

Copy `.env.example` to `.env`:

**Windows Command Prompt:**

```bat
copy .env.example .env
```

**PowerShell:**

```powershell
Copy-Item .env.example .env
```

Edit `.env` and enter the credentials for your local MySQL installation. Set a long, random `SECRET_KEY` value. Do not commit or upload `.env`; only commit `.env.example` with placeholder values.

```dotenv
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=library
SECRET_KEY=replace-with-a-long-random-secret
```

### Step 6 — Start Flask

```bash
python app.py
```

Open the local address shown by Flask, normally:

http://127.0.0.1:5000/

The home route redirects to the login page. Register a new account, then use the tabs: **Books**, **Authors**, **Search**, **Catalogue**, **Reports**, **Loans**, **Most borrowed** and **Authors & books**.

## 7. Features

### Accounts and members

- **Register:** create an account with name, email, password, and confirmation. A duplicate email is rejected.
- **Login and logout:** passwords are checked against a bcrypt hash. All library pages require login.
- **Members:** every account is also a library member (the member with the same email). The member is created automatically when the account registers or logs in, and it is the member used for loans and returns.

### Books

- **View:** a table (or grid of cards) with the cover, book ID, title, price, author ID and author name.
- **Add:** title, price, publish year, author, publisher, category, and an optional cover. The author, publisher and category lists end with a "+ Add a new ..." option that opens the matching Add page and returns to the book form after saving.
- **Edit:** change any field in a form filled with the current values. An **X** on the cover removes the image; when the form is saved the image is removed from the database and deleted from the `uploads` folder.
- **Delete:** remove a book with the trash icon, after a confirmation message. Its loans are deleted too.
- **Loan:** the loan icon next to edit and delete opens the loan page of the book (see Loans).

### Authors and publishers

- **Authors:** view, add, edit and delete (with all their books), with an optional photo. Click an author to open a window with all the books of that author.
- **Publishers:** a table under the authors, with an **Add publisher** button (name and optional country).
- **Categories:** added from the "+ Add a new category..." option of the book form. A duplicate name is rejected.

### Search and reports (the new pages)

| Page | Tab | What it shows | SQL features |
| --- | --- | --- | --- |
| F2.1 | Search | Title keyword, minimum and maximum price, and a category list. The matching books are shown cheapest first, and the results update while you type (no need to press Enter) | `WHERE`, `LIKE`, `BETWEEN`, `ORDER BY` |
| F2.2 | Catalogue | All books with the author, publisher and category names instead of the ids | `JOIN` of four tables |
| F2.3 | Reports | Number of books and average price of each category; authors who wrote at least 2 books; total, smallest and largest price of the library, with the title of the cheapest and of the most expensive book | `GROUP BY`, `HAVING`, `COUNT`, `AVG`, `SUM`, `MIN`, `MAX` |
| F2.4 | Loans | Loans not returned yet; members who never borrowed a book; books that were never borrowed | `JOIN`, `LEFT JOIN ... IS NULL` |
| F2.5 | Most borrowed | The 3 books with the most loans and the member with the most loans (returned loans are counted too) | `GROUP BY`, `ORDER BY`, `LIMIT` |
| F2.6 | Authors & books | Every author with the number of books, including the authors with 0 books; the books whose author and publisher come from the same country | `LEFT JOIN`, `JOIN` |

### Loans

- **Loan page:** it shows the title, author and category of the book and its status, **Available** or **Unavailable**.
  - If the book is available, choose the member and the loan date, then press **Confirm Borrow**.
  - If the book is borrowed and not returned yet, the page shows "This book is already loaned." and no form.
- **Rules:** a loan can only be made in the name of the logged-in member (otherwise the message is "Login as <name> first to loan this book"), and the loan date cannot be in the future.
- **Return:** the Loans page lists every loan that is not returned yet with the member name. The **Return** button appears only on the loans of the logged-in member, and it sets the return date to today. A member cannot return the loans of other members.

### Images

- **Upload:** a cover for each book and a photo for each author (png, jpg, jpeg, gif or webp, up to 5 MB).
- **Storage:** the files are saved in `website/static/uploads/` and only the file name is stored in the database (`book.cover`, `author.photo`).
- **Cleanup:** an image file is deleted together with its book or author, when it is replaced, or when it is removed with the X.

### Interface

- **List and grid view:** the Books and Authors pages can be switched between a table and a grid of cards, and the choice is remembered in the browser.
- **Icon buttons:** edit (pencil), loan (arrows) and delete (trash) icons in every row and card.
- **Messages:** a short confirmation after every add, edit, delete, loan and return.

### Validation and Security

- **Validation:** required fields, title and name length, a numeric price of 0 or more, a publish year between 1000 and the current year, a valid loan date that is not in the future, and a minimum price that is not larger than the maximum price are checked on the server, with an error message under the field.
- **Prepared statements (bonus):** the search form of F2.1 never builds the SQL text with what the user typed. The keyword, the prices and the category are sent as `%s` placeholders, and the `%` and `_` typed in the keyword are matched literally.
- **SQL:** only parameterized `SELECT`, `INSERT`, `UPDATE`, and `DELETE` statements are used; every search page is a single `SELECT` without set operators or nested queries.
- **Passwords:** stored as bcrypt hashes, never as plain text.

## 8. Notes for Testing

- The seed members (Youssef Attia, Mohamed Ali, Sara Hassan, Omar Khaled and Nour Ahmed) have no website accounts. To act as one of them, register with the member's email, for example `mohamed@example.com`.
- A new account becomes a member as soon as it registers, so it appears in "Members who never borrowed a book" until it borrows a book.
