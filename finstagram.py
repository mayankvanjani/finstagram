#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
from functools import wraps

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
                       autocommit=True,
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

'''
### Check if Logged In ###
def isLoggedIn(f):
    @wraps(f)
    def dec(*args,**kwargs):
        if not "username" in session: return redirect(url_for("login"))
        return f(*args,**kwargs)
    #if not "username" in session: return redirect(url_for("login"))
    #print("check login")
    #return redirect("/")
    return dec
'''

def isLoggedIn():
    if not "username" in session: return redirect(url_for("login"))

@app.route('/home')
#@isLoggedIn
def home():
    #user = session['username']
    #cursor = conn.cursor();
    #query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    #cursor.execute(query, (user))
    #data = cursor.fetchall()
    #cursor.close()
    return render_template('home.html', username = session["username"])

### IMPLEMENTATION FUNCTIONS ###
def uploadImage():
    pass

### FriendGroup Required Features ###
@app.route('/addGroup')
def addGroup():
    return render_template('friend.html')

@app.route('/addFriendGroup', methods = ["GET", "POST"])
def addFriendGroup():
    groupName = request.form['Group Name']
    description = request.form['Description']

    cursor = conn.cursor()
    query = 'SELECT * FROM FriendGroup WHERE groupName = %s AND groupCreator = %s'
    cursor.execute(query, (groupName, session["username"]))
    data = cursor.fetchone()

    error = None
    if(data):
        error = "FriendGroup with this Owner Already Exists"
        return render_template('friend.html', error = error)
    else:
        ins = 'INSERT INTO FriendGroup VALUES(%s, %s, %s)'
        cursor.execute(ins, (groupName, session["username"], description))
        ins = 'INSERT INTO BelongTo VALUES(%s, %s, %s)'
        cursor.execute(ins, (session["username"], groupName, session["username"]))
        conn.commit()
        cursor.close()
        return redirect(url_for("home"))
    
@app.route('/viewGroup', methods = ["GET", "POST"])
def viewGroup():
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT groupName,groupCreator FROM BelongTo WHERE username = %s'
    #query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    cursor.execute(query, (user))
    data = cursor.fetchall()
    cursor.close()
    return render_template('viewGroups.html', username = user, posts = data)

### Follower Required Features ###
@app.route('/manageFollows', methods = ["GET", "POST"])
def manageFollows():
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT follower FROM Follow WHERE followee = %s AND followStatus = 0'
    cursor.execute(query, (user))
    data = cursor.fetchall()
    query = 'SELECT follower FROM Follow WHERE followee = %s AND followStatus = 1'
    cursor.execute(query, (user))
    moreData = cursor.fetchall()
    #conn.commit()
    cursor.close()
    return render_template('follows.html', username = user,
                           followerPosts = moreData, requestPosts = data)

@app.route('/followRequest', methods = ["GET", "POST"])
def followRequest():
    user = session['username']
    toFollow = request.form['request']
    cursor = conn.cursor()
    
    legal = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(legal, (toFollow))
    data = cursor.fetchone()
    if (not data):
        error = "Invalid Username, Try Again"
        return render_template('follows.html', error = error)

    queryTrue = 'SELECT * FROM Follow WHERE follower = %s and followee = %s and followStatus = 1'
    cursor.execute(queryTrue, (user, toFollow))
    data = cursor.fetchone()
    if(data):
        error = "You are already following them"
        return render_template('follows.html', error = error)

    queryFalse = 'SELECT * FROM Follow WHERE follower = %s and followee = %s and followStatus = 0'
    cursor.execute(queryFalse, (user, toFollow))
    data = cursor.fetchone()
    if(data):
        error = "Follow Request has already been sent, wait for the response"
        return render_template('follows.html', error = error)

    ins = "INSERT into Follow VALUES(%s,%s,%s)"
    cursor.execute(ins, (user,toFollow,0))
    #conn.commit()
    #upd = 'UPDATE Follow SET followStatus=1 WHERE follower = %s AND followee = %s'
    #cursor.execute(upd, (user, toFollow))
    conn.commit()
    cursor.close()
    return redirect(url_for("home"))

@app.route('/acceptRequest', methods = ["GET", "POST"])
def acceptRequest():
    user = session['username']
    accepted = request.form['accepted']
    print(accepted)
    cursor = conn.cursor()
    query = 'UPDATE Follow SET followStatus = 1 WHERE Follow.follower = %s AND Follow.followee = %s'
    cursor.execute(query, (accepted,user))
    conn.commit()
    cursor.close()
    return redirect('/manageFollows')

@app.route('/declineRequest', methods = ["GET", "POST"])
def declineRequest():
    user = session['username']
    declined = request.form['declined']
    #print(declined)
    cursor = conn.cursor()
    query = 'DELETE FROM Follow WHERE Follow.follower = %s and Follow.followee = %s'
    cursor.execute(query, (declined,user))
    conn.commit()
    cursor.close()
    return redirect('/manageFollows')

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
