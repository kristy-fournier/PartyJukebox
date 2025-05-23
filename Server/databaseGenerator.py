import os
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import requests, ast, time, math, argparse, json

loading = ["-","\\","|","/"]

parser=argparse.ArgumentParser(description="Options for the generation of the song database")
parser.add_argument('-k','--apikey', help='String: LastFM api key', default="")
parser.add_argument('-m', '--mode', help='new/update: Remake database or update current', default= "update")
parser.add_argument('-a', '--art', help="True/False: Add art to the database using LastFm (takes minimum 0.25s per song)", default="True")
parser.add_argument('-d','--directory',help="Directory of the song files", default="./sound/")
args = parser.parse_args()
apikeylastfm = args.apikey
if args.directory[-1] == "/" or args.directory[-1] == "\\":
    soundLocation = args.directory
elif "/" in args.directory:
    soundLocation = args.directory + "/"
else:
    soundLocation = args.directory + "\\"
# if you want to set the api key/sound directory permenantly for your setup just uncomment the next line
# apikeylastfm = "KeyHere"
# soundLocation = "directoryHere"
songFiles = os.listdir(soundLocation)
if args.mode.lower() == "update":
    try:   
        with open('songDatabase.json', 'r') as handle:
            songDatabaseList = json.load(handle)
    except:
        songDatabaseList={"songDirectory":soundLocation,'songData':{}}
    deleteySongs = []
    for i in songDatabaseList["songData"]:
        try:
            if songFiles.index(i) == -1:
                deleteySongs.append(i)
        except:
            deleteySongs.append(i)
    if deleteySongs:
        print("deleted: " + ", ".join(deleteySongs)+ " from database")
    for i in deleteySongs:
        songDatabaseList["songData"].pop(i)
    for i in songDatabaseList["songData"]:
        songFiles.remove(i)
    # This prints everything in the directory, including non mp3s
    # theres not agood way to fix this without looping again.
    print("new songs: " + ", ".join(songFiles))
elif args.mode.lower()=="new":
    songDatabaseList={"songDirectory":soundLocation,'songData':{}}
else:
    raise ValueError("Must be \"new\" or \"update\"")
if args.art.lower() == "true" and not(args.apikey == ""):
    x = len(songFiles)*0.25
    if x > 60:
        print("ETA "+ str(x/60) + " minutes")
    else:
        print("ETA "+ str(x) + " seconds")

for i in songFiles:
    if i[-4:].lower() != ".mp3":
        # skip any non-mp3's (like directories or cover art)
        continue
    try:
        # get the metadata
        song = EasyID3(soundLocation+i)
        title = song['title'][0]
        artist = song['artist'][0]
    except:
        try:
            # if metadata is missing, try to use file name following title_artist.mp3
            song = i.split("_")
            title = song[0]
            artist = song[1].split(".")[0]
        except:
            #if the file is not formatted with an underscore, the title is the file name
            title = i
            artist = None
    if args.art.lower() == "true" and not(args.apikey == ""):
        try:
            # get the images from last fm, try 2 different sizes
            image = ast.literal_eval(requests.post(url="http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key="+apikeylastfm+"&artist="+artist+"&track="+title+"&format=json").text)["track"]["album"]["image"][2]["#text"]
            if image == "":
                image = ast.literal_eval(requests.post(url="http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key="+apikeylastfm+"&artist="+artist+"&track="+title+"&format=json").text)["track"]["album"]["image"][1]["#text"]
                if image == "":
                    image = None
            time.sleep(0.25)
        except:
            image=None
    else:
        image=None
    try:
        length = math.ceil(MP3(soundLocation+i).info.length)
    except:
        length = 0
    if len(songFiles) != 1:
        index = (songFiles.index(i))%4
        print("\r" + str(loading[index] + str(math.floor((songFiles.index(i)/(len(songFiles)-1))*100))+ "%"), end='', flush=True)
    # each "song" is stored as a dictionary/JSON entry following the format seen in the readME
    songDatabaseList["songData"][i] = ({"title":title,"artist":artist,"art":image,"length":length})
    
with open('songDatabase.json', 'w') as handle:
    json.dump(songDatabaseList, handle)
