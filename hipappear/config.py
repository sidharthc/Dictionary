# To override any of these settings in production,
# create environment variables with the prefix HIPAPPEAR_
#
# For example, to override SECRET_KEY, you create an environment variable
# HIPAPPEAR_SECRET_KEY='blah'

#MONGOHQ_URL
#REDISTOGO_URL

# This is a flask property for session secrets
SECRET_KEY = 'super secret stuff'

DEBUG = False

# Keep sessions for 1 hour only
# We do not use sessions directly, but the HipChat plugin
# apparently uses sessions during the authentication phase
PERMANENT_SESSION_LIFETIME = 3600

#Addon vendor properties
ADDON_VENDOR_NAME = "HipChat"
ADDON_VENDOR_URL = "https://www.hipchat.com"

#Newrelic settings
NEWRELIC_ENABLE = False
NEW_RELIC_FILE = './newrelic.ini'

LOAD_TESTING = False

#This is required by HipChat plugin to generate fully qualified urls
BASE_URL = "https://17e50875.ngrok.com"

APPEAR_URL = "https://appear.in/"
APPEAR_BASE_URL = "https://appear.in"
APPEAR_API_BASE_URL = "https://api.appear.in/"

DICT_API = "http://www.dictionaryapi.com/api/v1/references/collegiate/xml/"
DICT_API_KEY = "575993b8-f522-40fc-909d-4ce04728e067"
KEEN_ENABLED = False

KEEN_TIME_FRAME_TEXT = [
             {
              "id": "this_1_days",
              "text": "Today"
              },
             {
              "id": "this_7_days",
              "text": "This 7 days"
              },
             {
              "id": "this_15_days",
              "text": "This 15 days"
              },
             {
              "id": "this_30_days",
              "text": "This 30 days"
              },
             {
              "id": "this_45_days",
              "text": "This 45 days"
              },
             {
              "id": "this_60_days",
              "text": "This 60 days"
              }
             ]
KEEN_INTERVAL = "every_12_hours"
