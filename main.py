from flask import Flask, render_template,request , redirect, flash
from flask_login import current_user, LoginManager, login_user, login_required

import pymysql

from dynaconf import Dynaconf

app = Flask(__name__)

 
config = Dynaconf(settings_file=["settings.toml"])

app.secret_key = config.secret_key

login_manager = LoginManager(app)

class User:
    is_authenticated = True
    is_active = True
    is_anonymous = False

    def __init__(self,result):
        self.name = result["Name"]
        self.email = result ['Email']
        self.address = result ['Address']
        self.id = result ['ID']
    def get_id(self):
        return str(self.id)

@login_manager.user_loader

def load_user(user_id):
    connection = connect_db()
    
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM `User` WHERE `ID`= %s", (user_id))

    result = cursor.fetchone()
     
    connection.close()

    if result is None:
        return None
    
    return User(result)



def connect_db():
    conn = pymysql.connect(
        host="db.steamcenter.tech",
        user="dward",
        password= config.password,
        database="dward_doughi_sweets",
        autocommit="True",
        cursorclass= pymysql.cursors.DictCursor
    )
    return conn

@app.route("/")
def index():
    return render_template("homepage.html.jinja")

@app.route("/browse")
def browse():
    connection = connect_db()

    cursor = connection.cursor() 

    cursor.execute("SELECT * FROM `Product` " )

    result = cursor.fetchall()
    
    connection.close()

    return render_template("browse.html.jinja", products=result)

@app.route("/product/<product_id>")
def product(product_id):
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM `Product` WHERE `ID` = %s", (product_id) )

    result = cursor.fetchone()
    
    connection.close()

    return render_template("product.html.jinja", product=result)

@app.route("/login",methods =['POST','GET'])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        connection = connect_db()

        cursor = connection.cursor()
       
        cursor.execute("SELECT * FROM `User` WHERE `Email` = %s", (email))

        result = cursor.fetchone()

        print(result)
        
        if result is None:
           flash("No user is found")
        elif password != result["Password"]:
           flash("Incorrect password")
        else:
            login_user(User(result))
            return redirect("/browse")
    

    return render_template("login.html.jinja")





@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        address = request.form["address"]

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect("/register")

        if len(password) < 8:
            flash("Password is too short")
            return redirect("/register")
        else:
            connection = connect_db()
            cursor = connection.cursor()

            try:
                cursor.execute("""
                    INSERT INTO User (Name, Email, Password, Address)
                    VALUES (%s, %s, %s, %s)
                """, (name, email,password,address))
                connection.commit()
            except pymysql.err.IntegrityError:
                flash("User with that email already exists")
                return redirect("/register")
            finally:
                connection.close()

            flash("Account created successfully! Please log in.")
            return redirect("/login")

    return render_template("register.html.jinja")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out! Thanks for shopping")
    return redirect("/login")
