from flask import Flask
from flask import request
from flask_cors import CORS
import sqlite3 as sql
import vlc,threading,time,random, argparse
# Argparse Stuff
parser=argparse.ArgumentParser(description="Options for the Webby Bits")
# this is no longer needed assuming my file works correctly with the generator
# parser.add_argument('-d','--directory',help="Directory of the song files (make sure this matches the directory used for the databaseGenerator)", default="./sound/")
parser.add_argument('-p','--port',help="Port to host on, not the same as the web (client) port",default='19054')
parser.add_argument('-a','--admin',help="Add an admin password to be used in the client. DO NOT use a password you use elsewhere",default="")
args = parser.parse_args()

portTheUserPicked=args.port
# Just a note that the return code "401" as of now is used to mean "you don't have the password"
# This is not great design, and the whole "returning string codes" thing is something to add to the todo list
# I mean returning 200 when no return is necesary i think is fine but we'll see
ERR_NO_ADMIN = "401"
ADMIN_PASS = args.admin
if not(ADMIN_PASS):
    ADMIN_PASS = None
# True = everyone, False = admin only. Change in client while in use. 
"""PP,SK,AS,PM,VOL all set to True or False
False is admin only
True is all users"""
controlPerms = {
    "PP":True, #done
    "SK":True, #done
    "AS":True, #done
    "PM":True, #done
    "VOL":True #done
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
#print(soundLocation)
#Create Virtual table for searching
songDatabase.execute("DROP TABLE virtualSongs;")
songDatabase.execute("CREATE VIRTUAL TABLE virtualSongs USING fts5(filename, title, artist, art, length);")
songDatabase.execute("INSERT INTO virtualSongs SELECT * FROM songs;")
fileofDB.commit()
fileofDB.close()
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

def queueSong(song):
    with playlistLock:
        playlist.append(song)
# this is a loop that plays the songs and checks for playlist changes, skips, ect.
def playQueuedSongs():
    global skipNow
    global songNext
    global partyMode
    while True:
        with playlistLock:
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
            elif (skipNow==True or (playerState in endStates)):
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
                # the above 2 means this only applies if (a song is playing (or paused)) and the queue is empty
                playlist.append(result[0][0])
        # check for new songs every second
        # I just didn't want to eat too much processing looping  
        time.sleep(1)
# start the media player thread
queueThread = threading.Thread(target=playQueuedSongs)
queueThread.daemon = True
queueThread.start()

@app.route("/controls", methods=['POST'])
def playerControls():
    # recieve control inputs (play/pause and skip) from the webUI
    global skipNow
    global partyMode
    recieveData=request.get_json(force=True)
    if recieveData["control"] != None:
        if recieveData["control"] == "play-pause":
            if ADMIN_PASS == recieveData['password'] or not(ADMIN_PASS) or controlPerms["PP"]:
                player.pause()
                return "200"
            else:
                return ERR_NO_ADMIN
        elif recieveData["control"] == "skip":
            if ADMIN_PASS == recieveData['password'] or not(ADMIN_PASS) or controlPerms["SK"]:
                skipNow = True
                return "200"
            else:
                return ERR_NO_ADMIN
        else:
            return "400"
    else:
        return "400"

@app.route("/settings", methods=['POST'])
def settingsControl():
    global controlPerms
    # set the volume and partymode
    global partyMode
    global player
    recieveData = request.get_json(force=True)
    if recieveData["setting"] == "volume":
        if ADMIN_PASS == recieveData['password'] or not(ADMIN_PASS) or controlPerms["VOL"]:
            volumePassed = player.audio_set_volume(int(recieveData["level"]))
            return {"volumePassed":volumePassed}
        else:
            return ERR_NO_ADMIN
    elif recieveData["setting"] == "partymode-toggle":
        if ADMIN_PASS == recieveData['password'] or not(ADMIN_PASS) or controlPerms["PM"]:
            partyMode = not(partyMode)
            return "200"
        else:
            return ERR_NO_ADMIN
    elif recieveData["setting"] == "perms":
        if ADMIN_PASS == recieveData["password"] and ADMIN_PASS:
            #if an adminpass doesn't exist these perms can never be changed
            controlPerms = recieveData["admin"]
            return "200"
        else:
            return ERR_NO_ADMIN
    elif recieveData["setting"] == "getsettings":
        # probably should have made this a different request type or something but it works
        x = {"partymode":partyMode,"volume":player.audio_get_volume(),"admin":controlPerms}
        return x
    else:
        return "400"

@app.route("/search", methods=['POST'])
def searchSongDB():
    recieveData=request.get_json(force=True)
    fileofDB = sql.connect("songDatabase.db")
    songDatabase = fileofDB.cursor()
    results = []
    if (recieveData['search'] == ""):
        songDatabase.execute("SELECT * FROM virtualSongs")
        results = songDatabase.fetchall()
    else:
        songDatabase.execute("SELECT * FROM virtualSongs WHERE virtualSongs MATCH ?",[recieveData['search']])
        results = songDatabase.fetchall()
    tempdata = {}
    # this is a temporary solution so i dont have to change the 
    for i in results:
        tempdata[i[0]] = {
            "title": i[1],
            "artist": i[2],
            "art": i[3],
            "length": i[4]
        }
    # print(tempData)
    fileofDB.close()
    return tempdata

@app.route("/songadd", methods=["POST"])
def songadd():
    recieveData=request.get_json(force=True)
    if (ADMIN_PASS and ADMIN_PASS == recieveData['password']) or controlPerms["AS"]:
        # Pass exists and is correct, or it's not restricted 
        queueSong(recieveData['song'])
        return "200"
    else:
        # the pass is incorrect (technically a pass not existing falls into the above case because controlPerms is never changed)
        return ERR_NO_ADMIN

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
    # print(tempPlaylist)
    fileofDB.close()
    return tempPlaylist

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=portTheUserPicked)
    