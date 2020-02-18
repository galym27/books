# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 20:20:50 2020

@author: MutaGa
"""

import os
import sqlite3
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
#
#app = Flask(__name__)
#
### Check for environment variable
##if not os.getenv("DATABASE_URL"):
##    raise RuntimeError("DATABASE_URL is not set")
#
## Configure session to use filesystem
#app.config["SESSION_PERMANENT"] = False
#app.config["SESSION_TYPE"] = "filesystem"
#Session(app)

# Set up database
#engine = create_engine("postgres://tfzyvtzbqytdic:e10db1d4ab1e718636c9b39d96a13e0fdf6d5899a010048d5bf9f888a4edaa03@ec2-35-168-54-239.compute-1.amazonaws.com:5432/d5crvtkunaf7r0")
db = scoped_session(sessionmaker(bind=engine))

# Set up local database
conn = sqlite3.connect("localDBusers2.db", check_same_thread=False)
db = conn.cursor()

#db.execute("CREATE TABLE reviews (`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'isbn' VARCHAR NOT NULL, 'username' VARCHAR NOT NULL, `score` INTEGER NOT NULL, 'comment' VARCHAR NOT NULL, 'date' VARCHAR)")
db.execute("INSERT INTO reviews (username, password) VALUES('ggg2', '12345')")
conn.commit()
check = db.execute("SELECT* FROM users").fetchall()
print(check)

#conns = db.execute("SELECT * FROM pg_stat_activity")
conn.close()
#print(conns)