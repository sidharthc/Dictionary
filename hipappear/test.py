import threading
import atexit
from flask import Flask
from threading import Thread
import main
import requests

POOL_TIME = 5 #Seconds

# variables that are accessible from anywhere
commonDataStruct = {}
# lock to control access to variable
dataLock = threading.Lock()
# thread handler
yourThread = threading.Thread()


def create_app():
    app = Flask(__name__)

    def interrupt():
        global yourThread
        yourThread.cancel()

    def doStuff():
        global commonDataStruct
        global yourThread
        with dataLock:
        # Do your stuff with commonDataStruct Here
            '''resp = requests.request('GET', 'https://www.google.com', headers={'content-type': 'application/json'},
                             data=None)'''
            main.send_first_notification()
            #print "?????????????", resp
            #main.send_first_notification()
        # Set the next thread to happen
        yourThread.start()   

    def doStuffStart():
        # Do initialisation stuff here
        global yourThread
        # Create your thread
        yourThread = Thread(target=doStuff, args=())
        yourThread.start()

    # Initiate
    doStuffStart()
    # When you kill Flask (SIGTERM), clear the trigger for the next thread
    atexit.register(interrupt)
    return app

