import requests
import json
import os
import base64
import mysql.connector
from flask import Flask, request, render_template

Host = os.environ["DATABASE_HOST"]
User = os.environ["DATABASE_USER"]
Password = os.environ["DATABASE_PASS"]
connection = mysql.connector.connect(host = Host,
                                     database = "Melody",
                                     user = User,
                                     password = Password)
if connection.is_connected():
    cursor = connection.cursor()
    cursor.execute("select database();")
    record = cursor.fetchone()
    print("Connected To Database: "+record[0].title()+"\n")

del Host
del User
del Password

class Auth():
    def __init__(self):
        self.ID = os.environ["SPOTIFY_CLIENT"]
        self.Secret = os.environ["SPOTIFY_SECRET"]

        ClientData = self.ID+":"+self.Secret
        AuthStr =  base64.urlsafe_b64encode(ClientData.encode()).decode()
        self.AuthHead = {"Content-Type": "application/x-www-form-urlencoded", 'Authorization': 'Basic {0}'.format(AuthStr)}

    def AuthenticateUser(self, Code):
        data = {'grant_type': "authorization_code", 'code': str(Code), 'redirect_uri': 'http://82.22.157.214:5000/', 'client_id': self.ID, 'client_secret': self.Secret}
        AuthData = requests.post("https://accounts.spotify.com/api/token", data, self.AuthHead)
        print(AuthData)
        print(AuthData.json())
        AuthData = AuthData.json()
        self.UserToken = AuthData['access_token']
        self.UserRefresh = AuthData['refresh_token']
        self.UserHead = {'Accept': "application/json", 'Content-Type': "application/json", 'Authorization': "Bearer "+self.UserToken}
        self.GetUserDetails()

    def GetUserDetails(self):
        UserData = requests.get("https://api.spotify.com/v1/me", headers = self.UserHead).json()
        self.Name = UserData['display_name']
        self.UserID = UserData['id']
        self.ProfilePic = UserData['images'][0]['url']
        self.URL = UserData['external_urls']['spotify']

Web = Flask(__name__)
Authenticate = Auth()

@Web.route("/")
def home():
    Code = request.args.get('code')
    State = request.args.get('state')
    print("\n"+str(Code)+"\n"+str(State)+"\n")
    Authenticate.AuthenticateUser(Code)
    cursor.execute("INSERT INTO Spotify (Token, Refresh, Name, SpotifyID, Pic, State) VALUES (%s, %s, %s, %s, %s, %s)", params=(Authenticate.UserToken, Authenticate.UserRefresh, Authenticate.Name, Authenticate.UserID, Authenticate.ProfilePic, str(State)))
    connection.commit()
    return render_template('Success.html', Name=str(Authenticate.Name), Link=str(Authenticate.URL))
    
if __name__ == "__main__":
    Web.run(host='0.0.0.0', debug=True)