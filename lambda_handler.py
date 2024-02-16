from mangum import Mangum
from etradingview.asgi import application

handler = Mangum(application, lifespan="off")

