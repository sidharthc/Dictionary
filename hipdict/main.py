from __future__ import division
import json
import requests

from flask import render_template, request
from ac_flask.hipchat import events
from ac_flask.hipchat.auth import tenant

from hipdict.exceptions import *
from hipdict import app, addon, tasks
from PyDictionary import PyDictionary

dictionary = PyDictionary()

# The regular expression for the slash command.
DICTIONARY_COMMAND_PATTERN = "(^\/[Dd][Ii][Cc][Tt])"


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


def construct_meaning(meaning):
    constructed_meaning = {}
    for key, value in meaning.iteritems():
        constructed_meaning[key] = value[0]
    return constructed_meaning


@app.route('/dictionary_callback_url', methods=["POST"])
@addon.webhook(event="room_message", pattern=DICTIONARY_COMMAND_PATTERN)
def _handle_dict_callback():
    """This function acts as a HipChat webhook and responds
    whenever it encounters the appropriate slash command.
    """
    data = json.loads(request.data)
    room_id = data['item']['room']['id']
    tenant_id = data['oauth_client_id']
    input_message = data['item']['message']['message']
    if len(input_message.split(" ")) > 2:
        message = "Please enter single word to know its meaning."
    elif len(input_message.split(" ")) == 1:
        message = "Usage: /dict <<word>>. It will return you the meaning of the word."
    else:
        word = input_message.split(" ")[1]
        meaning = dictionary.meaning(word)
        synonym = dictionary.synonym(word)
        antonym = dictionary.antonym(word)
        message = "Sorry, We are unable to find meaning of the word <b>'" + word + "'</b>. Please try some other word."
        if meaning:
            meaning = construct_meaning(meaning)
            if synonym:
                synonym = ', '.join(synonym)
            if antonym:
                antonym = ', '.join(antonym)
            message = create_html_from_meaning_list(word, meaning, synonym, antonym)
    try:
        tasks.send_notification(tenant_id, message, room_id, color="random")
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


def create_html_from_meaning_list(word, meaning, synonym, antonym):
    data_to_parse = {"meanings": meaning, "synonym": synonym, "antonym": antonym, "word": word}
    if not synonym:
        del data_to_parse["synonym"]
    if not antonym:
        del data_to_parse["antonym"]
    return render_template('message_template.html', **data_to_parse)


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
