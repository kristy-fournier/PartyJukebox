from flask import Flask
from flask import request
from flask_cors import CORS
from flask_socketio import SocketIO
import sqlite3 as sql
import vlc,threading,time,random,argparse,dotenv,os,hashlib,string
# Argparse Stuff
parser=argparse.ArgumentParser(description="Options for the Webby Bits")
# parser.add_argument('-p','--port',help="Port to host on, not the same as the web (client) port",default='19054')
parser.add_argument('-a','--admin',help="Add an admin password to be used in the client. DO NOT use a password you use elsewhere",default="")
args = parser.parse_args()
dotenv.load_dotenv()
portTheUserPicked=os.getenv("SERVER_PORT")

ERR_NO_ADMIN = ({"error":"no-admin","data":None},401)
ERR_200 = ({"error":"OK","data":None},200)
ERR_MISSING_ARGS = ({"error":"Request missing required arguments","data":None}),400
if args.admin:
    ADMIN_PASS = hashlib.sha256(bytes(args.admin,'utf-8')).hexdigest()
else:
    tempPass = ''.join(random.choices(string.ascii_letters + string.digits +"?"+"!",k=20))
    print("No adminPass was set, the auto generated one is: "+tempPass)
    ADMIN_PASS = hashlib.sha256(bytes(tempPass,'utf-8')).hexdigest()
    
# True = everyone, False = admin only. Change in client while in use. 
# play-pause,skip,addsong,partymode,volume in order
controlPerms = {
    "PP":True, 
    "SK":True, 
    "AS":True, 
    "PM":True, 
    "VOL":True,
    "DUP":True # Not implemented, allow duplicate songs in queue
}

fileofDB = sql.connect("songDatabase.db")
songDatabase = fileofDB.cursor()

#song directory
songDatabase.execute("SELECT * FROM meta WHERE id='songDirectory';")
soundLocation = songDatabase.fetchall()[0][1]
if soundLocation[-1] == "/" or soundLocation[-1] == "\\":
    pass
elif "/" in soundLocation:
    soundLocation += "/"
else:
    soundLocation += "\\"
#Create Virtual table for searching
#I'm not sure why i don't do this in the databaseGenerator, but it also takes like 3 seconds so i'm not messing with it rn

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
# because you are POSTing from another domain to this one, you need CORS
CORS(app)
# Replace the star with the frontend domain if you dislike being hacked
socketio = SocketIO(app, cors_allowed_origins="*")

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
                socketio.emit('timeUpdate',{"elapsedTime":player.get_time()/1000,"playingState":playingState})
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
        time.sleep(1)

@socketio.on("connect")
def handleConnect():
    pass

@app.route("/controls", methods=['POST'])
def playerControls():
    # recieve control inputs (play/pause and skip) from the webUI
    global skipNow
    global partyMode
    recieveData=request.get_json(force=True)
    try:
        if recieveData["control"] == "play-pause":
            if ADMIN_PASS == recieveData['password'] or controlPerms["PP"]:
                playingState = str(player.get_state())=="State.Playing"
                player.pause()
                return {"error":"ok","data":{"playingState":not(playingState)}},200
            else:
                playingState = str(player.get_state())=="State.Playing"
                return {"error":"Admin Restricted Action","data":{"playingState":playingState}},401
        elif recieveData["control"] == "skip":
            if ADMIN_PASS == recieveData['password'] or controlPerms["SK"]:
                skipNow = True
                return ERR_200
            else:
                return ERR_NO_ADMIN
        # Maybe i should have put this next one in the "settings" section
        elif recieveData["control"] == "clear":
            if ADMIN_PASS == recieveData['password']: # this is only ever allowed with the adminpassword
                with playlistLock:
                    playlist.clear()
                return ERR_200
            else:
                return ERR_NO_ADMIN
        else:
            return {"error":"Not a valid control","data":None},400
    except KeyError:
        return ERR_MISSING_ARGS

@app.route("/settings", methods=['POST'])
def settingsControl():
    global controlPerms
    # set the volume and partymode
    global partyMode
    global player
    recieveData = request.get_json(force=True)
    try:
        if recieveData["setting"] == "volume":
            if ADMIN_PASS == recieveData['password'] or controlPerms["VOL"]:
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
            if ADMIN_PASS == recieveData['password'] or controlPerms["PM"]:
                partyMode = not(partyMode)
                partyModeStr = "On" if partyMode else "Off"
                socketio.emit("settingsChange",{"settingToChange":"partymode","newData":partyModeStr})
                return ERR_200
            else:
                return ERR_NO_ADMIN
        elif recieveData["setting"] == "perms":
            if ADMIN_PASS == recieveData["password"]:
                controlPerms = recieveData["admin"]
                # print(recieveData["admin"])
                socketio.emit("settingsChange",{"settingToChange":"perms","newData":controlPerms})
                return ERR_200
            else:
                return ERR_NO_ADMIN
        elif recieveData["setting"] == "getsettings":
            # probably should have made this a different request type or something but it works
            return {"error":"ok","data":{"partymode":partyMode,"volume":player.audio_get_volume(),"admin":controlPerms}},200
        else:
            return {"error":"Not a valid setting","data":None},400
    except:
        return ERR_MISSING_ARGS

@app.route("/search", methods=['POST'])
def searchSongDB():
    recieveData=request.get_json(force=True)
    fileofDB = sql.connect("songDatabase.db")
    songDatabase = fileofDB.cursor()
    try:
        results = []
        # print(recieveData["search"])
        if (recieveData['search'] == ""):
            songDatabase.execute("SELECT * FROM virtualSongs")
            results = songDatabase.fetchall()
        else:
            songDatabase.execute("SELECT * FROM virtualSongs WHERE virtualSongs MATCH ?",['"' + recieveData['search']+'"'])
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
    except KeyError:
        fileofDB.close()
        return ERR_MISSING_ARGS
    except sql.OperationalError as e:
        print(e)
        fileofDB.close()
        return ({"error":"Database error (Try another search?)","data":None},500)


@app.route("/songadd", methods=["POST"])
def songadd():
    recieveData=request.get_json(force=True)
    try:
        if (ADMIN_PASS == recieveData['password']) or controlPerms["AS"]:
            # Password exists and is correct, or it's not restricted
            if not(controlPerms["DUP"]) and (recieveData['song'] in playlist) and not(ADMIN_PASS == recieveData['password']):
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

@app.route("/playlist", methods=["POST"])
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
    socketio.run(app=app,host='0.0.0.0', port=portTheUserPicked)
    