from flask import Flask
from flask import request
from flask_cors import CORS
import json,vlc,threading,time,random, argparse
# Argparse Stuff
parser=argparse.ArgumentParser(description="Options for the Webby Bits")
parser.add_argument('-p','--port',help="Pick a port to host on, not the same as the web (client) port",default='19054')
portTheUserPicked=parser.parse_args().port
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
# open the json file as a dictionary
with open('./songDatabase.json', 'r') as handle:
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
                # New song is in the queue and (the previous song is over or skip has been pressed)
                player.stop()
                skipNow = False
                songNext = playlist.pop(0)
                media = fakeplayer.media_new("sound/"+songNext)
                player.set_media(media)
                player.play()
            elif (len(playlist) == 0) and skipNow==True:
                # skip was pressed and there are no new songs
                skipNow=False
                songNext = None
                player.stop()
            elif (len(playlist) == 0) and (z == "State.Ended" or z == "State.NothingSpecial" or z=="State.Stopped"):
                # i feel like this could actually be combined with the above, but imma not do that rn
                songNext = None
            elif (len(playlist)<1) and (partyMode == True):
                # adds the random songs for party mode
                # the above 2 means this only applies if (a song is playing (or paused)) and the queue is empty
                playlist.append(random.choice(songDatabaseList)["file"])
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
    recieveData = request.get_json(force=True)
    if recieveData["setting"] == "volume":
        player.audio_set_volume(int(recieveData["level"]))
        return "200"
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
    # what went through my head to make past-me think this is a good idea???
    # i mean actually looping through once still shouldn't ever take that long 
    # but like a binary search must exist in python and be faster
    # wait no binary search only helps if they're sorted
    # i mean i guess i could sort them and make searching faster
    for k in songDatabaseList:
        if k["file"] == songNext:
            temp = k.copy()
            temp["playing"] = True
            temp["time"] = player.get_time()/1000
            tempPlaylist.append(temp)
    for i in playlist:
        # oh my goodness i did it again
        # i seriously need to rewrite the databaseGenerator and this code
        # wait isn't this literally useless code???
        # oh no the playlist only contains names
        # i should really have used an object for this.
        for j in songDatabaseList:
            if j["file"] ==  i:
                tempPlaylist.append(j)
    return tempPlaylist

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=portTheUserPicked)
    