import db
import json
import requests

from hipdict import app
from hipdict.exceptions import *


def send_notification(tenant_id, message, room_id, color='gray'):
    """Copied from AC_Flask_Hipchat
    """
    data = json.dumps({"message": message, "color": color, "notify": False, "message_format": 'html'})
    url = "/room/%s/notification" % (room_id)
    get_response_from_hipchat(tenant_id, "POST", url, data)
    app.logger.info("%s - notification successfully sent to the room %s, tenant %s" % (message, room_id, tenant_id))


def get_response_from_hipchat(tenant_id, method, url, data=None):
    """A common function which can be used while making any request to HipChat"""
    tenant = db.get_tenant(tenant_id)
    token = db.get_tenant_token(tenant)

    base_url = tenant.capabilities_url[0:tenant.capabilities_url.rfind('/')]
    url = base_url + url + "?auth_token=" + token
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

