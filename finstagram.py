#Import Flask ALibrary
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib

#Initialize the app from Flask
app = Flask(__name__)
SALT = "cs3083salting"

#Configure MySQL
conn = pymysql.connect(host="localhost",
                       port = 8889,
                       user="root",
                       password="root",
                       db="finstagram",
                       charset="utf8mb4",
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route("/")
def hello():
    if "username" in session: return redirect(url_for("home"))
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    username = request.form['username']
    password = request.form['password'] + SALT
    hashed_password = hashlib.sha256(password.encode("utf-8")).hexdigest()

    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, hashed_password))
    data = cursor.fetchone()
    cursor.close()

    error = None
    if(data):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        error = 'Invalid login, please try again'
        return render_template('login.html', error=error)

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password'] + SALT
    hashed_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    email = request.form['email']

    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchone()

    error = None
    if(data):
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, hashed_password, firstName, lastName, email))
        conn.commit()
        cursor.close()
        return render_template('index.html')

@app.route('/home')
def home():
    #user = session['username']
    #cursor = conn.cursor();
    #query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    #cursor.execute(query, (user))
    #data = cursor.fetchall()
    #cursor.close()
    return render_template('home.html', username = session["username"])

### IMPLEMENTATION FUNCTIONS ###
def isLoggedIn():
    pass

def uploadImage():
    pass

@app.route('/addGroup', methods = ["Post"])
#@login.required
def addFriendGroup():
    groupName = request.form['Group Name']
    description = request.form['Description']

    cursor = conn.cursor()
    query = 'SELECT * FROM FriendGroup WHERE groupName = %s AND groupCreator = %s'
    cursor.execute(query, (groupName, session["username"]))
    data = cursor.fetchone()

    error = None
    if(data):
        error = "FrienGroup with this Owner Already Exists"
        return render_template('friend.html', error = error)
    else:
        ins = 'INSERT INTO FriendGroup VALUES(%s, %s, %s)'
        cursor.execute(ins, (groupName, session["username"], description))
        ins = 'INSERT INTO BelongTo VALUES(%s, %s, %s)'
        cursor.execute(ins, (session["username"], groupName, session["username"]))
        conn.commit()
        cursor.close()
        return redirect(url_for("home"))
    

'''
@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor();
    blog = request.form['blog']
    query = 'INSERT INTO blog (blog_post, username) VALUES(%s, %s)'
    cursor.execute(query, (blog, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/select_blogger')
def select_blogger():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    
    cursor = conn.cursor();
    query = 'SELECT DISTINCT username FROM blog'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', user_list=data)

@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor();
    query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    cursor.execute(query, poster)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data)
'''

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
