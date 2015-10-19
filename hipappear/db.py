from ac_flask.hipchat.db import mongo, redis
from ac_flask.hipchat.tenant import Tenant
from hipappear import app


def get_tenant_token(tenant, scope):
    return tenant.get_token(redis, scopes=scope)


def on_invalid_hipchat_credentials(tenant_id):
    mongo['tenant_settings'].update(
                {"tenant_id": tenant_id},
                {"$set": {"is_valid_hipchat_creds": False}}
        )


def get_tenant_settings(tenant_id):
    return mongo['tenant_settings'].find_one({"tenant_id": tenant_id}) or {}


def set_settings_for_tenant(tenant_id):
    settings = get_tenant_settings(tenant_id)
    settings['tenant_id'] = tenant_id
    settings['install_notification_sent'] = True
    settings['is_valid_trello_creds'] = True
    mongo['tenant_settings'].save(settings)


def get_tenant(tenant_id):
    try:
        return Tenant.load(tenant_id)
    except:
        app.logger.error("Not able to load tenant")
        return None


def get_count_of_organisations():
    """Gets the count of total number of
    organizations from client collection.
    """
    return mongo['clients'].find({'room_id': None}).count()


def get_all_clients_count():
    """Gets the list of all the clients in clients collection."""
    return mongo['clients'].find().count()
