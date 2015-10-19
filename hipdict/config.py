# To override any of these settings in production,
# create environment variables with the prefix HIPDICT_
#
# For example, to override BASE_URL, you create an environment variable
# HIPDICT_BASE_URL='blah'

# This is a flask property for session secrets
SECRET_KEY = 'super secret stuff'

DEBUG = False


#Addon vendor properties
ADDON_VENDOR_NAME = "HipChat"
ADDON_VENDOR_URL = "https://www.hipchat.com"


#This is required by HipChat plugin to generate fully qualified urls
BASE_URL = "https://17e50875.ngrok.com"

DICT_BASE_URL = "https://glosbe.com/gapi/translate?from=eng&dest=eng&format=json&phrase=%s&page=1&pretty=true"
