import gc
import redis
import random
import smtplib
from functools import wraps
from dbconnect import Connection
from flask_session import Session
from passlib.hash import sha256_crypt
from email.message import EmailMessage
from content_management import Content
from datetime import datetime,timedelta
from MySQLdb import escape_string as thwart
from indexing import index_things, get_indexed_array
from flask import Flask, render_template, request, url_for, redirect, session, g, make_response, send_from_directory


TOPIC_ARRAY = Content()

app = Flask(__name__)
app.secret_key = "123456789012345678901234"
SECRET_KEY = '123456789012345678901234'
SESSION_TYPE = 'redis'
SESSION_REDIS = redis.from_url('redis://localhost:6379')
app.config.from_object(__name__)
app.jinja_env.filters['zip'] = zip
sess = Session(app)
sess.init_app(app)
index_things()


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.logged_in:
            return f(*args, **kwargs)
        else:
            return redirect(url_for("login"))

    return wrap


def sign_up_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if g.status:
            return f(*args, **kwargs)
        else:
            return redirect(url_for("signup"))
            
    return wrap


@app.before_request
def before_request():
    g.user = None
    g.logged_in = False
    g.status = None
    g.mail = None

    try:
        if "username" in session:
            g.user = session["username"]
        if "email" in session:
            g.mail = session["email"]
        if "status" in session:
            g.status = session["status"]
        if "logged_in" in session:
            g.logged_in = True
    except:
        pass


@app.route('/', methods=['GET', 'POST'])
def homepage():
    try:
        if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))
            # return render_template('signup.html', umessage=INDEXED_ARRAY)
            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

        else:
            return render_template("main.html",
                                   TOPIC_ARRAY=TOPIC_ARRAY,
                                   main_topic="Solution ERA",
                                   sub_topic="One stop solution to all your problems!")


    except Exception as e:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=str(unsuccessful))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    try:
        if (request.method == 'POST'):
            try:
                email = request.form['name']
                c, conn = Connection()
                similar_emails_in_db = c.execute("SELECT password, business_name, rank FROM users WHERE email = (%s)", [thwart(str(email)),])
                if int(similar_emails_in_db) > 0:
                    password, business_name, rank = c.fetchall()[0]
                    if sha256_crypt.verify(str(request.form['password']), password):
                        # rank: 100 payment left plan not selected, 101 payment left plan selected, 110 payment inquired, 111 in plan, 011 plan expired.
                        if rank == "100":
                            session["username"] = str(email).split("@")[0]
                            session["email"] = str(email)
                            session["status"] = "100"
                            unsuccessful = "You have not selected a plan yet!!!"
                            return render_template('login.html', umessage=unsuccessful)
                        elif rank == "101":
                            session["username"] = str(email).split("@")[0]
                            session["email"] = str(email)
                            session["status"] = "101"
                            unsuccessful = "You have not payed for your selected plan yet!!!"
                            return render_template('login.html', umessage=unsuccessful)
                        elif rank == "110":
                            session["username"] = str(email).split("@")[0]
                            session["email"] = str(email)
                            session["status"] = "110"
                            unsuccessful = "Please wait while We Verify Your Payment."
                            return render_template('login.html', umessage=unsuccessful)
                        elif rank == "011":
                            session["username"] = str(email).split("@")[0]
                            session["email"] = str(email)
                            session["status"] = "011"
                            unsuccessful = "Your Plan has been Expired Please Renew it!!!"
                            return render_template('login.html', umessage=unsuccessful)
                        else:
                            session["username"] = str(email).split("@")[0]
                            session["email"] = str(email)
                            session["status"] = "111"
                            session["logged_in"] = True
                            return redirect(url_for("dashboard"))
                    else:
                        unsuccessful = 'Incorrect Password!!!'
                        return render_template('login.html', umessage=unsuccessful)

                unsuccessful = 'Email is not Registered!!!'
                return render_template('login.html', umessage=unsuccessful)
                
            except:
                searched_term = request.form['searched_term']
                INDEXED_ARRAY = get_indexed_array(str(searched_term))

                return render_template("search.html",
                                        INDEXED_ARRAY=INDEXED_ARRAY)

        else:
            return render_template("login.html")
    except:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('login.html', umessage=unsuccessful)


@app.route('/logged_out/', methods=['GET', 'POST'])
@login_required
def log_out():
    try:
        if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))
            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

        else:
            g.user = None
            g.logged_in = False
            g.status = None
            g.mail = None
            try:
                session.pop("username", None)
            except:
                pass
            try:
                session.pop("logged_in", None)
            except:
                pass
            try:
                session.pop("status", None)
            except:
                pass
            try:
                session.pop("email", None)
            except:
                pass
            session.clear()
            gc.collect()

            return render_template('login.html', umessage="Logged Out.", logout=True)

    except:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=unsuccessful)


@app.route('/resetting_password/', methods=['GET', 'POST'])
def resetting_password():
    try:
        if (request.method == 'POST'):
            try:
                email = request.form['name']

                c, conn = Connection()

                email_content = c.execute("SELECT * FROM ForgotPass WHERE email = (%s)", [thwart(str(email))])

                if int(email_content):

                    code = request.form['code']

                    email, code2 = c.fetchall()[0]

                    if str(code) == str(code2):

                        password = sha256_crypt.encrypt((str(request.form['password'])))

                        if len(str(request.form['password2'])) < 6:
                            unsuccessful = 'Please make sure the password is longer than 6 characters!!!'
                            return render_template('resetting_password.html', umessage=unsuccessful)
                        elif not sha256_crypt.verify(str(request.form['password2']), password):
                            unsuccessful = 'Please make sure the password matches to confirm password!!!'
                            return render_template('resetting_password.html', umessage=unsuccessful)

                        c.execute("UPDATE users SET password = (%s) WHERE email = (%s)", [thwart(str(password)), thwart(str(email))])
                        conn.commit()

                        c.execute("DELETE FROM ForgotPass WHERE email = (%s)", [thwart(str(email))])
                        conn.commit()

                        c.close()
                        conn.close()

                        return render_template('login.html', smessage="Password Successfully Changed.", logout=True)

                    else:
                        return render_template("resetting_password.html", umessage="Incorrect Code")
                else:
                    return render_template("forgot_password.html", umessage="Email not registered as Forgot Passwords")


            except:
                searched_term = request.form['searched_term']
                INDEXED_ARRAY = get_indexed_array(str(searched_term))
                return render_template("search.html",
                                        INDEXED_ARRAY=INDEXED_ARRAY)


        return render_template("resetting_password.html")
    except:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=unsuccessful)


@app.route('/forgot_password/', methods=['GET', 'POST'])
def forgot_password_form():
    try:
        if (request.method == 'POST'):
            try:
                email = request.form['name']

                c, conn = Connection()

                content = c.execute("SELECT uid from users WHERE email = (%s)", [thwart(str(email)),])

                if int(content):

                    code = str(random.randint(100000, 999999))

                    c.execute("INSERT INTO ForgotPass (email, code) VALUES (%s, %s)", [thwart(str(email)), thwart(str(code))])
                    conn.commit()

                    c.close()
                    conn.close()

                    EMAIL_ID = "kapilnchauhan77@gmail.com"
                    EMAIL_PASS = "rjgrnnplkhgkxbtt"
                    msg = EmailMessage()
                    msg['Subject'] = 'Details for resetting password'
                    msg['From'] = EMAIL_ID
                    body = f"Enter your email and code given with this email in the following url,\n URL: https://solutionera.tk/resetting_password/ \ncode: {code}"
                    msg['To'] = str(email)
                    msg.set_content(body)
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(EMAIL_ID, EMAIL_PASS)
                        smtp.send_message(msg)

                    successful = "Please check your Email for futher details."
                    return render_template('login.html', smessage=successful, logout=True)

                else:
                    c.close()
                    conn.close()
                    gc.collect()

                    return render_template('signup.html', umessage="Sign Up First!")

            except:
                searched_term = request.form['searched_term']
                INDEXED_ARRAY = get_indexed_array(str(searched_term))
                return render_template("search.html",
                                        INDEXED_ARRAY=INDEXED_ARRAY)


        return render_template("forgot_password.html")
    except:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=unsuccessful)


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    try:
        if (request.method == 'POST'):
            try:
                email = request.form['name']
                business_name = request.form['business_name']
                owner_name = request.form['owner_name']
                industry = request.form['industry']
                business_address = request.form['business_address']
                ph_num = request.form['ph_num']
                password = sha256_crypt.encrypt((str(request.form['password'])))
                try:
                    if len(str(request.form['password2'])) < 6:
                        unsuccessful = 'Please make sure the password is longer than 6 characters!!!'
                        return render_template('signup.html', umessage=unsuccessful)
                    elif not sha256_crypt.verify(str(request.form['password2']), password):
                        unsuccessful = 'Please make sure the password matches to confirm password!!!'
                        return render_template('signup.html', umessage=unsuccessful)
                    else:
                        
                        # password = sha256_crypt.encrypt((str(password)))

                        c, conn = Connection()

                        # rank: 100 payment left plan not selected, 101 payment left plan selected, 110 payment inquired, 111 in plan, 011 plan expired.
                        similar_emails_in_db_with_rank = c.execute("SELECT rank, pricing FROM users WHERE email = (%s)", [thwart(str(email)),])

                        if int(similar_emails_in_db_with_rank) > 0:
                            rank_, pricing_ = c.fetchone()

                            c.close()
                            conn.close()
                            gc.collect()

                            if rank_ == "111":
                                unsuccessful = 'Business Name has already been taken.'
                                return render_template('signup.html', umessage=unsuccessful)

                            elif rank_ == "101":
                                session["username"] = str(email).split("@")[0]
                                session["email"] = str(email)
                                session["status"] = "101"

                                if pricing_ == "85":
                                    return redirect(url_for("register_85"))

                                elif pricing_ == "225":
                                    return redirect(url_for("register_225"))

                                elif pricing_ == "400":
                                    return redirect(url_for("register_400"))

                                elif pricing_ == "600":
                                    return redirect(url_for("register_600"))

                                else:
                                    unsuccessful = 'There is a problem please contact via details in contact page'
                                    return render_template('signup.html', umessage=unsuccessful)

                            elif rank_ == "110":
                                session["username"] = str(email).split("@")[0]
                                session["email"] = str(email)
                                session["status"] = "110"

                                unsuccessful = 'Please wait while we verify your Payment.'
                                return render_template('signup.html', umessage=unsuccessful)

                            elif rank_ == "011":
                                session["username"] = str(email).split("@")[0]
                                session["email"] = str(email)
                                session["status"] = "011"

                                unsuccessful = 'Your Plan has been Expired Please Renew it!!!'
                                return render_template('signup.html', umessage=unsuccessful)

                            elif rank_ == "100":
                                session["username"] = str(email).split("@")[0]
                                session["email"] = str(email)
                                session["status"] = "100"

                                return redirect(url_for("register"))

                            else:
                                unsuccessful = 'There is a problem please contact via details in contact page'
                                return render_template('signup.html', umessage=unsuccessful)

                        similar_businesses_names_in_db = c.execute("SELECT rank FROM users WHERE business_name = (%s)", [thwart(str(business_name)),])

                        if int(similar_businesses_names_in_db) > 0:
                            rank_ = c.fetchone()[0]

                            c.close()
                            conn.close()
                            gc.collect()

                            if rank_ == "111" or rank_ == "110" or rank_ == "011":
                                unsuccessful = 'Business Name has already been taken.'
                                return render_template('signup.html', umessage=unsuccessful)

                        else:

                            # rank: 100 payment left plan not selected, 101 payment left plan selected, 110 payment inquired, 111 in plan, 011 plan expired.
                            c.execute("INSERT INTO users (business_name, owner_name, industry, business_address, mobile_number, email, password, rank) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                             [thwart(str(business_name)), thwart(str(owner_name)), thwart(str(industry)), thwart(str(business_address)), thwart(str(ph_num)), thwart(str(email)), thwart(str(password)), thwart(str(100))])
                            conn.commit()

                            c.close()
                            conn.close()
                            gc.collect()


                            session["username"] = str(email).split("@")[0]
                            session["email"] = str(email)
                            session["status"] = "100"
     
                            return redirect(url_for("register"))
                        return render_template('signup.html', umessage="There is a problem please contact via details in contact page")
                except:
                    unsuccessful = 'There is a problem please contact via details in contact page'
                    # unsuccessful = str(e)
                    return render_template('signup.html', umessage=unsuccessful)

            except:
                searched_term = request.form['searched_term']
                INDEXED_ARRAY = get_indexed_array(str(searched_term))
                return render_template("search.html",
                                        INDEXED_ARRAY=INDEXED_ARRAY)
                
        return render_template("signup.html")
    except:
        unsuccessful = 'There is a problem please contact via details in contact page'
        # unsuccessful = str(e)
        return render_template('signup.html', umessage=unsuccessful)


@app.route('/register/', methods=['GET', 'POST'])
@sign_up_required
def register():
    try:
        if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))
            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

        else:
            session["status"] = "100"
            return render_template("register.html")
    except:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=unsuccessful)


@app.route('/register_85/', methods=['GET', 'POST'])
@sign_up_required
def register_85():
    try:
        if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))
            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

        else:
            c, conn = Connection()

            c.execute("UPDATE users SET pricing = '85' WHERE email = (%s)", [thwart(str(g.mail)),])
            c.execute("UPDATE users SET rank = '101' WHERE email = (%s)", [thwart(str(g.mail)),])

            conn.commit()

            c.close()
            conn.close()

            return render_template('pricing.html',
                                   price="₹85",
                                   heading="1 Month Membership",
                                   subheading="With all the benefits mentioned previously.",
                                   membership=True)
    except:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=unsuccessful)


@app.route('/pricing/', methods=['GET', 'POST'])
def pricing():
    try:
        if (request.method == 'POST'):
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            membership = request.form['membership']

            if membership == "yes":
                paymentMethod = request.form['paymentMethod']
                if paymentMethod == "cash":

                    mail = g.mail

                    c, conn = Connection()

                    c.execute("SELECT business_name, mobile_number, owner_name, industry, business_address, pricing FROM users WHERE email = (%s)",
                        [thwart(str(mail))])

                    business_name, mobile_number, owner_name, industry, business_address, pricing = c.fetchall()[0]

                    c.execute("UPDATE users set rank = '110' WHERE email = (%s)",
                        [thwart(str(mail))])

                    conn.commit()

                    c.close()
                    conn.close()


                    EMAIL_ID = "kapilnchauhan77@gmail.com"
                    EMAIL_PASS = "rjgrnnplkhgkxbtt"
                    msg = EmailMessage()
                    msg['Subject'] = 'Get Payment from this Client'
                    msg['From'] = EMAIL_ID
                    body = f"First Name: {first_name}, Last Name: {last_name}, Business Name: {business_name}, Mob. No.: {mobile_number}, Owner Name: {owner_name}, Industry: {industry}, Add.: {business_address}, Plan Selected: {pricing}"
                    msg['To'] = "kapilnchauhan77@gmail.com", "nishant6625@gmail.com", "darshitjagetiya888@gmail.com"
                    msg.set_content(body)
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(EMAIL_ID, EMAIL_PASS)
                        smtp.send_message(msg)

                    return render_template("login.html", smessage="Please wait our Executives will Contact you Shortly", logout=True)

                elif paymentMethod == "paypal":
                    pass
            elif membership == "no":
                ph_num = request.form['ph_num']
                PhoneNumber = request.form['PhoneNumber']
                product_name = request.form['product_name']
                EMAIL_ID = "kapilnchauhan77@gmail.com"
                EMAIL_PASS = "rjgrnnplkhgkxbtt"
                msg = EmailMessage()
                msg['Subject'] = "Contact via Solution ERA"
                msg['From'] = EMAIL_ID
                body = f"Name: {str(first_name)}, Mobile Number: {str(PhoneNumber)}, has ordered {product_name}, call {ph_num}"
                msg['To'] = "kapilnchauhan77@gmail.com", "nishant6625@gmail.com", "darshitjagetiya888@gmail.com"
                msg.set_content(body)
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(EMAIL_ID, EMAIL_PASS)
                    smtp.send_message(msg)

                return render_template('ordered.html', smessage="Your Order Will Be Delivered Shortly!!!", ph_num=str(ph_num))

            else:
                return render_template('signup.html', umessage=membership)


        else:
            return render_template('signup.html')

    except Exception as e:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=str(unsuccessful))


@app.route('/register_225/', methods=['GET', 'POST'])
@sign_up_required
def register_225():
    try:
        if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))

            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

        else:
            c, conn = Connection()

            c.execute("UPDATE users SET pricing = '225' WHERE email = (%s)", [thwart(str(g.mail)),])
            c.execute("UPDATE users SET rank = '101' WHERE email = (%s)", [thwart(str(g.mail)),])
            
            conn.commit()

            c.close()
            conn.close()
            return render_template('pricing.html',
                               price="₹225",
                               heading="3 Month Membership",
                               subheading="With all the benefits mentioned previously.",
                               membership=True)
    except Exception as e:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=unsuccessful)


@app.route('/register_400/', methods=['GET', 'POST'])
@sign_up_required
def register_400():
    try:
        if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))

            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

        else:
            c, conn = Connection()

            c.execute("UPDATE users SET pricing = '400' WHERE email = (%s)", [thwart(str(g.mail)),])
            c.execute("UPDATE users SET rank = '101' WHERE email = (%s)", [thwart(str(g.mail)),])
            
            conn.commit()

            c.close()
            conn.close()
            return render_template('pricing.html',
                               price="₹400",
                               heading="6 Month Membership",
                               subheading="With all the benefits mentioned previously.",
                               membership=True)
    except:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=unsuccessful)


@app.route('/register_600/', methods=['GET', 'POST'])
@sign_up_required
def register_600():
    try:
        if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))

            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

        else:
            c, conn = Connection()

            c.execute("UPDATE users SET pricing = '600' WHERE email = (%s)", [thwart(str(g.mail)),])
            c.execute("UPDATE users SET rank = '101' WHERE email = (%s)", [thwart(str(g.mail)),])
            
            conn.commit()

            c.close()
            conn.close()
            return render_template('pricing.html',
                               price="₹600",
                               heading="1 Year Membership",
                               subheading="With all the benefits mentioned previously.",
                               membership=True)
    except:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=unsuccessful)


@app.route('/products/', methods=['GET', 'POST'])
def products():
    try:
        if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))

            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

        else:
            return render_template('products.html')
    except:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=unsuccessful)


@app.route('/contact/', methods=['GET', 'POST'])
def contact():
    try:
        if (request.method == 'POST'):

            name_ = request.form['name']
            phone_ = request.form['phone']
            mail_ = request.form['email']
            message_ = request.form['message']

            EMAIL_ID = "kapilnchauhan77@gmail.com"
            EMAIL_PASS = "rjgrnnplkhgkxbtt"
            msg = EmailMessage()
            msg['Subject'] = "Order to Deliver"
            msg['From'] = EMAIL_ID
            body = f"Name: {str(name_)}, Mobile Number: {str(phone_)}, Email id: {str(mail_)}, Message: {str(message_)}"
            msg['To'] = "kapilnchauhan77@gmail.com", "nishant6625@gmail.com", "darshitjagetiya888@gmail.com"
            msg.set_content(body)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_ID, EMAIL_PASS)
                smtp.send_message(msg)

            # return render_template("login.html", smessage="Please wait our Executives will Contact you Shortly", logout=True)
            return render_template('ordered.html', smessage="Please wait our Executives will Contact you Shortly", ph_num=str("+917984147792"))


        return render_template("contact.html")

    except:
        try:
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))

            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)
        except:
            unsuccessful = 'There is a problem please contact via details in contact page'
            return render_template('signup.html', umessage=str(unsuccessful))


@app.route("/mypage/", methods=['GET', 'POST'])
@login_required
def my_page():
    try:
        if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))

            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

        mail = str(g.mail)

        c, conn = Connection()

        c.execute("SELECT business_name FROM users WHERE email = (%s)", [thwart(str(mail)),])

        business_name = str(c.fetchall()[0][0])

        c.execute("SELECT business_url FROM businesses WHERE business_name = (%s)", [thwart(str(business_name)),])

        business_url = str(c.fetchall()[0][0]).replace("-","_").replace(" ","_").replace(",","").replace("/","").replace(")","").replace("(","").replace(".","").replace("!","").replace(":","-").replace("'","")

        c.close()
        conn.close()

        return redirect(url_for(business_url))

    except Exception as e:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=str(unsuccessful))


@app.route('/additionalProduct/', methods=['GET', 'POST'])
@login_required
def additionalProduct():
    try:
        c, conn = Connection()

        c.execute("SELECT business_name FROM users WHERE email = (%s)", [thwart(str(g.mail))])

        business_name = c.fetchall()[0][0]

        c.execute("SELECT BID FROM businesses WHERE business_name = (%s)", [thwart(str(business_name))])

        BID = c.fetchall()[0][0]

        c.close()
        conn.close()

        return render_template("add_product.html", BID=BID)

    except:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=unsuccessful)


@app.route('/addProduct/', methods=['GET', 'POST'])
@login_required
def addProduct():
    try:
        product_name = request.form['product_name']
        product_img_url = request.form['product_img']
        product_price = "Rs. " + str(request.form['product_price'])
        BID = request.form['BID']

        c, conn = Connection()

        c.execute("INSERT INTO products (BID, product_name, product_price, product_img_url, visit_count) VALUES (%s, %s, %s, %s, %s);",
             [thwart(str(BID)), thwart(str(product_name)), thwart(str(product_price)), thwart(str(product_img_url)), 0,])
        conn.commit()

        c.close()
        conn.close()

        EMAIL_ID = "kapilnchauhan77@gmail.com"
        EMAIL_PASS = "rjgrnnplkhgkxbtt"
        msg = EmailMessage()
        msg['Subject'] = 'Contact Kapil !!!! This product has to be added!'
        msg['From'] = EMAIL_ID
        body = f"product to add: {product_name}, tmg: {product_img_url}, price: {product_price}, businesses id: {BID}"
        msg['To'] = "kapilnchauhan77@gmail.com", "nishant6625@gmail.com", "darshitjagetiya888@gmail.com"
        msg.set_content(body)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ID, EMAIL_PASS)
            smtp.send_message(msg)

        # index_things()

        # create_init()

        # return redirect(url_for("dashboard"))
        return render_template("product_reviewing.html", smessage="Your Product will be added Shortly after reviewed by our Executives.", ph_num="+917984147792")

    except:
        try:
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))

            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)
        except:
            unsuccessful = 'There is a problem please contact via details in contact page'
            return render_template('signup.html', umessage=str(unsuccessful))


@app.route('/updateBusiness/', methods=['GET', 'POST'])
@login_required
def updateBusiness():
    try:
        if (request.method == 'POST'):
            ch_business_name = request.form['business_name']
            business_url = str(ch_business_name).replace("-","_").replace(" ","_").replace(",","").replace("/","").replace(")","").replace("(","").replace(".","").replace("!","").replace(":","-").replace("'","")
            business_url = f"/{business_url}/"
            business_img_url = request.form['business_img']
            ph_num = request.form['ph_num']
            email_id = request.form['name']

            c, conn = Connection()

            c.execute("SELECT business_name FROM users WHERE email = (%s)", [thwart(str(g.mail))])

            business_name = c.fetchall()[0][0]

            c.execute("UPDATE businesses SET business_url=(%s) WHERE business_name = (%s)", [thwart(str(business_url)), thwart(str(business_name)),])            
            c.execute("UPDATE businesses SET business_img_url=(%s) WHERE business_img_url = (%s)", [thwart(str(business_img_url)), thwart(str(business_name)),])            
            c.execute("UPDATE businesses SET ph_num=(%s) WHERE ph_num = (%s)", [thwart(str(ph_num)), thwart(str(business_name)),])
            c.execute("UPDATE businesses SET email_id=(%s) WHERE email_id = (%s)", [thwart(str(email_id)), thwart(str(business_name)),])                        
            c.execute("UPDATE businesses SET business_name=(%s) WHERE business_name = (%s)", [thwart(str(ch_business_name)), thwart(str(business_name)),]) 

            conn.commit()
            c.close()
            conn.close()

            return redirect(url_for("dashboard"))
            # return render_template("product_reviewing.html")


        c, conn = Connection()

        c.execute("SELECT business_name FROM users WHERE email = (%s)", [thwart(str(g.mail)),])

        business_name = c.fetchall()[0][0]

        c.execute("SELECT ph_num FROM businesses WHERE business_name = (%s)", [thwart(str(business_name)),])

        ph_num = c.fetchall()[0][0]

        c.close()
        conn.close()

        return render_template('update_business.html', business_name=business_name, ph_num=ph_num, mail=str(g.mail))

    except:
        try:
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))

            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)
        except:
            unsuccessful = 'There is a problem please contact via details in contact page'
            return render_template('signup.html', umessage=str(unsuccessful))



@app.route('/addBusiness/', methods=['GET', 'POST'])
@login_required
def addBusiness():
    try:
        business_name = request.form['business_name']
        business_url = str(business_name).replace("-","_").replace(" ","_").replace(",","").replace("/","").replace(")","").replace("(","").replace(".","").replace("!","").replace(":","-").replace("'","")
        business_url = f"/{business_url}/"
        business_img_url = request.form['business_img']
        ph_num = request.form['ph_num']
        email_id = request.form['name']
        industry = request.form['industry']

        c, conn = Connection()

        content = c.execute("SELECT SID FROM services WHERE service_name = (%s)", [thwart(str(industry))])

        if int(content):
            SID = c.fetchall()[0][0]

            c.execute("INSERT INTO businesses (SID, business_name, business_url, business_img_url, ph_num, email_id, visit_count) VALUES (%s, %s, %s, %s, %s, %s, %s);",
                 [thwart(str(SID)), thwart(str(business_name)), thwart(str(business_url)), thwart(str(business_img_url)), thwart(str(ph_num)), thwart(str(email_id)), 0,])
            conn.commit()

            c.execute("SELECT BID FROM businesses WHERE business_name = (%s)", [thwart(str(business_name))])

            BID = str(c.fetchall()[0][0])

            c.close()
            conn.close()

            return render_template("add_product.html", BID=BID)

        else:
            c.close()
            conn.close()

            EMAIL_ID = "kapilnchauhan77@gmail.com"
            EMAIL_PASS = "rjgrnnplkhgkxbtt"
            msg = EmailMessage()
            msg['Subject'] = 'Contact Kapil !!!! This service has to be added!'
            msg['From'] = EMAIL_ID
            body = f"Service to add: {industry} for businesses: {business_name}, Mobile Number: {ph_num}, Email: {email_id}"
            msg['To'] = "kapilnchauhan77@gmail.com", "nishant6625@gmail.com", "darshitjagetiya888@gmail.com"
            msg.set_content(body)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_ID, EMAIL_PASS)
                smtp.send_message(msg)

            # return render_template("signup.html", smessage="Please wait till we add your area of service, our Executives will Contact you Shortly")
            return render_template("product_reviewing.html", smessage="Please wait till we add your area of service, our Executives will Contact you Shortly", ph_num="+917984147792")

    except Exception as e:
        try:
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))

            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)
        except Exception as e:
            unsuccessful = 'There is a problem please contact via details in contact page'
            return render_template('signup.html', umessage=str(unsuccessful))



@app.route('/dashboard/', methods=['GET', 'POST'])
@login_required
def dashboard():
    try:
        if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))

            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)
        c, conn = Connection()

        c.execute("SELECT business_name FROM users WHERE email = (%s)", [thwart(str(g.mail)),])

        business_name = c.fetchall()[0][0]

        content = c.execute("SELECT SID, BID, visit_count FROM businesses WHERE business_name = (%s)", [thwart(str(business_name)),])

        if int(content):

            data = c.fetchall()

            SID = data[0][0]

            BID = data[0][1]

            business_visit_count = data[0][2]

            c.execute("SELECT visit_count, service_name FROM services WHERE SID = (%s)", [thwart(str(SID)),])

            data = c.fetchall()

            service_name = data[0][1]

            service_visit_count = data[0][0]

            c.execute("SELECT visit_count, product_name FROM products WHERE BID = (%s)", [thwart(str(BID)),])

            products = []
            product_visit_counts = []

            for info in c.fetchall():
                products.append(info[1])
                product_visit_counts.append(info[0])

            labels = [service_name] + [business_name] + products
            visits = [service_visit_count] + [business_visit_count] + product_visit_counts

            c.close()
            conn.close()

            return render_template('dashboard.html', labels=labels, visits=visits)

        else:
            c.execute("SELECT mobile_number FROM users WHERE email = (%s)", [thwart(str(g.mail)),])

            ph_num = c.fetchall()[0][0]

            c.execute("SELECT industry FROM users WHERE email = (%s)", [thwart(str(g.mail)),])

            industry = c.fetchall()[0][0]

            c.close()
            conn.close()

            return render_template('add_business.html', business_name=business_name, ph_num=ph_num, mail=str(g.mail), industry=str(industry))

    except Exception as e:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('login.html', umessage=str(unsuccessful))


@app.errorhandler(500)
def page_not_found2(e):
    if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))

            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

    else:
        unsuccessful = 'There is a problem please contact via details in contact page'
        return render_template('signup.html', umessage=str(unsuccessful))


@app.errorhandler(404)
def page_not_found(e):
    try:
        if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))

            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

        else:
            return render_template("404.html")
    except:
        return(str(e))


@app.route('/robots.txt/')
def robots():
    return("User-agent: *\nDisallow: /register/\nDisallow: /login/")


@app.route('/sitemap.xml/', methods=['GET'])
def sitemap():
    try:
      """Generate sitemap.xml. Makes a list of urls and date modified."""
      pages=[]
      ten_days_ago=(datetime.now() - timedelta(days=7)).date().isoformat()
      # static pages
      for rule in app.url_map.iter_rules():
          if "GET" in rule.methods and len(rule.arguments)==0:
              pages.append(
                           ["https://solutionera.tk"+str(rule.rule),ten_days_ago]
                           )

      sitemap_xml = render_template('sitemap_template.xml', pages=pages)
      response= make_response(sitemap_xml)
      response.headers["Content-Type"] = "application/xml"    
    
      return response
    except Exception as e:
        return(str(e))



@app.route(TOPIC_ARRAY[0][1], methods=['GET', 'POST'])
def Tuition_Classes():
    if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))
            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

    else:

        c, conn = Connection()

        c.execute("UPDATE services SET visit_count = visit_count + 1 WHERE service_url = (%s)", [thwart(str(TOPIC_ARRAY[0][1]))])
        conn.commit()

        c.close()
        conn.close()

        return render_template("main.html", TOPIC_ARRAY=TOPIC_ARRAY[0][3], url_for_image= TOPIC_ARRAY[0][2], main_topic=TOPIC_ARRAY[0][0])

    

@app.route(TOPIC_ARRAY[0][3][0][1], methods=['GET', 'POST'])
def Shubham_Classes():
    if (request.method == 'POST'):
        try:
            money = request.form['money']
            HEADING = request.form['HEADING']
            IMAGE_URL = request.form['IMAGE_URL']
            
            c, conn = Connection()

            c.execute("UPDATE products SET visit_count = visit_count + 1 WHERE product_img_url = (%s) AND product_name = (%s) AND product_price = (%s)", [thwart(str(IMAGE_URL)), thwart(str(HEADING)), thwart(str(money))])
            conn.commit()

            c.execute("SELECT ph_num FROM businesses WHERE business_url = (%s)", [thwart(str(TOPIC_ARRAY[0][3][0][1]))])

            ph_num = str(c.fetchall()[0][0])

            c.close()
            conn.close()

            return render_template('pricing.html',
                                   price=str(money),
                                   heading= HEADING,
                                   ph_num=ph_num)

        except:
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))
            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)


    else:

        c, conn = Connection()

        c.execute("UPDATE businesses SET visit_count = visit_count + 1 WHERE business_url = (%s)", [thwart(str(TOPIC_ARRAY[0][3][0][1]))])
        conn.commit()

        c.close()
        conn.close()

        return render_template("main.html", price=True, TOPIC_ARRAY=TOPIC_ARRAY[0][3][0][5], url_for_image= TOPIC_ARRAY[0][3][0][2] ,main_topic=TOPIC_ARRAY[0][3][0][0], ph_contact=TOPIC_ARRAY[0][3][0][3], email_contact=TOPIC_ARRAY[0][3][0][4])
        
    

@app.route(TOPIC_ARRAY[0][3][1][1], methods=['GET', 'POST'])
def Science_Tuition():
    if (request.method == 'POST'):
        try:
            money = request.form['money']
            HEADING = request.form['HEADING']
            IMAGE_URL = request.form['IMAGE_URL']
            
            c, conn = Connection()

            c.execute("UPDATE products SET visit_count = visit_count + 1 WHERE product_img_url = (%s) AND product_name = (%s) AND product_price = (%s)", [thwart(str(IMAGE_URL)), thwart(str(HEADING)), thwart(str(money))])
            conn.commit()

            c.execute("SELECT ph_num FROM businesses WHERE business_url = (%s)", [thwart(str(TOPIC_ARRAY[0][3][1][1]))])

            ph_num = str(c.fetchall()[0][0])

            c.close()
            conn.close()

            return render_template('pricing.html',
                                   price=str(money),
                                   heading= HEADING,
                                   ph_num=ph_num)

        except:
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))
            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)


    else:

        c, conn = Connection()

        c.execute("UPDATE businesses SET visit_count = visit_count + 1 WHERE business_url = (%s)", [thwart(str(TOPIC_ARRAY[0][3][1][1]))])
        conn.commit()

        c.close()
        conn.close()

        return render_template("main.html", price=True, TOPIC_ARRAY=TOPIC_ARRAY[0][3][1][5], url_for_image= TOPIC_ARRAY[0][3][1][2] ,main_topic=TOPIC_ARRAY[0][3][1][0], ph_contact=TOPIC_ARRAY[0][3][1][3], email_contact=TOPIC_ARRAY[0][3][1][4])
        
    

@app.route(TOPIC_ARRAY[0][3][2][1], methods=['GET', 'POST'])
def Math_Tuition():
    if (request.method == 'POST'):
        try:
            money = request.form['money']
            HEADING = request.form['HEADING']
            IMAGE_URL = request.form['IMAGE_URL']

            c, conn = Connection()

            c.execute("UPDATE products SET visit_count = visit_count + 1 WHERE product_img_url = (%s) AND product_name = (%s) AND product_price = (%s)", [thwart(str(IMAGE_URL)), thwart(str(HEADING)), thwart(str(money))])
            conn.commit()

            c.execute("SELECT ph_num FROM businesses WHERE business_url = (%s)", [thwart(str(TOPIC_ARRAY[0][3][2][1]))])

            ph_num = str(c.fetchall()[0][0])

            c.close()
            conn.close()

            return render_template('pricing.html',
                                   price=str(money),
                                   heading= HEADING,
                                   ph_num=ph_num)


        except:
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))
            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)


    else:

        c, conn = Connection()

        c.execute("UPDATE businesses SET visit_count = visit_count + 1 WHERE business_url = (%s)", [thwart(str(TOPIC_ARRAY[0][3][2][1]))])
        conn.commit()

        c.close()
        conn.close()

        return render_template("main.html", price=True, TOPIC_ARRAY=TOPIC_ARRAY[0][3][2][5], url_for_image= TOPIC_ARRAY[0][3][2][2] ,main_topic=TOPIC_ARRAY[0][3][2][0], ph_contact=TOPIC_ARRAY[0][3][2][3], email_contact=TOPIC_ARRAY[0][3][2][4])
        
    

@app.route(TOPIC_ARRAY[1][1], methods=['GET', 'POST'])
def Electricians():
    if (request.method == 'POST'):
            searched_term = request.form['searched_term']
            INDEXED_ARRAY = get_indexed_array(str(searched_term))
            return render_template("search.html",
                                    INDEXED_ARRAY=INDEXED_ARRAY)

    else:

        c, conn = Connection()

        c.execute("UPDATE services SET visit_count = visit_count + 1 WHERE service_url = (%s)", [thwart(str(TOPIC_ARRAY[1][1]))])
        conn.commit()

        c.close()
        conn.close()

        return render_template("main.html", TOPIC_ARRAY=TOPIC_ARRAY[1][3], url_for_image= TOPIC_ARRAY[1][2], main_topic=TOPIC_ARRAY[1][0])
