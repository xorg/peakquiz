import sys
from pathlib import Path

sys.path.insert(0, '/home/xorg/peakquiz_v2/backend')

from dotenv import load_dotenv  # noqa: E402
from a2wsgi import ASGIMiddleware  # noqa: E402

load_dotenv(Path(__file__).parent / '.env')

from app.main import app as asgi_app  # noqa: E402

application = ASGIMiddleware(asgi_app, lifespan="off")