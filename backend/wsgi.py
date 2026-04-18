import sys
sys.path.insert(0, '/home/xorg/peakquiz_v2/backend')

from app.main import app as asgi_app
from a2wsgi import ASGIMiddleware

application = ASGIMiddleware(asgi_app)