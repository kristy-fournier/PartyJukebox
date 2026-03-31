import eventlet
eventlet.monkey_patch()
from flask import Flask
from flask import request,render_template
from flask_cors import CORS
from flask_socketio import SocketIO
import sqlite3 as sql
import vlc,threading,random,argparse,dotenv,os,hashlib,string,getpass

# So i'm famously bad at following Semantic versioning, we're gonna see how this goes
REL_VER_NUM = "0.0.1"

# Argparse Stuff
parser=argparse.ArgumentParser(description="Options for the Webby Bits")
parser.add_argument('-a','--admin',help="Set as True to be prompted to enter an AdminPassword",default=False)
args = parser.parse_args()
dotenv.load_dotenv()
portTheUserPicked=os.getenv("SERVER_PORT")

ERR_NO_ADMIN = ({"error":"no-admin","data":None},401)
ERR_200 = ({"error":"OK","data":None},200)
ERR_MISSING_ARGS = ({"error":"Request missing required arguments","data":None}),400
if bool(args.admin) and args.admin.lower() != "false":
    ADMIN_PASS = hashlib.sha256(bytes(getpass.getpass("Enter AdminPass: "),'utf-8')).hexdigest()
else:
    tempPass = ''.join(random.choices(string.ascii_letters + string.digits +"?"+"!",k=20))
    print("No adminPass was set, the auto generated one is: "+tempPass)
    ADMIN_PASS = hashlib.sha256(bytes(tempPass,'utf-8')).hexdigest()
    
# True = everyone, False = admin only. Change in client while in use. 
# play-pause,skip,addsong,partymode,volume,add duplicates in order
controlPerms = {
    "PP":True, 
    "SK":True, 
    "AS":True, 
    "PM":True, 
    "VOL":True,
    "DUP":True
}

fileofDB = sql.connect("songDatabase.db")
songDatabase = fileofDB.cursor()

#song directory
try:
    songDatabase.execute("SELECT * FROM meta WHERE id='songDirectory';")
    soundLocation = songDatabase.fetchall()[0][1]
except sql.OperationalError:
    print("No Database Found, try running databaseGenerator.py")
if soundLocation[-1] == "/" or soundLocation[-1] == "\\":
    pass
elif "/" in soundLocation:
    soundLocation += "/"
else:
    soundLocation += "\\"
#Initializing all the global stuff
random.seed()
global partyMode
global skipNow
global songNext
partyMode = False
songNext = None
skipNow = False
playlist = []
playlistLock = threading.Lock()
vlcInstance = vlc.Instance()
player = vlcInstance.media_player_new()
# for client side volume to work as well as possible, set system volume to 100 and control in app
player.audio_set_volume(100)
app = Flask(__name__)
socketio = SocketIO(app)

def queueSong(song):
    with playlistLock:
        playlist.append(song)
    socketio.emit("songAdd",getSongInfo(song))

def getSongInfo(song):
    fileofDB = sql.connect("songDatabase.db")
    songDatabase = fileofDB.cursor()
    songDatabase.execute("SELECT * FROM songs WHERE filename = ?",[song])
    result = songDatabase.fetchall()[0]
    # again, this is still using the old JSON format to avoid client changes
    k = {
        "title": result[1],
        "artist": result[2],
        "art": result[3],
        "length": result[4]
    }
    fileofDB.close()
    return {song:k}

# this is a loop that plays the songs and checks for playlist changes, skips, ect.
counter = 0
isPlaying = False
def playQueuedSongs():
    global skipNow
    global songNext
    global partyMode
    global counter
    global isPlaying
    while True:
        with playlistLock:
            counter+=1
            if(counter > 2):
                playingState = str(player.get_state()) == "State.Playing"
                socketio.emit('timeUpdate',{"elapsedTime":player.get_time()/1000,"playingState":playingState,"songLength":player.get_length()/1000})
                counter = 0
            playerState = str(player.get_state())
            endStates = ["State.Ended","State.Stopped","State.NothingSpecial"]
            if playlist and (playerState in endStates or skipNow == True):
                # New song is in the queue and (the previous song is over or skip has been pressed)
                player.stop()
                skipNow = False
                songNext = playlist.pop(0)
                media = vlcInstance.media_new(soundLocation+songNext)
                player.set_media(media)
                player.play()
                isPlaying = True
                socketio.emit("skipSong",None)
            elif (skipNow==True or (playerState in endStates)):
                if(isPlaying):
                    socketio.emit("skipSong",None)
                    isPlaying = False
                # print(playerState)
                # skip was pressed and there are no new songs
                skipNow=False
                songNext = None
                player.stop()
            elif len(playlist)<1 and (partyMode == True):
                fileofDB = sql.connect("songDatabase.db")
                songDatabase = fileofDB.cursor()
                songDatabase.execute("SELECT * FROM songs ORDER BY RANDOM() LIMIT 1;")
                result = songDatabase.fetchall()
                # adds the random songs for party mode
                # the above 2 means this only applies if (a song is playing or paused) and (the queue is empty)
                playlist.append(result[0][0])
                socketio.emit('songAdd',getSongInfo(result[0][0]))
        # check for new songs every second
        # I just didn't want to eat too much processing looping 
        # this also has another useful affect that skips get "queued" to only 1 per second, that way somebody usually can't skip twice accidentally
        socketio.sleep(1)

@socketio.on("connect")
def handleConnect():
    pass

@app.route("/",methods=['GET'])
def returnStaticFile():
    return render_template("index.html",REL_VER_NUM=REL_VER_NUM)

@app.route("/controls", methods=['POST'])
def playerControls():
    # recieve control inputs (play/pause and skip) from the webUI
    global skipNow
    global partyMode
    recieveData=request.get_json(force=True)
    try:
        if recieveData["control"] == "play-pause":
            if ADMIN_PASS == request.headers["Jukebox-Auth"] or controlPerms["PP"]:
                playingState = str(player.get_state())=="State.Playing"
                player.pause()
                return {"error":"ok","data":{"playingState":not(playingState)}},200
            else:
                playingState = str(player.get_state())=="State.Playing"
                return {"error":"Admin Restricted Action","data":{"playingState":playingState}},401
        elif recieveData["control"] == "skip":
            if ADMIN_PASS == request.headers["Jukebox-Auth"] or controlPerms["SK"]:
                skipNow = True
                return ERR_200
            else:
                return ERR_NO_ADMIN
        # Maybe i should have put this next one in the "settings" section
        elif recieveData["control"] == "clear":
            if ADMIN_PASS == request.headers["Jukebox-Auth"]: # this is only ever allowed with the adminpassword
                with playlistLock:
                    playlist.clear()
                return ERR_200
            else:
                return ERR_NO_ADMIN
        else:
            return {"error":"Not a valid control","data":None},400
    except KeyError:
        return ERR_MISSING_ARGS

@app.route("/settings", methods=['POST','GET'])
def settingsControl():
    global controlPerms
    # set the volume and partymode
    global partyMode
    global player
    if (request.method == 'GET'):
        return {"error":"ok","data":{"partymode":partyMode,"volume":player.audio_get_volume(),"admin":controlPerms}},200
    elif (request.method == 'POST'):
        recieveData = request.get_json(force=True)
        try:
            if recieveData["setting"] == "volume":
                if ADMIN_PASS == request.headers["Jukebox-Auth"] or controlPerms["VOL"]:
                    volumeLevel = int(recieveData["level"])
                    if(volumeLevel <= 100 and volumeLevel >= 0):
                        volumePassed = player.audio_set_volume(volumeLevel)
                        if(volumePassed == 0):
                            # only emit a signal i the volume really changed
                            socketio.emit("settingsChange",{"settingToChange":"volume","newData":volumeLevel})
                        return {"error":"ok","data":{"volumePassed":volumePassed}},200
                    else:
                        return {"error":"Invalid volume level","data":None},422
                else:
                    return ERR_NO_ADMIN
            elif recieveData["setting"] == "partymode-toggle":
                if ADMIN_PASS == request.headers["Jukebox-Auth"] or controlPerms["PM"]:
                    partyMode = not(partyMode)
                    partyModeStr = "On" if partyMode else "Off"
                    socketio.emit("settingsChange",{"settingToChange":"partymode","newData":partyModeStr})
                    return ERR_200
                else:
                    return ERR_NO_ADMIN
            elif recieveData["setting"] == "perms":
                if ADMIN_PASS == request.headers["Jukebox-Auth"]:
                    controlPerms = recieveData["admin"]
                    # print(recieveData["admin"])
                    socketio.emit("settingsChange",{"settingToChange":"perms","newData":controlPerms})
                    return ERR_200
                else:
                    return ERR_NO_ADMIN
            else:
                return {"error":"Not a valid setting","data":None},400
        except KeyError as e:
            print(f"Error: {e}")
            return {"error":"Incorrect Data Sent","data":None},400

@app.route("/search", methods=['GET'])
def searchSongDB():
    recieveData = request.args.get("query")
    fileofDB = sql.connect("songDatabase.db")
    songDatabase = fileofDB.cursor()
    try:
        results = []
        # print(recieveData["search"])
        if (recieveData == None or recieveData == ""):
            songDatabase.execute("SELECT * FROM virtualSongs")
            results = songDatabase.fetchall()
        else:
            songDatabase.execute("SELECT * FROM virtualSongs WHERE virtualSongs MATCH ?",['"' + recieveData +'"'])
            results = songDatabase.fetchall()
        tempdata = {}
        # this is a temporary solution so i dont have to change the client 
        for i in results:
            tempdata[i[0]] = {
                "title": i[1],
                "artist": i[2],
                "art": i[3],
                "length": i[4],
                "lossless":i[5]
            }
        fileofDB.close()

        return {"error":"ok","data":tempdata},200
    except sql.OperationalError as e:
        print(e)
        fileofDB.close()
        return ({"error":"Database error (Try another search?)","data":None},500)


@app.route("/songadd", methods=["POST"])
def songadd():
    recieveData=request.get_json(force=True)
    try:
        if (ADMIN_PASS == request.headers["Jukebox-Auth"]) or controlPerms["AS"]:
            # Password exists and is correct, or it's not restricted
            if not(controlPerms["DUP"]) and (recieveData['song'] in playlist) and not(ADMIN_PASS == request.headers["Jukebox-Auth"]):
                return {"error":"This song is already in the queue, hang on!","data":None},409
            else:
                queueSong(recieveData['song'])
                return ERR_200
        else:
            # the password is incorrect (technically a password not existing falls into the above case because controlPerms is never changed)
            return ERR_NO_ADMIN
    except KeyError as e:
        print(e)
        return ERR_MISSING_ARGS

@app.route("/playlist", methods=["GET"])
def getPlaylist():
    global songNext
    fileofDB = sql.connect("songDatabase.db")
    songDatabase = fileofDB.cursor()
    tempPlaylist = []
    if songNext != None:
        # Adds the currently playing song
        songDatabase.execute("SELECT * FROM songs WHERE filename = ?",[songNext])
        result = songDatabase.fetchall()[0]
        # again, this is still using the old JSON format to avoid client changes
        k = {
            "title": result[1],
            "artist": result[2],
            "art": result[3],
            "length": result[4]
        }
        temp = k.copy()
        temp["playing"] = True
        temp["time"] = player.get_time()/1000
        tempPlaylist.append({songNext:temp})
    for i in playlist:
        songDatabase.execute("SELECT * FROM songs WHERE filename = ?",[i])
        result = songDatabase.fetchall()[0]
        k = {
            "title": result[1],
            "artist": result[2],
            "art": result[3],
            "length": result[4]
        }
        tempPlaylist.append({i:k})
    fileofDB.close()
    playingState = False
    if(str(player.get_state())=="State.Playing"):
        playingState = True
    # print(playingState)
    return {"error":"ok","data":{"playlist":tempPlaylist,"playingState":playingState}},200

if __name__ == "__main__":
    # There's not really a whole lot of point to a main function for something like this, you'd never use any of these methods
    # elsewhere, but its just good practice i guess
    # start the media player thread
    queueThread = threading.Thread(target=playQueuedSongs)
    queueThread.daemon = True
    queueThread.start()
    print(f"PartyJukebox v{REL_VER_NUM} running on port {portTheUserPicked}")
    socketio.run(app=app,host='0.0.0.0', port=portTheUserPicked)
    