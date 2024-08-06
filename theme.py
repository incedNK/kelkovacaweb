from contextlib import contextmanager
from nicegui import ui, app

@contextmanager
def user_frame():
    with ui.column().classes('w-full'):
        yield
    with ui.footer().classes('justify-between items-center bg-[#476D38] pl-6 pr-6'):
        with ui.column():
            ui.image('static/logos/logo.png')
            ui.label('Agro Konsultant')
        with ui.row().classes('h-20 items-center'):
            with ui.column().classes('gap-0'):
                ui.label('Podrzano od: /')
                ui.label('Supported by:')
            ui.image('static/logos/EU4AGRI.png').classes('w-20 h-20')
            
@contextmanager
def admin_frame():
    with ui.header().classes('justify-between').classes('bg-white items-center'):
        with ui.row():
            ui.link('Home', '/').classes('no-underline')
            ui.link('Crops', '/crops').classes('no-underline')
            ui.link('Alerts', '/alerts').classes('no-underline')
            ui.link('Map', '/map').classes('no-underline')
        with ui.row():
            with ui.link(target='/login'):
                ui.button(text='Logout', on_click=lambda: (app.storage.user.clear())).props('no-caps outline flat')
    with ui.column().classes('w-full'):
        yield
    with ui.footer().classes('justify-between items-center bg-[#476D38] pl-6 pr-6'):
        with ui.column():
            ui.image('static/logos/logo.png')
            ui.label('Agro Konsultant')
        with ui.row().classes('h-20 items-center'):
            with ui.column().classes('gap-0'):
                ui.label('Podrzano od: /')
                ui.label('Supported by:')
            ui.image('static/logos/EU4AGRI.png').classes('w-20 h-20')