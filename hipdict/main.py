from __future__ import division
import json
import requests


from flask import render_template, request
from ac_flask.hipchat import events
from ac_flask.hipchat.auth import tenant

from hipdict.exceptions import *
from hipdict import app, addon, tasks


# The regular expression for the slash command.
DICTIONARY_COMMAND_PATTERN = "(^\/[Mm][Ee][Aa][Nn][Ii][Nn][Gg])"


@addon.configure_page(path="/configure", methods=['GET'])
def configuration_page():
    """This function renders the HipChat Configuration page."""
    return _render_configuration_page()


def _render_configuration_page():
    model = {}
    message = ("Dictionary integration has been installed successfully in this room. Type /meaning <word>" +
               "to get the meaning of the word.")
    tasks.send_notification(tenant.id, message, tenant.room_id, color='green')
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
        word = input_message.split(" ")[1]
        message = get_meaning_of_the_word(word, tenant_id)
        list_of_meanings = get_list_of_meanings(message)
        html_message = "Sorry, We are unable to find the meaning of the word " + word + "."
        if list_of_meanings:
            data_to_parse = {}
            data_to_parse["list_of_meanings"] = list_of_meanings
            data_to_parse["word"] = word
            html_message = create_html_from_meaning_list(data_to_parse)
        tasks.send_notification(tenant_id, html_message, room_id)
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


def create_html_from_meaning_list(data_to_parse):
        return render_template('message_template.html', **data_to_parse)

def get_list_of_meanings(message):
    list_of_meanings = []
    if ('tuc' in message and  len(message['tuc']) > 0 and 
        'meanings' in message['tuc'][0] and len(message['tuc'][0]['meanings']) >0):
        for meaning in message['tuc'][0]['meanings']:
            if len(list_of_meanings) >= 5:
                break
            list_of_meanings.append(meaning["text"])
            
    return list_of_meanings


def get_meaning_of_the_word(word, tenant_id):
    """Retrieves unique and random room name from appear"""
    url = app.config['DICT_BASE_URL'] % (word)
    resp = requests.request('GET', url, timeout=14)
    if resp.status_code >= 200 and resp.status_code <= 299:
        app.logger.info("Generated random room for tenant :"
        + tenant_id)
        return resp.json()
    elif resp.status_code in (400, 404) or\
    (resp.status_code >= 405 and resp.status_code < 500):
        app.logger.error('Dict returned %d status code for tenant %s while\
         sending notification.' % (resp.status_code, str(tenant_id)))
        raise BadRequest()

    elif resp.status_code >= 500:
        app.logger.error('Dict returned %d status code for tenant %s while\
         sending notification.' % (resp.status_code, str(tenant_id)))
        raise InternalServerError()

    else:
        app.logger.error('Appear returned %d status code for tenant %s while \
        sending notification.' % (resp.status_code, str(tenant_id)))
        raise Exception('Appear returned %d status code for tenant %s while\
         sending notification.' % (resp.status_code, str(tenant_id)))


def on_install(params):
    """This function is called when user installs the add-on."""
    client = params['client']
    app.logger.info("Tenant : " + client.id + " has installed the integration")


def on_uninstall(params):
    """This function is called when user uninstalls the add-on."""
    client = params['client']
    app.logger.info("Tenant : " + client.id + " has uninstalled the integration")


events.register_event("uninstall", on_uninstall)
events.register_event("install", on_install)


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
