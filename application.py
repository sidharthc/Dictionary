import logging

from logging.handlers import RotatingFileHandler
from hipdict import app as application

application.logger.setLevel(logging.INFO)
handler = RotatingFileHandler('application.log',
                               maxBytes=10000, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(module)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
application.logger.addHandler(handler)


if __name__ == '__main__':
    application.run(processes=2)
