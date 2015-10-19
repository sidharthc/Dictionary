from hipappear import app
from ac_flask.hipchat.db import redis


class DefaultLogger(object):
    def increment_stat(self, name, key, amount):
        redis.hincrby(name, key, amount)

    def get_stat(self, name, key):
        count = redis.hget(name, key)
        if count:
            return int(count)
        return 0


class StatsLogger(DefaultLogger):
    def log_event(self, event_name, args=None):
        app.logger.info("Event: %s & args: %s" % (event_name, str(args)))


class KeenIOStats(DefaultLogger):
    def __init__(self):
        from keen.client import KeenClient
        self.keen = KeenClient(
                project_id=app.config['KEEN_PROJECT_ID'],
                write_key=app.config['KEEN_WRITE_KEY'],
                read_key=app.config['KEEN_READ_KEY']
            )

    def log_event(self, event_name, args):
        self.keen.add_event(event_name, args)
        app.logger.info("Event: %s & args: %s" % (event_name, str(args)))


def _create_stats_object():
    if (app.config['KEEN_ENABLED'] and 
        str(app.config['KEEN_ENABLED']).lower() == 'true'):
        return KeenIOStats()
    else:
        return StatsLogger()

stats = _create_stats_object()
