import os
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import mutagen.flac
import mutagen.wave
import sqlite3 as sql
import requests, ast, time, math, argparse

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
fileOfDB = sql.connect("songDatabase.db")
songDatabase = fileOfDB.cursor()
# setting song directory
songDatabase.execute("CREATE TABLE IF NOT EXISTS meta (id TEXT PRIMARY KEY, data TEXT);")
try:
    songDatabase.execute("INSERT INTO meta (id, data) VALUES (?,?)",("songDirectory",soundLocation))
except:
    songDatabase.execute("UPDATE meta SET data = ? WHERE id = 'songDirectory'", (soundLocation,))
if args.mode.lower() == "update":
    #Create if not exists
    songDatabase.execute("CREATE TABLE IF NOT EXISTS songs (filename TEXT PRIMARY KEY, title TEXT, artist TEXT, art TEXT, length INTEGER, lossless INTEGER);")
    songDatabase.execute("SELECT filename FROM songs;")
    dBfilelist = songDatabase.fetchall()
    dBfilelistSet = set()
    for i in dBfilelist:
        dBfilelistSet.add(i[0])
    # Delete nonexistant files
    deleteySongs = list(dBfilelistSet - set(songFiles))
    songDatabase.executemany("DELETE FROM songs WHERE filename = ?", [(item,) for item in deleteySongs]) # in this line it turns the list of strings into a list of tuples of strings
    print("Deleted: " + ", ".join(deleteySongs)+ " from database")
    # only include new files in list to be used
    songFiles = list(set(songFiles) - dBfilelistSet)
    print("new songs: " + ", ".join(songFiles))
elif args.mode.lower()=="new":
    songDatabase.execute("DROP TABLE IF EXISTS songs;")
    songDatabase.execute("CREATE TABLE songs (filename TEXT PRIMARY KEY, title TEXT, artist TEXT, art TEXT, length INTEGER, lossless INTEGER);")
else:
    raise ValueError("Must be \"new\" or \"update\"")

if args.art.lower() == "true" and not(args.apikey == ""):
    x = len(songFiles)*0.25
    if x > 60:
        print("ETA "+ str(x/60) + " minutes")
    else:
        print("ETA "+ str(x) + " seconds")

# will be used soon
validFormats = ["mp3","flac","wav"]

for i in songFiles:
    # songFiles is the list of filenames, so i is the filename of each song
    global song
    filenamesplit = i.split(".")
    extension = filenamesplit[len(filenamesplit)-1]
    lossless = 0 # sqlite doesn't have booleans. what is this, C?
    if not(extension.lower() in validFormats):
        # skip any non music files (like directories or cover art)
        continue
    try:
        # get the metadata
        if(extension.lower() == "mp3"):
            song = EasyID3(soundLocation+i)
        elif(extension.lower() == "flac"):
            song = mutagen.flac.FLAC(soundLocation+i)
            lossless = 1
        elif(extension.lower() in ["wav","wave"]):
            # Im actually pretty sure waves can't have metadata, but whatevz
            song = mutagen.wave.WAVE(soundLocation+i)
            lossless = 1
        title = song['title'][0]
        artist = song['artist'][0]
    except:
        if "_" in i:
            # if metadata is missing, try to use file name following "title_artist.mp3"
            song = i.split("_")
            title = song[0]
            artist = song[1].split(".")[0]
        elif "-" in i:
            # if there's no underscore, try "artist - title.mp3"
            song = i.split("-")
            title = song[1].split(".")[0]
            artist = song[0]
            title = title.strip()
            artist = artist.strip()
        else:
            #if the file is not formatted with an underscore or hyphen, the title is the file name
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
        if extension.lower() in ['flac','wave','wav']:
            length = math.ceil(song.info.length)
        elif extension.lower() == "mp3":
            # for some reason ID3 and mutagen.mp3 get different info
            # artist and title are in id3() and length is in mp3()
            # I dunno why
            length = MP3(soundLocation+i).info.length
    except:
        length = 0
    if len(songFiles) != 1:
        index = (songFiles.index(i))%4
        print("\r" + str(loading[index] + str(math.floor((songFiles.index(i)/(len(songFiles)-1))*100))+ "%"), end='', flush=True)
    # each "song" is stored as a SQLite entry following the format seen below
    songDatabase.execute(f"INSERT INTO songs (filename, title, artist, art, length, lossless) VALUES (?,?,?,?,?,?)",(i,title,artist,image,length,lossless))

songDatabase.execute("DROP TABLE IF EXISTS virtualSongs;")
songDatabase.execute("CREATE VIRTUAL TABLE virtualSongs USING fts5(filename, title, artist, art, length, lossless);")
songDatabase.execute("INSERT INTO virtualSongs SELECT * FROM songs;")
fileOfDB.commit()
fileOfDB.close()