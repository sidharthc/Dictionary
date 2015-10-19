from __future__ import division
import db
import json
import requests
import uuid
import re

from stats import stats
from hipappear import app, addon, tasks
from flask import render_template, request, Response
from ac_flask.hipchat import events
from functools import wraps
from hipappear.exceptions import *
from ac_flask.hipchat.auth import tenant

# The regular expression for the slash command.
APPEAR_COMMAND_PATTERN = "(^\/([Aa][Pp][Pp][Ee][Aa][Rr])([\s])?(.|\n)*$)"
APPEAR_KEYWORD_PATTERN = "(^\/([Aa][Pp][Pp][Ee][Aa][Rr])([\s])?)"
DICTIONARY_COMMAND_PATTERN = "(^\/[Dd][Ii][Cc][Tt])" 

@addon.configure_page(path="/configure", methods=['GET'])
def configuration_page():
    """This function renders the HipChat Configuration page."""
    return _render_configuration_page()


def _render_configuration_page():
    model = {}
    tasks.send_first_notification(tenant.id, tenant.room_id)
    return render_template('configure.html', **model)


@app.route('/dicctionary_callback_url', methods=["POST"])
@addon.webhook(event="room_message", pattern=DICTIONARY_COMMAND_PATTERN)
def _handle_appear_callback():
    """This function acts as a HipChat webhook and responds
    whenever it encounters the appropriate slash command.
    """
    data = json.loads(request.data)
    room_id = data['item']['room']['id']
    tenant_id = data['oauth_client_id']
    input_message = data['item']['message']['message']
    message = "success"
    if len(input_message.split(" ")) > 2:
        message = "Please enter single word to know its meaning."
    elif len(input_message.split(" ")) == 1:
        message = "Usage: /dict <<word>>. It will return you the meaning of the word."
    else:
        get_meaning_from_dictionary(input_message.split(" ")[1])
    try:
        tasks.send_notification(tenant_id, message, room_id)
    except InvalidCredentials as ex:
        app.logger.error(ex)
        return "Invalid Credentials", 401
    except BadRequest as ex:
        app.logger.error(ex)
        return "Bad Request", 400
    except InternalServerError as ex:
        app.logger.error(ex)
        return "Internal Server Error", 500
    except Exception as ex:
        app.logger.error(ex)
    return "Success", 200


def get_meaning_from_dictionary(word):
    response = tasks.get_response_from_dictionary(word)
    return response


def generate_notification_message(data):
    """This function generates a proper notification message to
    sent to the HipChat room
    """
    user = data['item']['message']['from']['name']
    room_id = data['item']['room']['id']
    tenant_id = data['oauth_client_id']
    message = re.sub(APPEAR_KEYWORD_PATTERN, '',
                     data['item']['message']['message']).strip()
    if len(message) > 0:
        notification_message = ("To start <a href='" + app.config['APPEAR_URL'] + "'>" +
                                "appear.in</a> video conference, just type \"/appear\".")
    else:
        notification_message = "Join " + user + "'s "\
                     + create_appears_link(tenant_id, str(room_id)) + "."
    return notification_message


def get_appear_random_room_name(tenant_id):
    """Retrieves unique and random room name from appear"""
    resp = requests.post(app.config['APPEAR_API_BASE_URL'] + "random-room-name")
    if resp.status_code >= 200 and resp.status_code <= 299:
        app.logger.info("Generated random room for tenant :"
        + tenant_id)
        return resp.json()['roomName']
        '''Since Appear api doesn't have authentication. removing exception handeling for invalid Credentials'''
    elif resp.status_code in (400, 404) or\
    (resp.status_code >= 405 and resp.status_code < 500):
        app.logger.error('Appear returned %d status code for tenant %s while\
         sending notification.' % (resp.status_code, str(tenant_id)))
        raise BadRequest()

    elif resp.status_code >= 500:
        app.logger.error('Appear returned %d status code for tenant %s while\
         sending notification.' % (resp.status_code, str(tenant_id)))
        raise InternalServerError()

    else:
        app.logger.error('Appear returned %d status code for tenant %s while \
        sending notification.' % (resp.status_code, str(tenant_id)))
        raise Exception('Appear returned %d status code for tenant %s while\
         sending notification.' % (resp.status_code, str(tenant_id)))


def create_appears_link(tenant_id, room_id):
    """This function creates a appear link by adding a unique random room\
     name provided by appear."""
    try:
        random_room_name = get_appear_random_room_name(tenant_id)
    except Exception as ex:
        random_room_name = str(uuid.uuid4())
    url = app.config['APPEAR_BASE_URL'] + random_room_name
    app.logger.info("Generated url:" + url + " for room :" + room_id + " and \
     tenant_id : " + tenant_id)
    notification_message = "<a href = '" + url + "'>appear.in conference</a>"
    return notification_message


def check_auth(username, password):
    """This function is used to authenticate admin user."""
    admin_username = app.config['USERNAME']
    admin_password = app.config['PASSWORD']
    if username == admin_username and password == admin_password:
        return True
    return False


def authenticate():
    """Send 401, if admin credentials are wrong."""
    return Response(
                'Could not verify your access level for that URL.\n'
                'You have to login with proper credentials', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def on_install(params):
    """This function is called when user installs the add-on."""
    client = params['client']
    stats.log_event("install", {'tenant_id': client.id})
    app.logger.info("Tenant : " + client.id + " has installed the integration")


def on_uninstall(params):
    """This function is called when user uninstalls the add-on."""
    client = params['client']
    stats.log_event("uninstall", {'tenant_id': client.id})
    app.logger.info("Tenant : " + client.id + " has uninstalled the integration")

events.register_event("uninstall", on_uninstall)
events.register_event("install", on_install)


@app.route('/admin')
@requires_auth
def statistics():
    """This function renders the data of the admin page."""
    organization_installs = db.get_count_of_organisations()
    total_installs = db.get_all_clients_count()
    model = {
        'project_id': app.config['KEEN_PROJECT_ID'],
        'read_key': app.config['KEEN_READ_KEY'],
        'active_organization_installs': organization_installs,
        'active_room_installs': (total_installs - organization_installs),
        'time_frame_text': (app.config['KEEN_TIME_FRAME_TEXT']),
        'interval': app.config['KEEN_INTERVAL']
    }
    return render_template('admin_statistics.html', **model)


# This function is called when the admin logs out.
@app.route('/admin/logout')
def logout():
    return Response("You have successfully logged out.<a href='/admin'>\
    Login</a>", 401)


@app.errorhandler(404)
def page_not_found(error):
    """Called when the application receives 404 error."""
    response = {"status": 404,
                "title": "The page you are trying to access does not exist.",
                "body": "You may have clicked an old link or mistyped the URL."
            }
    return render_template('error.html', msg=response)


@app.errorhandler(500)
def internal_server_error(err):
    """Called when the application receives 500 error."""
    response = {"status": 500,
                "title": "Internal Server Error!",
                "body": "The server encountered an internal error or\
                 misconfiguration and was unable to complete your request."
            }
    app.logger.error("Internal server error.")
    return render_template('error.html', msg=response)
