import newrelic.agent
import logging

from logging.handlers import RotatingFileHandler
from hipappear import app as application

application.logger.setLevel(logging.INFO)
handler = RotatingFileHandler('/var/log/appear/application.log',
                               maxBytes=10000, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(module)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
application.logger.addHandler(handler)


if application.config['NEWRELIC_ENABLE']:
    newrelic.agent.initialize(application.config['NEW_RELIC_FILE'])
    application = newrelic.agent.wsgi_application()(application)

if __name__ == '__main__':
    application.run(processes=2)
