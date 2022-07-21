
#! -------------------- IMPORT MODULES --------------------- !#


import os
import json
import string
import random
import base64
import requests
import mysql.connector
from time import sleep
from datetime import datetime
from cryptography.fernet import Fernet
from dateutil.relativedelta import relativedelta
from flask import Flask, request, render_template, redirect


#! -------------------- DATABASE CONNECTION --------------------- !#


#** Get Connection Details **
Host = os.environ["DATABASE_HOST"]
User = os.environ["DATABASE_USER"]
Password = os.environ["DATABASE_PASS"]

#** Connect To Database **
print("--------------------CONNECTING TO DATABASE--------------------")
connection = mysql.connector.connect(host = Host,
                                    database = "discordmusic",
                                    user = User,
                                    password = Password)

#** Setup Cursor and Output Successful Connection **                  
if connection.is_connected():
    cursor = connection.cursor(buffered=True)
    cursor.execute("SELECT database();")
    print("Database Connection Established: "+datetime.now().strftime("%H:%M")+"\n")
else:
    print("Database Connection Failed: "+datetime.now().strftime("%H:%M")+"\n")

#** Delete Connection Details **
del Host
del User
del Password


#! -------------------- AUTH CLASS --------------------- !#


class Auth():

    def __init__(self):

        #** Get Spotify Details From Environment Variables **
        self.ID = os.environ["SPOTIFY_CLIENT"]
        self.Secret = os.environ["SPOTIFY_SECRET"]

        #** Setup Auth Header For Requests & Dictionary Of Active States **
        ClientData = self.ID+":"+self.Secret
        AuthStr =  base64.urlsafe_b64encode(ClientData.encode()).decode()
        self.AuthHead = {"Content-Type": "application/x-www-form-urlencoded", 'Authorization': 'Basic {0}'.format(AuthStr)}


    def NewClientAuth(self, discordID):

        #** Set DiscordID As Class Object **
        self.discordID = discordID

        #** Get Row With DiscordID From Database **
        cursor.execute("SELECT * FROM spotify WHERE DiscordID = '"+str(discordID)+"';")
        Verification = cursor.fetchone()
        connection.commit()

        #** Check Row Was Found & If Not None, Calculate Time Difference From When Request Was Made In Discord **
        if Verification != None:
            TimeDiff = relativedelta(datetime.now(), Verification[7])

            #** Check If Time Difference Is Within 10 Mins (Auth Hasn't Timed Out) & Cleanup User From Database If So **
            if TimeDiff.minutes >= 10:
                self.UserCleanup()
                return "Timeout"

            #** Generate Random State and Make Sure It Isn't Active **
            while True:
                NewState = []
                for i in range(10):
                    NewState.append(random.choice(string.ascii_letters))
                self.State = "".join(NewState)
                if not(self.State in ActiveStates.keys()):
                    ActiveStates[self.State] = self.discordID
                    break
        
            #** Return State (None If Could Create Client) **
            return self.State

        #** Return None If User Not In Table, ie, Not Linked Through Bot **
        else:
            return None

    
    def UserCleanup(self):

        #** Remove Row From Spotify With Specified Discord ID **
        cursor.execute("DELETE FROM spotify WHERE DiscordID = '"+str(self.discordID)+"'")
        connection.commit()


    def AuthenticateUser(self, Code):
        
        #** Request For An Access Token To Connected User Account Via Spotify Web API **
        data = {'grant_type': "authorization_code", 
                'code': str(Code), 
                'redirect_uri': 'http://82.22.157.214:5000/', 
                'client_id': self.ID, 
                'client_secret': self.Secret}
        AuthData = requests.post("https://accounts.spotify.com/api/token", data, self.AuthHead)

        #** Check If Request Was A Success **
        while AuthData.status_code != 200:
                
            #** Check If Rate Limit Has Been Applied **
            if 429 == AuthData.status_code:
                print("\n----------------------RATE LIMIT REACHED--------------------")
                print("Function: AuthenticateUser")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                Time = AuthData.headers['Retry-After']
                sleep(Time)
                AuthData = requests.post("https://accounts.spotify.com/api/token", data, self.AuthHead)
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("\n----------------------UNEXPECTED ERROR--------------------")
                print("Function: AuthenticateUser")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                print("Error: Spotify Request Code "+str(AuthData.status_code))
                return "UnexpectedError"
    
        #** Get Json Body Of Request & Set Token, Refresh & UserHeader For Requests **
        AuthData = AuthData.json()
        self.UserToken = AuthData['access_token']
        self.UserRefresh = AuthData['refresh_token']
        self.UserHead = {'Accept': "application/json", 'Content-Type': "application/json", 'Authorization': "Bearer "+self.UserToken}
        
        #** Carry Out Request To Get Further Details **
        Result = self.GetUserDetails()
        return Result


    def GetUserDetails(self):
        
        #** Request User Profile From Spotify & Check If Request Was A Success **
        UserData = requests.get("https://api.spotify.com/v1/me", headers = self.UserHead)
        while UserData.status_code != 200:
                
            #** Check If Rate Limit Has Been Applied **
            if 429 == UserData.status_code:
                print("\n----------------------RATE LIMIT REACHED--------------------")
                print("Function: GetUserDetails")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                Time = UserData.headers['Retry-After']
                sleep(Time)
                UserData = requests.get("https://api.spotify.com/v1/me", headers = self.UserHead)
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("\n----------------------UNEXPECTED ERROR--------------------")
                print("Function: GetUserDetails")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                print("Error: Spotify Request Code "+str(UserData.status_code))
                return "UnexpectedError"

        #** Get Request JSON Data & Set Class Objects Of Important Information From Request **
        UserData = UserData.json()
        self.Name = UserData['display_name']
        self.UserID = UserData['id']
        self.Avatar = UserData['images'][0]['url']
        self.Followers = UserData['followers']['total']
        if UserData['product'] in ["open", "free"]:
            self.Subscription = False
        else:
            self.Subscription = True
        return "Success"


    def AddToDatabase(self):

        #** Setup Symmetric Encryption Module **
        Key = os.environ['ENCRYPTION_KEY']
        Key = bytes(Key, 'utf-8')
        fernet = Fernet(Key)

        #** Encrypt Sensitive Information **
        Refresh = fernet.encrypt(str(self.UserRefresh).encode())
        Name = fernet.encrypt(str(self.Name).encode())
        Avatar = fernet.encrypt(str(self.Avatar).encode())
        SpotifyID = fernet.encrypt(str(self.UserID).encode())

        #** Convert Bytes To String **
        Refresh = str(Refresh).replace("b'", "").replace("'", "")
        Name = str(Name).replace("b'", "").replace("'", "")
        Avatar = str(Avatar).replace("b'", "").replace("'", "")
        SpotifyID = str(SpotifyID).replace("b'", "").replace("'", "")

        #** Delete Variables To Keep Key Safe **
        del Key
        del fernet

        #** Update Row In Spotify Table In Database With User Details & Refresh Token **
        cursor.execute("UPDATE Spotify SET SpotifyID = '"+str(SpotifyID)+"',"+
                                          "Name = '"+str(Name)+"',"+
                                          "Avatar = '"+str(Avatar)+"',"+
                                          "Followers = "+str(self.Followers)+","+
                                          "Subscription = "+str(self.Subscription)+","+
                                          "Refresh = '"+str(Refresh)+"'"+
                       "WHERE DiscordID = '"+str(self.discordID)+"';")
        connection.commit()



#** Setup Flask Service & Instantiate Auth Class **
Web = Flask(__name__)
ActiveStates = {}


#! -------------------- WEB PAGES --------------------- !#


@Web.route("/")
def PostSpotify():
    
    #** Get Code & State Passed In As Params In URL **
    Code = request.args.get('code')
    State = request.args.get('state')
    print("New Request!\nCode: "+str(Code)+"\nState: "+str(State)+"\n")
    
    #** Check State Is An Active State & Get Corresponding Auth Class **
    if State in list(ActiveStates.keys()):
        
        #** Get Auth Class For State & Check Code Was Returned (User Didn't Reject Auth) **
        Auth = ActiveStates[State]
        if Code != None:

            #** Get Credentials & User Information From Spotify Web API & If No Error, Add Data To Database & Render Success Template **
            Result = Auth.AuthenticateUser(Code)
            if Result == "Success":
                Auth.AddToDatabase()
                return render_template('Success.html', Name=str(Auth.Name), Link=str("https://api.spotify.com/v1/users/"+str(Auth.UserID)))

            #** If Error Occurs Whilst Requesting Data From Spotify, Cleanup User From Database and ActiveStates & Render Error Template **
            else:
                Auth.UserCleanup()
                ActiveStates.pop(State)
                return render_template('Error.html')
            
        #** If User Rejected Request To Link, Cleanup User From Database and ActiveStates & Render Failure Template **
        else:
            Auth.UserCleanup()
            ActiveStates.pop(State)
            return render_template('Failure.html')

    #** If State Is Invalid, Render Error Template **
    else:
        return render_template('Error.html')


@Web.route("/link")
def PreSpotify():

    #** Get DiscordID Passed Through In URL & Check It's Valid **
    discordID = str(request.args.get('discord'))
    if discordID.isdecimal() and len(discordID) == 18:
        
        #** Setup Auth Class For New User & Attempt To Initialise DiscordID **
        User = Auth()
        State = User.NewClientAuth(int(discordID))
        
        #** Check State Isn't None, ie, The DiscordID Had Requested To Link Via Discord First **
        if State != None:

            #** If Auth Request Has Timed Out, Render Timeout Template **
            if State == "Timeout":
                return render_template('Timeout.html')
            
            #** Add To Dict Of Active States & Redirect User To Spotify Auth URL **
            ActiveStates[State] = User
            AuthURL = "https://accounts.spotify.com/authorize?client_id=710b5d6211ee479bb370e289ed1cda3d&response_type=code"
            AuthURL += "&redirect_uri=http%3A%2F%2F82.22.157.214:5000%2F&scope=playlist-read-private%20playlist-read-collaborative%20user-read-private&state="+State
            return redirect(AuthURL)

        #** Render Error Template If Something Isn't Right With The Request **
        else:
            return render_template('Error.html')
    else:
        return render_template('Error.html')


#! -------------------- START WEBSERVICE --------------------- !#


#** Startup The Web Service **
if __name__ == "__main__":
    Web.run(host='0.0.0.0', debug=True)