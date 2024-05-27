from flask import Flask
from flask import request
from flask_cors import CORS
import json,vlc,csv,threading,time,random
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
CORS(app)
with open('songDatabase.json', 'r') as handle:
    songDatabaseList = json.load(handle)

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
                player.stop()
                skipNow = False
                songNext = playlist.pop(0)
                media = fakeplayer.media_new("sound/"+songNext)
                player.set_media(media)
                player.play()
            elif (len(playlist) == 0) and skipNow==True:
                skipNow=False
                songNext = None
                player.stop()
            elif (len(playlist) == 0) and (z == "State.Ended" or z == "State.NothingSpecial" or z=="State.Stopped"):
                songNext = None
            elif (len(playlist)<1) and (partyMode == True):
                playlist.append(random.choice(songDatabaseList)["file"])        
        time.sleep(1)

queueThread = threading.Thread(target=playQueuedSongs)
queueThread.daemon = True
queueThread.start()

@app.route("/controls", methods=['POST'])
def playerControls():
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
    global partyMode
    recieveData = request.get_json(force=True)
    if recieveData["setting"] == "volume":
        player.audio_set_volume(int(recieveData["level"]))
        return "200"
    elif recieveData["setting"] == "getsettings":
        x = {"partymode":partyMode,"volume":player.audio_get_volume()}
        return x
    elif recieveData["setting"] == "partymode-toggle":
        partyMode = not(partyMode)
        return "200"
    else:
        return "400"
@app.route("/search", methods=['POST'])
def searchSongDB():
    recieveData=request.get_json(force=True)
    # the way i put the data in a list was really dumb looking back, i could and should have used a list of dictioaries like i was before
    # i might try to change it but this layout is embedded deep in the client
    tempData = {}
    for i in songDatabaseList:
        if ((i["title"].lower().find(recieveData['search'].lower())) > -1) or (recieveData['search'] == ""):
            tempData[i["title"]] = [i["artist"],i["art"],i["file"]]
        try:
            if (i["artist"].lower().find(recieveData['search'].lower()) > -1):
                tempData[i["title"]] = [i["artist"],i["art"],i["file"]]
        except:
            pass
    
    return tempData

@app.route("/songadd", methods=["POST"])
def songadd():
    recieveData=request.get_json(force=True)
    queueSong(recieveData['song'])
    return "200"
@app.route("/playlist", methods=["POST"])
def getPlaylist():
    global songNext
    tempPlaylist = []
    for k in songDatabaseList:
        if k["file"] == songNext:
            temp = k.copy()
            temp["playing"] = True
            temp["time"] = player.get_time()/1000
            tempPlaylist.append(temp)
    for i in playlist:
        for j in songDatabaseList:
            if j["file"] ==  i:
                tempPlaylist.append(j)
    return tempPlaylist

if __name__ == "__main__":
    app.run(host='0.0.0.0', port='25565')
    