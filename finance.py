import os
import datetime
import sqlite3
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    # retrieve data from history
    connection = sqlite3.connect("finance.db")
    crsr = connection.cursor()
    username = session["user_id"]
    stocks = db.execute(f"SELECT compname, SUM(shares) FROM history WHERE user='{username}' GROUP BY compname ORDER BY SUM(shares) DESC")
    print("stocks:", stocks)
    print("userid:", username)
    # count shares and total value
    symbols = []
    allshares = []
    totals = []
    curPrices = []
    compName = []
    for index in range(len(stocks)):
        stock = stocks[index]
        symb = stock['compname']
        sharenumber = int(stock['SUM(shares)'])
        quote = lookup(symb)
        curPrice2 = quote['price']
        Namecomp = quote['name']
        totalValue = sharenumber*float(curPrice2)
        # append to lists
        symbols.append(symb)
        compName.append(Namecomp)
        allshares.append(sharenumber)
        totals.append(round(totalValue,2))
        curPrices.append(round(curPrice2,2))
    balance = db.execute("SELECT cash FROM users WHERE id = :nameid", nameid=username)
    balanceDict = balance[0]
    curBalance = round(float(balanceDict["cash"]),2)
    grandTotal = round((curBalance + sum(totals)),2)
    length = len(symbols)

    return render_template("index.html", symbols=symbols, allshares=allshares, totals=totals, curPrices=curPrices,
    curBalance=curBalance, grandTotal=grandTotal, length=length, compName=compName)
    # crsr.execute("INSERT INTO history VALUES(?, ?, ?, ?, ?, ?)", (datetimeNow, username, compname, price, shares, total))
    # connection.commit()


@app.route("/buy", methods=["GET"])
@login_required
def buy():
    """Buy shares of stock"""
    return render_template("buy.html")
    # return apology("TODO")

@app.route("/buy", methods=["POST"])
@login_required
def buypost():
    # check validity of input
    if ((not request.form.get("symbol")) or (not request.form.get("shares"))):
        # top = "please fill the form?"
        bottom = "blank"
        return apology(bottom, 400)
    # get the order from customer
    stock = request.form.get("symbol")
    sharesstring = request.form.get("shares")
    if(not sharesstring.isnumeric()):
        bottom = "must be a number"
        return apology(bottom, 400)
    shares = float(sharesstring)
    if(shares%1 != 0):
        bottom = "must be a whole number"
        return apology(bottom, 400)

    QuoteResult = lookup(stock)
    if(QuoteResult==None):
        bottom = "No such symbol exists??"
        # return render_template("apology.html", top = top, bottom = bottom)
        return apology(bottom, 400)
    # collect and prepare data from current purchase for inclusion into history database
    datetimeNow = datetime.datetime.now()
    username = session["user_id"]
    compname = QuoteResult['symbol']
    # print(QuoteResult)
    price = float(QuoteResult['price'])
    total = price*shares
    totalf = format(total, '.2f')
    pricef = format(price, '.2f')
    # check the balance of the user (whether purchase of shares is affordable)
    connection = sqlite3.connect("finance.db")
    crsr = connection.cursor()
    balance = db.execute("SELECT cash FROM users WHERE id = :nameid", nameid=username)
    balanceDict = balance[0]
    balanceUpd = float(balanceDict["cash"]) - total
    balanceUpdf = format(balanceUpd, '.2f')
    if(balanceUpd<0):
        # top = "Insufficient funds"
        bottom = "reduce amount of shares"
        return apology(bottom, 400)
    # include the transaction into user's purchase history
    crsr.execute("INSERT INTO history VALUES(?, ?, ?, ?, ?, ?)", (datetimeNow, username, compname, price, shares, total))
    connection.commit()
    # update user's balance after purchase
    crsr.execute(f"UPDATE users SET cash = '{balanceUpd}' WHERE id = {username}")
    connection.commit()
    # render html with history and current balance
    hist = db.execute("SELECT * FROM history WHERE user = :nameid", nameid=username)
    return render_template("bought_nice.html", bought = QuoteResult, shares = shares, hist=hist, balance=balanceUpdf, price=pricef, total=totalf)


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    return jsonify("TODO")


@app.route("/history")
@login_required
def history():
    # retrieve data from history
    connection = sqlite3.connect("finance.db")
    crsr = connection.cursor()
    username = session["user_id"]
    fullHistory = db.execute(f"SELECT * FROM history WHERE user='{username}'")
    # break down the list of dictionaries into separate lists each representing seaprate column of data
    symbols = []
    shares = []
    dates = []
    oldPrices = []
    payments = []
    curPrices = []
    compNames = []
    transTypes = []
    for index in range(len(fullHistory)):
        # retrieve data from history database
        row = fullHistory[index]
        symb = row['compname']
        sharenumber = row['shares']
        date = row['datetime']
        oldPrice = row['price']
        payment = row['total']
        # retrieve stocks' current price etc.
        quote = lookup(symb)
        curPrice = quote['price']
        compName = quote['name']
        # type of transaction
        if(float(sharenumber)<0):
            transType = "sold"
        else:
            transType = "purchased"
        # append to lists
        symbols.append(symb)
        shares.append(sharenumber)
        dates.append(date)
        oldPrices.append(round(oldPrice,2))
        payments.append(round(payment,2))
        curPrices.append(round(curPrice,2))
        compNames.append(compName)
        transTypes.append(transType)
        length = len(symbols)

    return render_template("history.html", symbols=symbols, shares=shares, dates=dates, oldPrices=oldPrices,
    payments=payments, curPrices=curPrices, compNames=compNames, transTypes=transTypes, length=length)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/quote", methods=["GET"])
@login_required
def quote():
    """Get stock quote."""
    return render_template("quote.html")


@app.route("/quote", methods=["POST"])
@login_required
def quoted():
    if (not request.form.get("symbol")):
        # top = "Blank symbol?"
        bottom = "Really??"
        # return render_template("apology.html", top = top, bottom = bottom)
        return apology(bottom, 400)

    symbol = request.form.get("symbol")
    QuoteResult = lookup(symbol)
    if(QuoteResult==None):
        bottom = "No such symbol exists??"
        # return render_template("apology.html", top = top, bottom = bottom)
        return apology(bottom, 400)
    price = float(QuoteResult['price'])
    pricef=format(price, '.2f')
    print(round(price,2))
    return render_template("quoted.html", price = pricef)



    # render html to collect data from user when /register is accessed via GET
    # once /register is sent as POST, upon submission of data, collect endered data from field names to store in the database
    # store the data into the SQL database

@app.route("/register", methods=["GET"])
def get_form():
    """Register user"""
    return render_template("registration.html")


@app.route("/register", methods=["POST"])
def post_form():
    # render apology in case blank fields are supplied
    if ((not request.form.get("username")) or (not request.form.get("password")) or (not request.form.get("confirmation"))):
        # top = "Blank data?"
        bottom = "Really??"
        # return render_template("apology.html", top = top, bottom = bottom)
        return apology(bottom, 400)
    # store the input data from the user into variables
    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    if(password != confirmation):
        # top = "Wow"
        bottom = "Try to find a password that you can reproduce"
        # return render_template("apology.html", top = top, bottom = bottom)
        return apology(bottom, 400)

    # access the database and retrieve all usernames
    connection = sqlite3.connect("finance.db")
    crsr = connection.cursor()
    users = crsr.execute("SELECT username FROM users")

    # crsr.execute("DELETE FROM users")

    #check if entered username already exists in database
    if(username in users):
        # top = "Maaan"
        bottom = "This username is popular"
        # return render_template("apology.html", top = top, bottom = bottom)
        return apology(bottom, 400)

    hashed = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
    # store the user data into SQL database
    crsr.execute("INSERT INTO users(username, hash) VALUES(?, ?)", (username, hashed))
    connection.commit()

    # execute the command to fetch all the data from the table emp
    crsr.execute("SELECT * FROM users")

    # store all the fetched data in the ans variable
    alldata = crsr.fetchall()

    connection.close()

    # # loop to print all the data
    # for i in alldata:
    #     print(i)

    return render_template("success.html", username = username, password = hashed, alldata = alldata)



    # return apology("TODO")


@app.route("/sell", methods=["GET"])
@login_required
def sell():
    # retrieve data from history
    connection = sqlite3.connect("finance.db")
    crsr = connection.cursor()
    username = session["user_id"]
    stocks = db.execute(f"SELECT compname, SUM(shares) FROM history GROUP BY compname HAVING user='{username}' ORDER BY SUM(shares) DESC")
    # count shares and total value and collect these data into lists to be passed to .html
    symbols = []
    allshares = []
    totals = []
    curPrices = []
    compName = []
    for index in range(len(stocks)):
        stock = stocks[index]
        symb = stock['compname']
        sharenumber = int(stock['SUM(shares)'])
        quote = lookup(symb)
        curPrice2 = quote['price']
        Namecomp = quote['name']
        totalValue = sharenumber*float(curPrice2)
        # append to lists
        symbols.append(symb)
        compName.append(Namecomp)
        allshares.append(sharenumber)
        totals.append(round(totalValue,2))
        curPrices.append(round(curPrice2,2))
    balance = db.execute("SELECT cash FROM users WHERE id = :nameid", nameid=username)
    balanceDict = balance[0]
    curBalance = round(float(balanceDict["cash"]),2)
    grandTotal = round((curBalance + sum(totals)),2)
    length = len(symbols)

    return render_template("sell.html", symbols=symbols, allshares=allshares, totals=totals, curPrices=curPrices,
    curBalance=curBalance, grandTotal=grandTotal, length=length, compName=compName)



@app.route("/sell", methods=["POST"])
@login_required
def sellpost():
    if (not request.form.get("shares")):
        # top = "Blank symbol?"
        bottom = "blank"
        # return render_template("apology.html", top = top, bottom = bottom)
        return apology(bottom, 400)
    symb = request.form.get("symbol")
    sharesSell = int(request.form.get("shares"))
    NegSharesSell = sharesSell*(-1)
    # retrieve data from history
    connection = sqlite3.connect("finance.db")
    crsr = connection.cursor()
    username = session["user_id"]
    # stocks = db.execute(f"SELECT compname, SUM(shares) FROM history WHERE compname='{symb}' GROUP BY compname HAVING user='{username}' ORDER BY SUM(shares) DESC")
    stocks = db.execute(f"SELECT compname, SUM(shares) FROM history WHERE compname='{symb}' AND user='{username}'")
    # RETRIEVE AMOUNT OF SHARES OWNED BY USER FOR SELECTED STOCK (to compare with sellShares) AND CALCULATE SELLVALUE
    for index in range(len(stocks)):
        stock = stocks[index]
        sharenumber = int(stock['SUM(shares)'])
        quote = lookup(symb)
        curPrice2 = quote['price']
        curPrice2f = format(curPrice2,'.2f')
        # Namecomp = quote['name']
        SellValue = NegSharesSell*float(curPrice2)
        totalf = format(SellValue*(-1), '.2f')
    # check amount of shares owned vs shares to sell
    if(sharenumber<sharesSell):
        # top = "shares to sell exceed the amount owned"
        bottom = "blank"
        return apology(bottom, 400)
    # insert the transaction into user's history
    datetimeNow = datetime.datetime.now()
    crsr.execute("INSERT INTO history VALUES(?, ?, ?, ?, ?, ?)", (datetimeNow, username, symb, curPrice2, NegSharesSell, SellValue))
    connection.commit()
    # retreive user's current balance
    balance = db.execute("SELECT cash FROM users WHERE id = :nameid", nameid=username)
    balanceDict = balance[0]
    curBalance = round(float(balanceDict["cash"]),2)
    # update user's balance after sell
    balanceUpd = curBalance + SellValue*(-1)
    balanceUpdf = format(balanceUpd, '.2f')
    crsr.execute(f"UPDATE users SET cash = '{balanceUpd}' WHERE id = {username}")
    connection.commit()

    # Redirect user to home page after completion of the transaction
    # return redirect("/")
    return render_template("sold.html", price = curPrice2f, shares = sharesSell, balance=balanceUpdf, total=totalf)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
