-- Lab 4 / Problem 2: seed data for the library database
-- Run after problem2_DDL.sql:  mysql -u root -p < problem2_DML.sql
USE library;

-- 5 authors
-- * Colleen Hoover and Stephen King: same country (United States)
-- * Paulo Coelho: no books
-- * Hoover, Christie, King, Abdelhamid: at least 2 books
INSERT INTO author (author_id, name, country) VALUES
(1, 'Colleen Hoover',  'United States'),
(2, 'Amr Abdelhamid',  'Egypt'),
(3, 'Agatha Christie', 'United Kingdom'),
(4, 'Stephen King',    'United States'),
(5, 'Paulo Coelho',    'Brazil');

-- 3 publishers (same countries as some authors, for F2.6 b)
INSERT INTO publisher (publisher_id, name, country) VALUES
(1, 'Atria Books',    'United States'),
(2, 'Dar El Shorouk', 'Egypt'),
(3, 'HarperCollins',  'United Kingdom');

-- 3 categories
INSERT INTO category (category_id, name) VALUES
(1, 'Romance'),
(2, 'Mystery'),
(3, 'Fantasy');

-- 10 books
-- * prices between 15 and 20: books 7, 8, 9, 10
-- * never borrowed: books 9 and 10
INSERT INTO book (book_id, title, price, publish_year, author_id, publisher_id, category_id) VALUES
(1,  'The Land of Zikola',           14.99, 2013, 2, 2, 3),
(2,  'It Starts With Us',            11.50, 2022, 1, 1, 1),
(3,  'Murder Is Easy',               12.00, 1939, 3, 3, 2),
(4,  'Amarita - Land of Zikola 2',    9.75, 2014, 2, 2, 3),
(5,  'It Ends With Us',              13.25, 2016, 1, 1, 1),
(6,  'Murder on the Orient Express', 10.99, 1934, 3, 3, 2),
(7,  'Misery',                       15.50, 1987, 4, 1, 2),
(8,  'The Shining',                  18.00, 1977, 4, 3, 2),
(9,  'And Then There Were None',     16.75, 1939, 3, 3, 2),
(10, 'Verity',                       19.99, 2018, 1, 1, 1);

-- 5 members (Nour Ahmed has no loans)
INSERT INTO member (member_id, name, email, join_date) VALUES
(1, 'Youssef Attia', 'youssef@example.com', '2026-01-10'),
(2, 'Mohamed Ali',   'mohamed@example.com', '2026-02-15'),
(3, 'Sara Hassan',   'sara@example.com',    '2026-03-20'),
(4, 'Omar Khaled',   'omar@example.com',    '2026-05-05'),
(5, 'Nour Ahmed',    'nour@example.com',    '2026-09-01');

-- 12 loans (loans 8, 10 and 12 are not returned yet)
INSERT INTO loan (loan_id, book_id, member_id, loan_date, return_date) VALUES
(1,  1, 1, '2026-09-01', '2026-09-10'),
(2,  1, 2, '2026-09-15', '2026-09-25'),
(3,  1, 3, '2026-10-05', '2026-10-12'),
(4,  2, 1, '2026-09-03', '2026-09-12'),
(5,  2, 4, '2026-10-01', '2026-10-09'),
(6,  3, 2, '2026-09-20', '2026-09-30'),
(7,  3, 4, '2026-10-10', '2026-10-20'),
(8,  5, 3, '2026-10-15', NULL),
(9,  6, 1, '2026-10-18', '2026-10-27'),
(10, 7, 2, '2026-11-01', NULL),
(11, 4, 4, '2026-11-05', '2026-11-10'),
(12, 8, 1, '2026-11-08', NULL);
