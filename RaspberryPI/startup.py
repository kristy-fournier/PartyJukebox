"""
Assume that this file is being run at startup, and should do all the things needed
    ()  Check USB for new mp3's
    ()  Check USB for updated data files (api keys, ports, )
    ()  Copy them to correct directory
    ()  Make sure the audio device is set to the 3.5mm jack
    ()  Run database updater if new files were found
    ()  Run Server
    ()  Run http module to host client
    ()  Generate a qr code and display it somehow (maybe)
"""
import threading, os, shutil, 
