from ac_flask.hipchat.db import mongo, redis
from ac_flask.hipchat.tenant import Tenant
from hipdict import app


def get_tenant_token(tenant):
    return tenant.get_token(redis)


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
    settings['is_valid_hipchat_creds'] = True
    mongo['tenant_settings'].save(settings)


def get_tenant(tenant_id):
    try:
        return Tenant.load(tenant_id)
    except:
        app.logger.error("Not able to load tenant")
        return None
