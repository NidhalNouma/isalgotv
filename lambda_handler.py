from mangum import Mangum
from etradingview.asgi import application

# handler = Mangum(application)
def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/plain"
        },
        "body": "Hello from Lambda"
    }
