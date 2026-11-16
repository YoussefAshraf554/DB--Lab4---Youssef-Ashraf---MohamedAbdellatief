-- Lab 4 / Problem 2: Library database (DDL)
-- Run: mysql -u root -p < problem2_DDL.sql
DROP DATABASE IF EXISTS library;
CREATE DATABASE library;
USE library;

CREATE TABLE author (
    author_id INT NOT NULL AUTO_INCREMENT,
    name      VARCHAR(100) NOT NULL,
    country   VARCHAR(50),
    photo     VARCHAR(255),                 -- file name of the uploaded photo (Lab 3)
    PRIMARY KEY (author_id)
);

CREATE TABLE publisher (
    publisher_id INT NOT NULL AUTO_INCREMENT,
    name         VARCHAR(100) NOT NULL,
    country      VARCHAR(50),
    PRIMARY KEY (publisher_id)
);

CREATE TABLE category (
    category_id INT NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    PRIMARY KEY (category_id)
);

CREATE TABLE book (
    book_id      INT NOT NULL AUTO_INCREMENT,
    title        VARCHAR(200) NOT NULL,
    price        DECIMAL(10, 2) NOT NULL,
    publish_year INT NOT NULL,
    author_id    INT NOT NULL,
    publisher_id INT NOT NULL,
    category_id  INT NOT NULL,
    cover        VARCHAR(255),              -- file name of the uploaded cover (Lab 3)
    PRIMARY KEY (book_id),
    FOREIGN KEY (author_id)    REFERENCES author(author_id) ON DELETE CASCADE,
    FOREIGN KEY (publisher_id) REFERENCES publisher(publisher_id),
    FOREIGN KEY (category_id)  REFERENCES category(category_id)
);

CREATE TABLE member (
    member_id INT NOT NULL AUTO_INCREMENT,
    name      VARCHAR(100) NOT NULL,
    email     VARCHAR(255) NOT NULL UNIQUE,
    join_date DATE NOT NULL,
    PRIMARY KEY (member_id)
);

CREATE TABLE loan (
    loan_id     INT NOT NULL AUTO_INCREMENT,
    book_id     INT NOT NULL,
    member_id   INT NOT NULL,
    loan_date   DATE NOT NULL,
    return_date DATE NULL,                  -- NULL while the book is still borrowed
    PRIMARY KEY (loan_id),
    FOREIGN KEY (book_id)   REFERENCES book(book_id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES member(member_id)
);

-- Used only by the login and register pages of the website (Lab 2 / Lab 3)
CREATE TABLE users (
    user_id       INT NOT NULL AUTO_INCREMENT,
    email         VARCHAR(255) NOT NULL UNIQUE,
    name          VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    PRIMARY KEY (user_id)
);
