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
    connection = connect_db()

    cursor = connection.cursor() 

    cursor.execute("SELECT * FROM `Product` " )

    result = cursor.fetchall()
    
    connection.close()

    return render_template("homepage.html.jinja", products=result)

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

    cursor.execute("""
      SELECT * FROM `Review` 
      JOIN `User` ON `User`.`ID` = `Review`.`UserID`
      WHERE `ProductID` = %s
      """, (product_id)) 
    
    reviews = cursor.fetchall()
    
    connection.close()
    
    if reviews:
        average_rating = round(sum(review["Rating"] for review in reviews) / len(reviews), 1)
    else:
        average_rating = 0 
    
    return render_template("product.html.jinja", product=result, reviews=reviews, average_rating=average_rating)


@app.route("/product/<product_id>/add_to_cart", methods=["POST"])
@login_required
def add_to_cart(product_id):
  quantity = request.form["Qty"]

  connection = connect_db()
  cursor = connection.cursor()


  cursor.execute("""
    INSERT INTO `Cart` (`Quantity`, `ProductID`, `UserID`)
    VALUES(%s, %s, %s)
    ON DUPLICATE KEY UPDATE
    `Quantity` = `Quantity` + %s
 """, (quantity, product_id, current_user.id, quantity))
  
  connection.close()

  return redirect("/cart")

@app.route("/product/<product_id>/review", methods=["POST"])
@login_required
def add_review(product_id):
    #get input vale from form 
    rating = request.form["rating"]
    comment = request.form["comment"]
   
   
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
      INSERT INTO `Review`
             (`Rating`, `Comments`,`UserID`,`ProductID`)
       VALUES
            (%s,%s,%s,%s)
      """,(rating,comment,current_user.id,product_id))
    
    

    connection.close()


    return redirect(f"/product/{product_id}")



@app.route("/cart")
@login_required
def cart():
     

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM `Cart`
        JOIN `Product` ON `Product`.`ID` = `Cart`.`ProductID`
        WHERE `UserID` = %s
    """, (current_user.id))
                 

    results = cursor.fetchall()
    connection.close()

    total=0
    for item in results:
      total = total + item["Price"] * item["Quantity"] 

    return render_template("cart.html.jinja", cart=results, total=total)

from flask import redirect, url_for

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(""" 
        SELECT * FROM `Cart`
        JOIN `Product` ON `Product`.`ID` = `Cart`.`ProductID`
        WHERE `UserID` = %s """ , (current_user.id,))
    
    results = cursor.fetchall()

    if request.method == "POST":
        # Create sale
        cursor.execute(
            "INSERT INTO `Sale` (`UserID`) VALUES (%s)",
            (current_user.id,)
        )
        sale_id = cursor.lastrowid

        # Store purchased products
        for item in results:
            cursor.execute("""
                INSERT INTO `SaleCart`
                (`SaleID`, `ProductID`, `Quantity`)
                VALUES (%s, %s, %s)
            """, (sale_id, item["ProductID"], item["Quantity"]))

        # Empty cart
        cursor.execute(
            "DELETE FROM `Cart` WHERE `UserID` = %s",
            (current_user.id,)
        )

        connection.commit()
        connection.close()

        # Redirect to thank-you page
        return redirect("/thank-you")

    connection.close()

    # Calculate total for GET
    total = sum(item["Price"] * item["Quantity"] for item in results)

    return render_template(
        "checkout.html.jinja",
        cart=results,
        total=total
    )

@app.route("/thank-you")
def thank():
    return render_template("thankyou.html.jinja")


@app.route("/cart/<product_id>/update_qty", methods=["POST"])
@login_required
def update_cart(product_id):
   
   new_qty = request.form["Qty"]

   connection = connect_db()
   cursor = connection.cursor()

   cursor.execute("""
      UPDATE `Cart`
      SET `Quantity` = %s
      WHERE `ProductID` = %s AND `UserID` = %s 
    """, (new_qty, product_id, current_user.id))
   

   connection.close()

   return redirect("/cart")


@app.route('/cart/<product_id>/delete_item', methods=["POST"])
@login_required
def delete_cart_item(product_id):

   connection = connect_db()
   cursor = connection.cursor()

   cursor.execute("""
       DELETE FROM Cart
       WHERE ProductID = %s AND UserID = %s
   """, (product_id, current_user.id))

   connection.close()
   flash("Item removed")
   return redirect('/cart')

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

@app.route("/orders")
@login_required
def order():
     
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""            
        SELECT
           `Sale`.`ID`,
           `Sale`.`Timestamp`,
            SUM(`SaleCart`.`Quantity` ) AS 'Quantity',
            SUM(`SaleCart`.`Quantity` * `Product`.`Price`) AS 'Total'
        FROM `Sale`
        JOIN `SaleCart` ON `SaleCart`.`SaleID` = `Sale`.`ID`
        JOIN `Product` ON `Product`.`ID` = `SaleCart`.`ProductID`          
        WHERE `UserID` = %s
        GROUP BY `Sale`.`ID`
    """, (current_user.id))

    results = cursor.fetchall()
    connection.close()

    return render_template("orders.html.jinja", orders = results)

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html.jinja")


