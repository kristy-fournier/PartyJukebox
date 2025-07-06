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
portTheUserPicked=parser.parse_args().port

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
fakeplayer = vlc.Instance()
player = fakeplayer.media_player_new()
# for client side volume to work as well as possible, set system volume to 100 and control in app
player.audio_set_volume(100)
app = Flask(__name__)
# because you are posting from another domain to this one, you need CORS
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
            z = str(player.get_state())
            
            if playlist and (z == "State.Ended" or z== "State.Stopped" or z == "State.NothingSpecial" or skipNow == True):
                # New song is in the queue and (the previous song is over or skip has been pressed)
                player.stop()
                skipNow = False
                songNext = playlist.pop(0)
                media = fakeplayer.media_new("sound/"+songNext)
                player.set_media(media)
                player.play()
            elif (skipNow==True or (z == "State.Ended" or z == "State.NothingSpecial" or z=="State.Stopped")):
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
    global media
    global partyMode
    recieveData=request.get_json(force=True)
    if recieveData["control"] != None:
        if recieveData["control"] == "play-pause":
            player.pause()
            return "200"
        elif recieveData["control"] == "skip":
            skipNow = True
            # print(str(player.get_state()))
            return "200"
        else:
            return "400"

@app.route("/settings", methods=['POST'])
def settingsControl():
    # set the volume and partymode
    global partyMode
    global player
    recieveData = request.get_json(force=True)
    if recieveData["setting"] == "volume":
        volumePassed = player.audio_set_volume(int(recieveData["level"]))
        return {"volumePassed":volumePassed}
    elif recieveData["setting"] == "partymode-toggle":
        partyMode = not(partyMode)
        return "200"
    elif recieveData["setting"] == "getsettings":
        # probably should have made this a different request type or something but it works
        x = {"partymode":partyMode,"volume":player.audio_get_volume()}
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
    queueSong(recieveData['song'])
    return "200"
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
    