from mangum import Mangum
import json
import logging
from etradingview.asgi import application

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = Mangum(application)

def lambda_handler(event, context):
    logger.info("Received event: " + json.dumps(event))
    return handler(event, context)
