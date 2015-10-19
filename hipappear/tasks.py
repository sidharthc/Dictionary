import db
import json
import os
import requests
import bson

from datetime import datetime
from boto.sqs.connection import SQSConnection
from json import JSONEncoder
from ac_flask.hipchat.auth import tenant
from flask import request
import xml.etree.ElementTree as ET
from stats import stats
from hipappear import app
from hipappear.exceptions import *


class TaskQueue:
    """This TaskQueue is used for local development purposes
    It isn't a queue. It simply executes tasks synchronously
    """
    def add(self, task_name, task_params=None, **kwargs):
        handler = _get_tasks_map()[task_name]
        handler(task_params)

    def is_empty(self):
        return True


class MongoEncoder(JSONEncoder):
    """Class that can encode MongoDB objects to JSON"""
    def default(self, obj):
        if isinstance(obj, bson.objectid.ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            if obj.utcoffset() is not None:
                obj = obj - obj.utcoffset()
            return obj.strftime('%Y-%m-%d %H:%M:%S.%f')

        return JSONEncoder.default(self, obj)


class SqsTaskQueue(TaskQueue):
    """This task queue adds the tasks to a specified AWS SQS queue
    Once a task is added, SQS automatically calls our task_handler at the URL
    /tasks. See function task_handler
    """
    def __init__(self, aws_key, aws_secret_key, sqs_queue_name):
        self._conn = SQSConnection(aws_key, aws_secret_key)
        self._q = self._conn.get_queue(sqs_queue_name)

    def add(self, task_name, task_params=None, delay_seconds=None, **kwargs):
        task_params = task_params or {}
        payload = {
                   "task_name": task_name,
                   "params": task_params
                   }
        payload_as_str = json.dumps(payload, cls=MongoEncoder)
        self._conn.send_message(self._q, payload_as_str,
                                delay_seconds=delay_seconds)

    def is_empty(self):
        # _q.count() returns an approximate count
        # .. so it is possible this function may return incorrect
        if self._q.count():
            return False
        return True

run_tasks_syncrhonously = app.config.get('RUN_TASKS_SYNCHRONOUSLY', os.environ.get('RUN_TASKS_SYNCHRONOUSLY'))
if run_tasks_syncrhonously and run_tasks_syncrhonously.lower() == 'true':
    taskqueue = TaskQueue()
else:
    _aws_key = os.environ.get('AWS_ACCESS_KEY_ID')
    _aws_secret_key = os.environ.get('AWS_SECRET_KEY')
    _sqs_queue_name = os.environ.get('AWS_SQS_QUEUE_NAME')
    taskqueue = SqsTaskQueue(_aws_key, _aws_secret_key, _sqs_queue_name)


def send_first_notification(tenant_id, room_id):
    taskqueue.add("send_install_notification", task_params = {"tenant_id": tenant_id, "room_id": room_id})


def _get_tasks_map():
    return {
        "send_install_notification": _send_install_notification,
    }


def _send_install_notification(params):
    room_id, tenant_id = params['room_id'], params['tenant_id']
    """Send first installation message to the room.
    """
    tenant_settings = db.get_tenant_settings(tenant_id)
    message = ("Start an <a href='" + app.config['APPEAR_URL'] + "'>appear.in</a> video " +
                 "conference by typing /appear.")
    if not tenant_settings or not tenant_settings['install_notification_sent']:
        db.set_settings_for_tenant(tenant_id)
        if room_id:
            send_notification(tenant_id, message, room_id, "green")
        else:
            try:
                data = get_all_rooms(tenant_id)
                for item in data:
                    send_notification(tenant_id, message, item['id'], "green")
            except Exception as ex:
                app.logger.info("An exception occurred while fetching the" +
                                " room list for tenant %s" % (str(tenant_id)))
                app.logger.error(ex)


def get_all_rooms(tenant_id):
    """This function returns all the rooms for a tenant"""
    room_url = "/room"
    min_result = 0
    max_result = 1000
    items = []
    while 1:
        params = ("&start-index=" + str(min_result) +
                   "&max-results=" + str(max_result))
        data = json.loads(get_response_from_hipchat(tenant_id, "GET",
                room_url, scope=['view_group'], params=params).content)
        items = items + data['items']
        if not ('links' in data and 'next' in data['links']):
            break
        min_result = max_result
        max_result = max_result + 1000
    return items


@app.route("/tasks", methods=['POST'])
def task_handler():
    """This function is automatically called by SQS when it's time to exectute a task
    If this function returns 200 status code, SQS assumes the task completed successfully
    If this function returns any error, SQS will automatically retry
    """
    if not _is_sqs_request():
        return '', 401
    params = request.get_json()
    if 'task_name' not in params:
        app.logger.error('task_name missing in POST body')
        return 'task_name missing in POST body', 401

    task_name = params['task_name']
    params = params['params']
    handler = _get_tasks_map()[task_name]
    if not handler:
        app.logger.error('Invalid Task - %s' % task_name)
        return 'Invalid Task - %s' % task_name, 401

    handler(params)
    return 'Task %s completed successfully' % task_name, 200


def send_notification(tenant_id, message, room_id, color='gray'):
    """Copied from AC_Flask_Hipchat
    Handles tenant in a stateless / non-threadlocal manner
    i.e. we pass in the tenant object
    """
    data = json.dumps({"message": message, "color": color, "notify": False, "message_format": 'html'})
    url = "/room/%s/notification" % (room_id)
    get_response_from_hipchat(tenant_id, "POST", url, data)
    stats.log_event("number_of_appear_url_created", {'tenant_id': tenant_id, 'room_id': room_id})
    app.logger.info("%s - notification successfully sent to the room %s, tenant %s" % (message, room_id, tenant_id))


def get_response_from_hipchat(tenant_id, method, url, data=None, scope=None, params = None):
    """A common function which can be used while making any request to HipChat"""
    tenant = db.get_tenant(tenant_id)
    try:
        token = db.get_tenant_token(tenant, scope)
    except:
        db.on_invalid_hipchat_credentials(tenant_id)
        stats.log_event("token_not_found", {'tenant_id': tenant_id,
                                            'group_id': tenant.group_id})
        app.logger.error("Could not find token for tenant " + tenant_id)
    base_url = tenant.capabilities_url[0:tenant.capabilities_url.rfind('/')]
    url = base_url + url + "?auth_token=" + token
    if params:
        url = url + params
    resp = requests.request(method, url, headers={'content-type': 'application/json'},
                             data=data, timeout=14)
    if resp.status_code >= 200 and resp.status_code <= 299:
        return resp

    elif resp.status_code in (401, 403):
        app.logger.info("Unauthorized access for tenant " + tenant_id)
        db.on_invalid_hipchat_credentials(tenant_id)
        raise InvalidCredentials()

    elif resp.status_code in (400, 404) or resp.status_code >= 405:
        app.logger.error('HipChat returned %d status code for tenant %s '
                         % (resp.status_code, str(tenant_id)))
        raise BadRequest()

    elif resp.status_code >= 500:
        app.logger.error('HipChat returned %d status code for tenant %s '
                         % (resp.status_code, str(tenant_id)))
        raise InternalServerError()

    else:
        app.logger.error('HipChat returned %d status code for tenant %s '
                         % (resp.status_code, str(tenant_id)))
        raise Exception('HipChat returned %d status code for tenant %s '
                        % (resp.status_code, str(tenant_id)))


def get_response_from_dictionary(word):
    url = app.config['DICT_API'] + word + "?key=" + app.config['DICT_API_KEY']
    resp = requests.request('GET', url, timeout=14)
    print "????????????????????????????????????????"
    print resp.content
    root = ET.fromstring(resp.content)
    print root
    print list(root)
    print "????????????????????????????????????????"


def _is_sqs_request():
    '''Checks if request is coming from SQS or not
    '''
    return request.remote_addr in ('127.0.0.1', )
