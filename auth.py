from typing import Optional

from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from jose import jwt, ExpiredSignatureError
from datetime import datetime, timezone
import models
import config

from nicegui import Client, app, ui, APIRouter

router = APIRouter()
app.add_static_files('/static', 'static')
unrestricted_page_routes = {'/login'}

class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware restricts access to all NiceGUI pages.

    It redirects the user to the login page if they are not authenticated.
    """
    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('auth_token', None):
            if request.url.path in Client.page_routes.values() and request.url.path not in unrestricted_page_routes:
                app.storage.user['referrer_path'] = request.url.path  # remember where the user wanted to go
                return RedirectResponse('/login')
        else:
            try:
                payload = jwt.decode(app.storage.user['auth_token'], config.secret_key, algorithms=[config.algorithm])
                expire: datetime=payload.get("exp")
                if datetime.now(timezone.utc).timestamp() > expire:
                    app.storage.user.update({'username': None, 'auth_token': None, 'lang': None})     
            except ExpiredSignatureError:
                app.storage.user.update({'username': None, 'auth_token': None, 'lang': None})
                return RedirectResponse('/login')
        return await call_next(request)

app.add_middleware(AuthMiddleware)


@router.page('/login')
def login(session: Session = Depends(config.get_session)) -> Optional[RedirectResponse]:
    def try_login() -> None:
        user = session.query(models.User).filter(models.User.email == username.value).first()
        if not user:
            username.value = ''
            password.value = ''
            ui.notify('Wrong username or password', position='top', color='negative')
        if not config.verify_password(plain_password=password.value, hashed_password=user.hashed_password):
            username.value = ''
            password.value = ''
            ui.notify('Wrong username or password', position='top', color='negative')
        else:
            access_token = config.create_access_token(data={"sub": user.email})
            app.storage.user.update({'username': username.value, 'auth_token': access_token, 'lang': lang.value})
            ui.navigate.to(app.storage.user.get('referrer_path', '/'))  # go back to where the user wanted to go
            
    ui.query('.nicegui-content').classes('p-0')
    with ui.image('/static/img/background.png').classes('h-screen w-screen'): 
        with ui.card().classes('xl:w-2/6 h-4/6 absolute-center bg-[#C3D66A] opacity-80 justify-between'):
            with ui.grid(columns=2).classes('justify-between w-full p-2 mb-4'):
                    ui.label('Agro Konsultant').classes('font-bold text-white xl:text-4xl')
                    ui.image('static/logos/logo.png').classes('xl:w-[170px] xl:h-[100px] justify-self-end')
            with ui.column().classes('w-full p-4 rounded-lg bg-white border-2 mb-4'):
                username = ui.input(placeholder='Korisnik/User').props('rounded-lg outlined dense').classes('w-full').on('keydown.enter', try_login)
                password = ui.input(placeholder='Lozinka/Password', password=True, password_toggle_button=True).props('rounded-lg outlined dense').classes('w-full').on('keydown.enter', try_login)
                with ui.row().classes('no-wrap w-full justify-between'):
                    with ui.column().classes('gap-0 w-1/2 self-center'):
                        ui.label('Odaberite jezik /').classes('text-black text-xs')
                        ui.label('Choose the language:').classes('text-black text-xs')
                    lang = ui.select({'en': 'English', 'sr': 'Српски', 'hr': 'Hrvatski', 'ba': 'Bosanski'}, value='en').classes('w-full place-items-center')
            ui.button('Login', on_click=try_login).classes('w-full')


    