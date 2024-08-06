from nicegui import ui, app
import auth
import web
from config import secret_key



app.include_router(auth.router)
app.include_router(web.router)

ui.run(title="Klekovaca", storage_secret=secret_key, favicon='static/favicon.ico')