from flask import Flask
from ac_flask.hipchat import Addon
import config
import os

_ENV_PREFIX = "HIPDICT_"


# The global flask application
app = Flask(__name__)

#This is HipChat's Addon object
#The Addon object has several methods that we use throughout the application
# IMPORTANT : Registering an addon loads the configuration from
#     - from config.py
#     - from environment variables that start with HIPDICT_
# It is therefore important to load addon object early in the game
addon = Addon(app,
              key=os.environ.get("%sADDON_KEY" % _ENV_PREFIX,
                                  "com.atlassian.HipDict"),
              name=os.environ.get("%sADDON_NAME" % _ENV_PREFIX,
                                    "Dict"),
              description="Get meaning of words by just typing /meaning work",
              config=config,
              env_prefix=_ENV_PREFIX,
              allow_global=False,
              allow_room=True,
              scopes=['send_notification'])


# Import this last so that views are loaded
from . import main
