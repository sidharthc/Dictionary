from flask import Flask
from ac_flask.hipchat import Addon
import config
import os

_ENV_PREFIX = "HIPAPPEAR_"

# This file exists to prevent coupling between web and tasks modules
# Anything shared between the foreground and background processes
# should be moved to this module

# The global flask application
app = Flask(__name__)

#This is HipChat's Addon object
#The Addon object has several methods that we use throughout the application
# IMPORTANT : Registering an addon loads the configuration from
#     - from config.py
#     - from environment variables that start with HIPAPPEAR_
# It is therefore important to load addon object early in the game
addon = Addon(app,
              key=os.environ.get("%sADDON_KEY" % _ENV_PREFIX,
                                  "com.atlassian.HipAppear"),
              name=os.environ.get("%sADDON_NAME" % _ENV_PREFIX,
                                    "Appear"),
              description="Initiate and Join an appear.in video call from a\
               HipChat Room. Use '/appear' command to generate appear.in link",
              config=config,
              env_prefix=_ENV_PREFIX,
              allow_global=True,
              allow_room=True,
              scopes=['send_notification', 'view_group'])


# Import this last so that views are loaded
from . import main
