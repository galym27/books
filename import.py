# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 20:20:50 2020

@author: MutaGa
"""

import os
import csv
import sqlite3
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up cloud database
engine = create_engine("postgres://tfzyvtzbqytdic:e10db1d4ab1e718636c9b39d96a13e0fdf6d5899a010048d5bf9f888a4edaa03@ec2-35-168-54-239.compute-1.amazonaws.com:5432/d5crvtkunaf7r0")
db = scoped_session(sessionmaker(bind=engine))

# Set up local database
#conn = sqlite3.connect("localDBusers2.db", check_same_thread=False)
#db = conn.cursor()

def create_table():
    # Create table for importing book info
    db.execute("CREATE TABLE books (isbn VARCHAR PRIMARY KEY NOT NULL, BookTitle VARCHAR NOT NULL, author VARCHAR NOT NULL, publishYear INTEGER)")
    db.commit()
    db.close()

def import_data():
    #Import the data from books.csv
    f = open("books.csv")
    reader = csv.reader(f)
    next(reader, None)  # skip the headers
    for isbn, title, auth, year in reader:
        print(year)
        db.execute("INSERT INTO books (isbn, BookTitle, author, publishYear) VALUES(:a, :b, :c, :d)",
                   {"a":isbn, "b": title, "c": auth, "d": year})
    db.commit()
    db.close()

def check_db():
    check = db.execute("SELECT* FROM books WHERE publishYear=1925").fetchall()
    print(check)
    db.close()
    
# Run selected functions:
#create_table()
#import_data()
check_db()
    