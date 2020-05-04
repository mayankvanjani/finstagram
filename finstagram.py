#Import Flask LibraryA
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
from functools import wraps
from datetime import datetime
import os
import random
import string

#Initialize the app from Flask
app = Flask(__name__, static_folder = "Uploaded_Images")
SALT = "cs3083salting"
picID = 0
picNum = 1
IMAGES = os.path.join(os.getcwd(), "Uploaded_Images")
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

#Configure MySQL
# UPDATE DB TO NAME OF DB IN phpMyAdmin
conn = pymysql.connect(host="localhost",
                       port = 8889,
                       user="root",
                       password="root",
                       db="finstagram2",
                       charset="utf8mb4",
                       autocommit=True,
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to login or home
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

### Check if Logged In ###
# Authenticates login as wrapper for remaining functions
def isLoggedIn(f):
    @wraps(f)
    def dec(*args,**kwargs):
        if not "username" in session: return redirect(url_for("login"))
        return f(*args,**kwargs)
    #print("check login")
    return dec

# Redireect to homepage if logged in
@app.route('/home')
@isLoggedIn
def home():
    user = session['username']
    return render_template('home.html', username = session["username"])



###                                                ###
###                                                ###
### IMPLEMENTATION FUNCTIONS: Project Requirements ###
###                                                ###
###                                                ###



###                          ###
### VIEWING / POSTING PHOTOS ###
###                          ###

# Define Route for Posting a Photo
@app.route('/post')
@isLoggedIn
def post():
    user = session["username"]
    cursor = conn.cursor()
    query = "SELECT groupName,groupCreator FROM BelongTo WHERE username = %s"
    cursor.execute(query, (user))
    groupNames = cursor.fetchall()
    cursor.close()
    return render_template('post.html', username = user, groups = groupNames)

# Checks valid input image files ('txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Posts Photo (Updates DB)
@app.route('/postPhoto', methods = ["GET", "POST"])
@isLoggedIn
def postPhoto():
    global picNum
    #print(picID)
    user = session['username']
    cursor = conn.cursor()
        
    if request.files:
        imageFile = request.files['upload']
        # Add random forehead to image path to prevent repeated filenames
        letters = string.ascii_lowercase
        ran = ''.join(random.choice(letters) for i in range(10))
        imageName = ran + imageFile.filename
        filepath = os.path.join(IMAGES, imageName)
        imageFile.save(filepath)
        
        cap = request.form['caption']
        share = request.form['shared']
        allFollow = (1 if share == "allFollowers" else 0)
        now = datetime.now()
        dt = now.strftime('%Y-%m-%d %H:%M:%S')
    
    else:
        error = "Need to Upload Photo"
        query = "SELECT groupName,groupCreator FROM BelongTo WHERE username = %s"
        cursor.execute(query, (user))
        groupNames = cursor.fetchall()
        cursor.close()
        return render_template('post.html', username = user, groups = groupNames, error = error)
    
    if share == "":
        error = "Select who to share this photo with"
        query = "SELECT groupName,groupCreator FROM BelongTo WHERE username = %s"
        cursor.execute(query, (user))
        groupNames = cursor.fetchall()
        cursor.close()
        return render_template('post.html', username = user, groups = groupNames, error = error)

    if imageFile and not allowed_file(imageName):
        error = "Incorrect Upload Type: Use jpg, png for best performance"
        query = "SELECT groupName,groupCreator FROM BelongTo WHERE username = %s"
        cursor.execute(query, (user))
        groupNames = cursor.fetchall()
        cursor.close()
        return render_template('post.html', username = user, groups = groupNames, error = error)
    
    share = share.split("@!@")
    #print(share, type(share))

    # Insert photo into Photo table, keeps track of allfollower
    ins = 'INSERT INTO Photo VALUES(%s, %s, %s, %s, %s, %s)'
    cursor.execute(ins, (picID,dt,imageName,allFollow,cap,user))
    conn.commit()

    if len(share) == 2:
        # Update SharedWith in case photo was shared with a friend group
        #print(share[0],share[1])
        ins = "INSERT INTO SharedWith VALUES(%s, %s, %s)"
        findpID = ("SELECT pID FROM Photo " +
                   "WHERE postingDate=%s AND filePath=%s AND allFollowers=%s AND caption=%s AND poster=%s")
        
        cursor.execute(findpID, (dt,imageName,allFollow,cap,user))
        curpID = cursor.fetchone()['pID']

        if curpID:
            cursor.execute(ins, (curpID,share[0],share[1]))
            conn.commit()
        
    cursor.close()
    return redirect(url_for("home"))

# Define Route for Viewing Photos
@app.route('/viewPhotos', methods = ["GET", "POST"])
@isLoggedIn
def viewPhotos():
    user = session["username"]
    cursor = conn.cursor()
    
    query = ("SELECT filePath,pID,firstName,lastName,postingDate " +
             "FROM (Photo JOIN Person ON (Photo.poster = Person.username)) " +
             "WHERE username = %s " +
             "ORDER BY Photo.postingDate DESC")

    cursor.execute(query, (user))
    yourPics = cursor.fetchall()
    #print("MINE: ", yourPics)
    query = ("SELECT filePath,pID,firstName,lastName,postingDate " +
             "FROM (Photo JOIN Person ON (Photo.poster = Person.username)) " +
             "JOIN Follow ON(Photo.poster = Follow.followee) " +
             "WHERE followStatus = 1 AND follower = %s AND allFollowers = 1 " +
             "UNION " +
             "SELECT filePath,pID,firstName,lastName,postingDate " +
             "FROM (SharedWith NATURAL JOIN BelongTo AS bt NATURAL JOIN Photo) " +
             "JOIN Person AS p ON (bt.groupCreator=p.username) " +
             "WHERE bt.username = %s AND bt.username != p.username " +
             "ORDER BY postingDate DESC")
    
    cursor.execute(query, (user,user))
    sharedPics = cursor.fetchall()
    #print("SHARED: ", sharedPics)
    cursor.close()
    return render_template('view.html', username = user, yourImages = yourPics, sharedImages = sharedPics)

# Define Route for Viewing Tags and Reactions (Note: No methods to create tags or reactions)
@app.route('/viewTagsandReacts', methods = ["GET", "POST"])
@isLoggedIn
def viewTagsandReacts():
    user = session['username']
    usepID = request.form['id']
    path = request.form['path']
    path2 = str(request.form['path'])
    #print(usepID, type(usepID))
    #print("TAG PATH: ", path, type(path), path2)
    usepID = int(usepID)
    cursor = conn.cursor()
    
    tagQuery = ("SELECT username,firstName,lastName FROM Photo NATURAL JOIN Tag NATURAL JOIN Person " +
                "WHERE pID = %s AND tagStatus = 1")
    cursor.execute(tagQuery, (usepID))
    tag = cursor.fetchall()

    reactQuery = "SELECT username,emoji,comment FROM ReactTo WHERE pID = %s"
    cursor.execute(reactQuery, (usepID))
    react = cursor.fetchall()

    cursor.close()
    return render_template('tagreact.html', username=user, photoID=usepID, filePath=path, tagInfo=tag, reactInfo=react)

###                          ###
###   MANAGING FRIENDGROUPS  ###
###                          ###

# Define Route for Adding a Friend Group
@app.route('/addGroup')
@isLoggedIn
def addGroup():
    return render_template('friend.html', username = session["username"])

# Add a Friend Group (Update DB)
@app.route('/addFriendGroup', methods = ["GET", "POST"])
@isLoggedIn
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
        return render_template('friend.html', username = session["username"], error = error)
    else:
        ins = 'INSERT INTO FriendGroup VALUES(%s, %s, %s)'
        cursor.execute(ins, (groupName, session["username"], description))
        ins = 'INSERT INTO BelongTo VALUES(%s, %s, %s)'
        cursor.execute(ins, (session["username"], groupName, session["username"]))
        conn.commit()
        cursor.close()
        return redirect(url_for("home"))

# Define Route for Viewing Friend Groups
@app.route('/viewGroup', methods = ["GET", "POST"])
@isLoggedIn
def viewGroup():
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT groupName,groupCreator FROM BelongTo WHERE username = %s'
    #query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    cursor.execute(query, (user))
    data = cursor.fetchall()
    cursor.close()
    return render_template('viewGroups.html', username = user, posts = data)

# Define Route for Adding a Friend to a Friend Group
@app.route('/aftg')
@isLoggedIn
def aftg():
    user = session["username"]
    cursor = conn.cursor()
    query = "SELECT groupName,groupCreator FROM BelongTo WHERE username = %s AND groupCreator = %s"
    cursor.execute(query, (user,user))
    groupNames = cursor.fetchall()
    cursor.close()
    return render_template('aftg.html', username = session["username"], groups = groupNames)

# Add Friend to Group (Updates DB)
@app.route('/addFriendToGroup', methods = ["GET", "POST"])
@isLoggedIn
def addFriendToGroup():
    user = session["username"]
    cursor = conn.cursor();
    chosen = request.form['chosenGroup']
    chosen = chosen.split("@!@")
    toAdd = request.form['friendUser']
    #print(chosen,toAdd)
    query = "SELECT groupName,groupCreator FROM BelongTo WHERE username = %s AND groupCreator = %s"
    cursor.execute(query, (user,user))
    groupNames = cursor.fetchall()
    
    check = "SELECT * FROM Person WHERE username = %s"
    cursor.execute(check, (toAdd))
    found = cursor.fetchone()
    if not found:
        error = 'Username to Add Not Found, Try Again'
        return render_template('aftg.html', username = session["username"], groups = groupNames, error = error)

    again = "SELECT * FROM BelongTo WHERE username = %s AND groupName = %s AND groupCreator = %s"
    cursor.execute(again, (toAdd,chosen[0],chosen[1]))
    found = cursor.fetchone()
    if found:
        error = "User Already Belongs to This Group"
        return render_template('aftg.html', username = session["username"], groups = groupNames, error = error)

    ins = 'INSERT INTO BelongTo VALUES(%s, %s, %s)'
    cursor.execute(ins, (toAdd,chosen[0],chosen[1]))
    conn.commit()
    cursor.close()
    return redirect(url_for("home"))

###                          ###
###     MANAGING FOLLOWS     ###
###                          ###

# Define Route for Managing Followers
@app.route('/manageFollows', methods = ["GET", "POST"])
@isLoggedIn
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

# Send a Follow Request (Updates DB)
@app.route('/followRequest', methods = ["GET", "POST"])
@isLoggedIn
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
    conn.commit()
    cursor.close()
    return redirect(url_for("home"))

# Accept a Follow Request (Updates DB)
@app.route('/acceptRequest', methods = ["GET", "POST"])
@isLoggedIn
def acceptRequest():
    user = session['username']
    accepted = request.form['accepted']
    #print(accepted)
    cursor = conn.cursor()
    query = 'UPDATE Follow SET followStatus = 1 WHERE Follow.follower = %s AND Follow.followee = %s'
    cursor.execute(query, (accepted,user))
    conn.commit()
    cursor.close()
    return redirect('/manageFollows')

# Decline a Follow Request (Updates DB)
@app.route('/declineRequest', methods = ["GET", "POST"])
@isLoggedIn
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

# Logout
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION

if __name__ == "__main__":
    print("STARTING")
    #print(os.path.isdir("Uploaded_Images"))
    if not os.path.isdir("Uploaded_Images"):
        print("Making Images Directory")
        os.mkdir(IMAGES)
    app.run('127.0.0.1', 5000, debug = True)

