import stripe
from flask import Flask, request, session, render_template, flash, redirect, url_for, make_response
from datetime import datetime, date
from helpers import login_required, LoginForm, RegistrationForm, AnalysisForm, EditProfileForm
from flask_session import Session
from tempfile import mkdtemp
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from random import randint
from dateutil import relativedelta

# Configuring the app
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

app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///amends.db'
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['STRIPE_PUBLIC_KEY'] = 'pk_test_51LmEDfSFUfAhVJjSNBugyGdCABuv3ykqWLa6mlpTdmQtGiutUr42jF4WDnoCFTuEKmoGViub2fzzi44T9Rhuu0KI00f8yURsW7'
app.config['STRIPE_SECRET_KEY'] = 'sk_test_51LmEDfSFUfAhVJjSLK6q61X16R19DIaeDEQnHAJj6PBEa9aqfiJo2n7qYfylYdRGMu2g9IGYTyf2WhPHsTAK9m4300Yu3xP7oI'


stripe.api_key = app.config['STRIPE_SECRET_KEY']

Session(app)

# Configuring the Database
db = SQL('sqlite:///amends.db')


# ROUTES
@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            # Getting Data from Form
            username = str(form.username.data)
            email = str(form.email.data)
            phone_no = request.form.get("phone_no")

            # Checking if the username and email already exists
            user_check = db.execute("SELECT username FROM users WHERE username = ?;", username)
            email_check = db.execute("SELECT email FROM users WHERE email = ?;", email)
            if user_check and email_check:
                flash("Username or Email already exists!", "danger")
                return redirect('/register')


            # If the username and email doesn't exist, add new user
            hashed_pwd = generate_password_hash(form.password.data)
            db.execute("INSERT INTO users (username, email, password, phone_no) VALUES (?,?,?,?);", username, email, hashed_pwd, phone_no)
            return redirect("/login")
        return render_template('register.html', title='Register', form=form)
    else:
        return render_template('register.html', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            # Getting data from Form
            email = str(form.email.data)
            password = str(form.password.data)

            # Checking if user exists
            email = db.execute("SELECT email, id FROM users WHERE email = ?;", email)
            if email:
                # If the user exists
                user_password = db.execute("SELECT password FROM users WHERE email = ?;", email[0]['email'])
                user_password = user_password[0]['password']

                # Checking if password and email match
                if email and check_password_hash(user_password, password):
                    # Remember which user has logged in
                    session['user_id'] = email[0]['id']

                    return redirect(url_for("dashboard"))
                else:
                    flash("Incorrect Password!", "danger")
                    return redirect("/login")
            else:
                flash("Invalid Email!", "danger")
                return redirect("/login")

        return render_template('login.html', title='Login', form=form)

    else:
        return render_template('login.html', title='Login', form=form)

@login_required
@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for('login'))



@app.route("/dashboard")
@app.route("/")
@login_required
def dashboard():
    # Data for Upcoming Dues Section
    dues = db.execute("SELECT * FROM dues WHERE user_id = ?;", 1)

    # Data for Frequently Bought Section
    # You have to calculate the VARIANCE HERE!!!!-------------
    frequent_data = db.execute("SELECT name, month, total_price, COUNT(name) FROM payments GROUP BY name HAVING COUNT(name) > 2 AND user_id = ? AND status = ?;", session['user_id'], "CLOSED")

    # Data for the Budget
    today = datetime.today()
    month = today.strftime("%b")
    budget = db.execute("SELECT budget FROM budgets WHERE user_id = ? AND month = ?;", session['user_id'], month)

    # Data for Recent Payments
    recent_data = db.execute("SELECT name, amount_paid, pay_date FROM payments WHERE user_id = ? ORDER BY payment_id DESC LIMIT 3;", session['user_id'])

    # Data for Analysis Overview
    amount_spent = db.execute("SELECT total_expense FROM budgets WHERE user_id = ? AND month = ?;", session['user_id'], month)
    most_expensive = db.execute("SELECT month, MAX(total_expense) FROM budgets WHERE user_id = ?;", session['user_id'])
    least_expensive = db.execute("SELECT month, MIN(total_expense) FROM budgets WHERE user_id = ?;", session['user_id'])

    # Data for Monthly Comparison
    last_month = datetime.today() + relativedelta.relativedelta(months=1)
    last_month = last_month.strftime("%b")

    current_month = db.execute("SELECT budget, total_expense, items_count, month FROM budgets WHERE user_id = ? AND month = ?;", session['user_id'], month)
    previous_month = db.execute("SELECT budget, total_expense, items_count, month FROM budgets WHERE user_id = ? AND month = ?;", session['user_id'], last_month)

    return render_template("dashboard.html", dues = dues, frequent_data = frequent_data, budget = budget, recent_data = recent_data, amount_spent = amount_spent,
    most_expensive = most_expensive, least_expensive = least_expensive, current_month_data = current_month, previous_month_data = previous_month, user_id = session['user_id'])



@app.route("/payments/dues", methods = ["GET"])
@login_required
def dues():
    # After the data is sent from the checkout section to the payments table, Get the data with the partial payments and display that here
    records = db.execute("SELECT * FROM dues WHERE user_id = ?;", session['user_id'])
    bill_info = db.execute("SELECT DISTINCT bill_id FROM dues WHERE user_id = ?;", session['user_id'])
    return render_template("payments(dues).html", records = records, bill_info = bill_info)



@app.route("/payments/history", methods = ["GET"])
@login_required
def history():
    # After the data is sent from the checkout section to the payments table, Display all of the data in here
    records = db.execute("SELECT * FROM payments WHERE user_id = ?;", session['user_id'])
    month_info = db.execute("SELECT DISTINCT month FROM payments WHERE user_id = ?;", session['user_id'])
    return render_template("payments(history).html", records = records, month_info = month_info)



@app.route("/analysis", methods = ["POST", "GET"])
@login_required
def compare():
    # After the Payments table and Budgets table are filled with data, the compare section can be filled
    form = AnalysisForm()
    if request.method == "POST":
        if form.validate_on_submit():
            first_month = str(form.first_month.data)
            second_month = str(form.second_month.data)
            print("MONTH NAMES -----------------", first_month[:3], second_month[:3])
            # Retrieving records from the PAYMENTS TABLE
            first_records = db.execute("SELECT name, quantity, total_price FROM payments WHERE month = ? AND user_id = ? AND status='CLOSED';", first_month[:3], session['user_id'])
            second_records = db.execute("SELECT name, quantity, total_price FROM payments WHERE month = ? AND user_id = ? AND status='CLOSED';", second_month[:3], session['user_id'])

            # Retrieving Data for the Description Section
            first_desc = db.execute("SELECT budget, total_expense, items_count FROM budgets WHERE month = ? AND user_id = ?;", first_month[:3], session['user_id'])
            second_desc = db.execute("SELECT budget, total_expense, items_count FROM budgets WHERE month = ? AND user_id = ?;", second_month[:3], session['user_id'])
            print("DATA_-----------------------------------", second_desc)
            print("DATA ---")

            if len(first_desc) == 0 or len(second_desc) == 0:
                return redirect("/analysis")

            profitable = ""
            if first_desc[0]['total_expense'] > second_desc[0]['total_expense']:
                profitable = first_month
            else:
                profitable = second_month

            # Calculating Variance
            price_high_quantity = db.execute("SELECT total_price FROM payments WHERE user_id = ? AND status = 'CLOSED';", session['user_id'])
            print(price_high_quantity)

            return render_template("analysis(compare).html", form = form, first_records = first_records, second_records = second_records, first_desc = first_desc,
            second_desc = second_desc, profitable = profitable)
        else:
            return redirect("/analysis")
    else:
        return render_template("analysis(compare).html", form=form)



@app.route("/products", methods = ["GET"])
@login_required
def products():
    # Get the data from the products table and display it here
    products = db.execute("SELECT * FROM products")
    return render_template("products.html", products = products)


@app.route("/products/cart", methods = ["POST", "GET"])
@login_required
def cart():
    # When the "Add to Cart" is pressed in the products section, the button has to redirect users to this route.
    # When the route is reached via "POST" method, we'll get the data from the form and populate the Cart table with the details of that product
    # We'll be getting the details of the product based on the Product ID taken from the form
    if request.method == "POST":
        product_id = int(request.form.get('product_id'))
        quantity = int(request.form.get('quantity'))
        product_details = db.execute("SELECT * FROM products WHERE product_id = ?", product_id)

        # Checking if the product already exists in Cart
        cart_check = db.execute("SELECT * FROM cart WHERE product_id = ? AND user_id = ?;", product_id, session['user_id'])
        if cart_check:
            db.execute("UPDATE cart SET quantity = quantity + ? WHERE user_id = ? AND product_id = ?;", quantity, session['user_id'], product_id)
            return redirect("/products")

        # Adding items to the Cart
        db.execute("INSERT INTO cart (user_id, product_id, product_name, net_quantity, product_price, exp_date, quantity) VALUES (?,?,?,?,?,?,?);", session['user_id'], product_id,
        product_details[0]['product_name'], product_details[0]['net_quantity'], product_details[0]['product_price'], product_details[0]['exp_date'], quantity)

        return redirect("/products")

    else:
        # When the route is reached via the GET method, we'll just render the "cart.html" with the details in the current cart
        cart_items = db.execute("SELECT * FROM cart WHERE user_id = ?;", session['user_id'])
        return render_template("cart.html", cart_items = cart_items, user_id = session['user_id'])


@app.route("/removeitem", methods=["POST"])
@login_required
def remove_item():
    product_name = request.form.get("product_name")
    quantity = int(request.form.get("quantity"))

    # Checking if cart exists
    cart_check = db.execute("SELECT * FROM cart WHERE user_id = ?;", session['user_id'])
    if not cart_check:
        return redirect("url_for('cart')")

    # Checking for incomplete inputs
    if product_name and quantity:
        current_quantity = db.execute("SELECT quantity FROM cart WHERE product_name = ? AND user_id = ?;", product_name, session['user_id'])
        if int(current_quantity[0]['quantity']) < quantity:
            db.execute("UPDATE cart SET quantity = 0 WHERE product_name = ? AND user_id = ?;", product_name, session['user_id'])
        else:
            db.execute("UPDATE cart SET quantity = quantity - ? WHERE product_name = ? AND user_id = ?;", quantity, product_name, session['user_id'])

    # Removing products with 0 quantity
    db.execute("DELETE FROM cart WHERE quantity = 0 AND user_id = ?;", session['user_id'])
    return redirect("/products/cart")



@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    # When the checkout button is pressed in the cart section, the button has to redirect to this route.
    # The route is only going to accept GET method, when reached, we'll take the user to the Stripe Checkout section.

    #Getting items in the cart
    current_user_id = request.form.get("cart_code")
    cart_items = db.execute("SELECT * FROM cart WHERE user_id = ?;", int(current_user_id))
    bill_id = ""

    # Checking for the type of payment (Partial or Full)
    pay_type = str(request.form.get("pay_type"))
    bill_id = str(request.form.get("bill_id"))
    cart_checkout = []

    if pay_type == "full":
        # Formatting the cart items as per Stripe Format
        # Checking if cart exists
        if not cart_items:
            return redirect("/products/cart")
        for cart_item in cart_items:
            product = {
                'price_data': {
                    'currency': 'inr',
                    'unit_amount': cart_item['product_price'],
                    'product_data': {
                        'name': cart_item['product_name'],
                    },
                },
                'quantity': cart_item['quantity']
            }

            cart_checkout.append(product)

    elif pay_type == "partial":
        # When the payment is partial
        # Checking if cart exists
        if not cart_items:
            return redirect("/products/cart")
        for cart_item in cart_items:
            product = {
                'price_data': {
                    'currency': 'inr',
                    'unit_amount': int(cart_item['product_price'] / 2),
                    'product_data': {
                        'name': cart_item['product_name'],
                    },
                },
                'quantity': cart_item['quantity']
            }

            cart_checkout.append(product)

    else:
        # When the user is trying to Pay a DUE.
        due_items = db.execute("SELECT * FROM dues WHERE user_id = ?;", int(current_user_id))
        for due_item in due_items:
            product = {
                'price_data': {
                    'currency': 'inr',
                    'unit_amount': int(due_item['product_due']),
                    'product_data': {
                        'name': due_item['product_name'],
                    },
                },
                'quantity': 1
            }

            cart_checkout.append(product)


    session = stripe.checkout.Session.create(
        payment_method_types = ['card'],
        line_items = cart_checkout,
        mode = 'payment',
        success_url=url_for('success', _external=True) + f"?pay_type={pay_type}" + f"&bill_id={bill_id}",
        cancel_url=url_for('failure', _external=True),
    )
    return redirect(session.url, code=303)



@app.route("/payment/success", methods = ["POST", "GET"])
@login_required
def success():
    # This route can only be reached when the payment is successful in Stripe
    # When the payment is successful we'll take the values from the Cart table and add them to the payments table and clear the cart.
    # Finally redirect the user to the payments section
    pay_type = request.args.get("pay_type")
    print("PAYMENT TYPE---------------", pay_type)
    cart_items = db.execute("SELECT * FROM cart WHERE user_id = ?;", session['user_id'])
    bill_id = randint(100,999)

    # When the payment method is FULL
    if pay_type == "full":
        pay_date = datetime.today()
        month = pay_date.strftime("%b")

        for cart_item in cart_items:
            total_price = int(cart_item['quantity']) * int(cart_item['product_price'])
            db.execute("INSERT INTO payments (user_id, bill_id, name, quantity, total_price, amount_paid, pay_date, due_date, status, month) VALUES (?,?,?,?,?,?,?,?,?,?);",
            session['user_id'], bill_id, cart_item['product_name'], cart_item['quantity'], total_price, total_price, pay_date, "none", "CLOSED", month)

        # Adding Data to the Budgets table
        item_count = db.execute("SELECT COUNT(*) FROM payments WHERE user_id = ? AND status = 'CLOSED';", session['user_id'])
        total_expense = db.execute("SELECT SUM(amount_paid) FROM payments WHERE user_id = ?;", session['user_id'])

        # Checking if record exists
        budget_check = db.execute("SELECT * FROM budgets WHERE user_id = ? AND month = ?;", session['user_id'], month)
        if budget_check:
            db.execute("UPDATE budgets SET items_count = ?, total_expense = ?;", int(item_count[0]['COUNT(*)']), int(total_expense[0]['SUM(amount_paid)']))
        else:
            db.execute("INSERT INTO budgets (user_id, items_count, total_expense, month) VALUES (?,?,?,?);", session['user_id'], int(item_count[0]['COUNT(*)']), int(total_expense[0]['SUM(amount_paid)']), month)

        # Clearing the cart after inserting values into Respective tables
        db.execute("DELETE FROM cart WHERE user_id = ?;", session['user_id'])

    # When the payment method is PARTIAL
    elif pay_type == "partial":
        pay_date = datetime.today()
        due_date = datetime.today() + relativedelta.relativedelta(months=1)
        month = pay_date.strftime("%b")

        for cart_item in cart_items:
            total_price = int(cart_item['quantity']) * int(cart_item['product_price'])
            amount_paid = total_price / 2

            # Inserting values into the Dues Table
            db.execute("INSERT INTO dues (user_id, bill_id, product_name, product_total, amount_paid, product_due, due_date, pay_date) VALUES (?,?,?,?,?,?,?,?);",
            session['user_id'], bill_id, cart_item['product_name'], total_price, amount_paid, amount_paid, due_date, pay_date)

            # Inserting values into the History(Payments) table
            db.execute("INSERT INTO payments (user_id, bill_id, name, quantity, total_price, amount_paid, pay_date, pay_type, due_date, status, month) VALUES (?,?,?,?,?,?,?,?,?,?,?);",
            session['user_id'], bill_id, cart_item['product_name'], cart_item['quantity'], total_price, amount_paid, pay_date, "partial", due_date, "OPEN", month)

        # Adding Data to the Budgets table
        item_count = db.execute("SELECT COUNT(*) FROM payments WHERE user_id = ? AND status = 'CLOSED';", session['user_id'])
        total_expense = db.execute("SELECT SUM(amount_paid) FROM payments WHERE user_id = ?;", session['user_id'])

        # Checking if record exists
        budget_check = db.execute("SELECT * FROM budgets WHERE user_id = ? AND month = ?;", session['user_id'], month)
        if budget_check:
            db.execute("UPDATE budgets SET items_count = ?, total_expense = ?;", int(item_count[0]['COUNT(*)']), int(total_expense[0]['SUM(amount_paid)']))
        else:
            db.execute("INSERT INTO budgets (user_id, items_count, total_expense, month) VALUES (?,?,?);", session['user_id'], int(item_count[0]['COUNT(*)']), int(total_expense[0]['SUM(amount_paid)']), month)

        # Clearing the cart after inserting values into Respective tables
        db.execute("DELETE FROM cart WHERE user_id = ?;", session['user_id'])

    # When the payment made is to clear a DUE
    else:
        bill_id = request.args.get("bill_id")
        print("BILL ID--------------", bill_id)
        previous_records = db.execute("SELECT * FROM payments WHERE user_id = ? AND bill_id = ?;", session['user_id'], bill_id)
        pay_date = datetime.today()
        due_date = datetime.today() + relativedelta.relativedelta(months=1)
        month = pay_date.strftime("%b")

        # Inserting records into the History(Payments) Table to CLOSE the DUE.
        for record in previous_records:
            db.execute("INSERT INTO payments (user_id, bill_id, name, quantity, total_price, amount_paid, pay_date, pay_type, due_date, status, month) VALUES (?,?,?,?,?,?,?,?,?,?,?);",
            session['user_id'], record['bill_id'], record['name'], record['quantity'], record['total_price'], record['amount_paid'], pay_date, "partial", due_date, "CLOSED", month)


        # Adding Data to the Budgets table
        item_count = db.execute("SELECT COUNT(*) FROM payments WHERE user_id = ? AND status = 'CLOSED';", session['user_id'])
        total_expense = db.execute("SELECT SUM(amount_paid) FROM payments WHERE user_id = ?;", session['user_id'])

        # Checking if record exists
        budget_check = db.execute("SELECT * FROM budgets WHERE user_id = ? AND month = ?;", session['user_id'], month)
        if budget_check:
            db.execute("UPDATE budgets SET items_count = ?, total_expense = ?;", int(item_count[0]['COUNT(*)']), int(total_expense[0]['SUM(amount_paid)']))
        else:
            db.execute("INSERT INTO budgets (user_id, items_count, total_expense, month) VALUES (?,?,?);", session['user_id'], int(item_count[0]['COUNT(*)']), int(total_expense[0]['SUM(amount_paid)']), month)

        # Clearing the Due Record from the Dues table
        db.execute("DELETE FROM dues WHERE user_id = ? AND bill_id = ?;", session['user_id'], bill_id)


    return render_template("success.html")



@app.route("/payment/failure", methods = ["GET"])
@login_required
def failure():
    # When the payment on checkout fails for some reason, do not remove the items from the cart.
    return render_template("failure.html")


@app.route("/products/savelist", methods=["GET"])
@login_required
def shopping_list():
    cart_items = db.execute("SELECT * FROM cart WHERE user_id = ?;", session['user_id'])
    month = datetime.today().strftime("%b")
    if cart_items:
        for cart_item in cart_items:
            db.execute("INSERT INTO shopping_list (user_id, product_name, quantity, month) VALUES (?, ?,?,?);", session['user_id'], cart_item['product_name'], cart_item['quantity'], month)
        return redirect("/products/cart")
    else:
        return redirect("/products/cart")

@app.route("/profile", methods = ["GET", "POST"])
@login_required
def profile():
    user_details = db.execute("SELECT username, email, phone_no, budget FROM users WHERE id = ?;", session['user_id'])
    month = datetime.today().strftime("%b")
    total_expense = db.execute("SELECT total_expense FROM budgets WHERE month = ? AND user_id = ?;", month, session['user_id'])
    try:
        amount_remains = user_details[0]['budget'] - total_expense[0]['total_expense']
    except:
        amount_remains = user_details[0]['budget']

    shopping_lists = db.execute("SELECT DISTINCT month FROM shopping_list WHERE user_id = ? LIMIT 2;", session['user_id'])
    return render_template("profile.html", user_details = user_details, amount_remains = amount_remains, shopping_lists = shopping_lists)

@app.route("/profile/edit", methods = ["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if request.method == "POST":
        if form.validate_on_submit():
            username = str(form.username.data)
            phone_no = int(request.form.get("phone_no"))
            budget = int(form.budget.data)
            month = datetime.today().strftime("%b")
            db.execute("UPDATE users SET username = ?, phone_no = ?, budget = ? WHERE id = ?;", username, phone_no, budget, session['user_id'])
            budget_check = db.execute("SELECT budget FROM budgets WHERE user_id = ? AND month = ?;", session['user_id'], month)
            if budget_check:
                db.execute("UPDATE budgets SET budget = ? WHERE user_id = ? AND month = ?;", budget, session['user_id'], month)
            else:
                db.execute("INSERT INTO budgets (budget, items_count, total_expense, month, user_id) VALUES (?,?,?,?,?);", budget, 0, 0, month, session['user_id'])
            return redirect("/profile")
        else:
            return redirect("/profile")
    else:
        return render_template("editprofile.html", form = form)

@app.route("/contact", methods= ["POST", "GET"])
@login_required
def contact():
    return render_template("contact.html")

@app.route("/profile/lists", methods=["GET", "POST"])
@login_required
def list_display():
    if request.method == "POST":
        list_id = request.form.get("list_id")
        list_data = db.execute("SELECT * FROM shopping_list WHERE month = ? and user_id = ?;", list_id, session['user_id'])

        return render_template("shopping_list.html", list_data = list_data)

if __name__ == "__main__":
  app.run(debug=True, host='0.0.0.0')