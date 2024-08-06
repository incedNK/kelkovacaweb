from nicegui import ui, events, app, APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
import models
import config
from theme import user_frame, admin_frame
from datetime import datetime
import asyncio
from lang import lang_list
import shapely
import folium

router = APIRouter()       

# App pages
@router.page('/')
def main_page(session: Session= Depends(config.get_session)) -> None:
    active_alerts = []
    devices = []
    crop_dict = {}
    parcel_dict = {}
    my_parcels = []
    my_sensors = []
    current_user = session.query(models.User).filter(models.User.email == app.storage.user["username"]).first()
    lg_id = app.storage.user['lang']
    for parcel in current_user.parcels:
        parcel_dict.update({parcel.id: parcel.name})
        e = parcel.location
        if e:
            existing_locations = shapely.wkb.loads(bytes(e.data), hex=True)
            my_parcels.append({'location':existing_locations, 'name': parcel.name})
        for alert in parcel.alerts:
            if alert.is_active:
                active_alerts.append(alert)
        for sensor in parcel.devices:
            loc = sensor.location
            if loc:
                sensor_location = shapely.wkb.loads(bytes(loc.data), hex=True)
                my_sensors.append({'location':sensor_location, 'ID': sensor.sensor_id})
            devices.append(sensor)
    db_user = session.query(models.User).filter(models.User.id == current_user.id)
    user = db_user.first()
    all_crops = session.query(models.Crop).all()
    for crop in all_crops:
        crop_dict.update({crop.id: crop.name})
    
    """User functions"""
    def change_password():
        entry = {}
        test_password = config.verify_password(old_password.value, user.hashed_password)
        if not test_password:
            ui.notify('Wrong password', position='top', color='negative')
        elif new_password.value != retyped.value:
            ui.notify('Both passwords must match each other!', position='top', color='negative')
        else:
            entry['hashed_password'] = config.get_password_hash(password=new_password.value)
            entry['date'] = datetime.now()
            db_user.update(entry, synchronize_session=False)
            session.commit()
            ui.notify('Password changed.', position='top', color='positive')
        setting_dialog.close()
        profile_dialog.close()
    def edit_user():
        entry = {}
        entry['phone'] = int(phone.value)
        entry['email_alert'] = email.value
        entry['sms_alert'] = sms.value
        entry['date'] = datetime.now()
        db_user.update(entry, synchronize_session=False)
        session.commit()
        ui.notify('Changed settings.', position='top', color='positive')
        setting_dialog.close()
        profile_dialog.close()
    
    """ Alert functions"""
    async def deactivate_alert(id:int):
        db_alert = session.query(models.Alert).filter(models.Alert.id == id)
        entry = {}
        entry['is_active'] = False
        entry['date'] = datetime.now()
        db_alert.update(entry, synchronize_session=False)
        session.commit()
        alert_dialog.close()
        ui.notify('Alert removed.', position='top', color='negative')
        await asyncio.sleep(1)
        ui.navigate.reload()
    
    """ Parcel functions """
    async def delete_parcel(id: int):
        db_parcel = session.query(models.Parcel).filter(models.Parcel.id == id)
        db_parcel.delete(synchronize_session=False)
        session.commit()
        get_parcel_dialog.close()
        ui.notify('Parcel deleted.', position='top', color='negative')
        await asyncio.sleep(1)
        ui.navigate.reload()
    async def create_parcel():
        data = models.Parcel(owner_id= current_user.id, name= new_parcel_name.value, crop_id= new_parcel_crop.value, sow_complete=False)
        session.add(data)
        session.commit()
        create_parcel_dialog.close()
        get_parcel_dialog.close()
        ui.notify('Added new parcel', position='top', color='positive')
        await asyncio.sleep(1)
        ui.navigate.reload()
    
    """ Sensor functions """
    async def delete_sensor(id: int):
        db_sensor = session.query(models.Sensor).filter(models.Sensor.id == id)
        db_sensor.delete(synchronize_session=False)
        session.commit()
        get_sensor_dialog.close()
        ui.notify('Sensor deleted.', position='top', color='negative')
        await asyncio.sleep(1)
        ui.navigate.reload()
    async def create_sensor():
        data = models.Sensor(parcel_id=parcel_id.value, sensor_id=sensor_id.value, config=30)
        session.add(data)
        session.commit()
        create_sensor_dialog.close()
        get_sensor_dialog.close()
        ui.notify('Added new sensor', position='top', color='positive')
        await asyncio.sleep(1)
        ui.navigate.reload()
    if not current_user.is_admin:    
        with user_frame():
            #map =ui.leaflet(center=(44.5108, 16.4786), zoom=13, options={'attributionControl': 0}).classes('absolute-center items-center h-full')
            #map.tile_layer(url_template='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}')
            # for x in my_parcels:
            #     m.generic_layer(name='polygon', args=[list(x.exterior.coords)])
            # for y in my_sensors:
            #     m.marker(latlng=(y.x, y.y))
            
            map = folium.Map(location=(44.5108, 16.4786), zoom_start=13, attributionControl=0)
            folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Satellite',
            overlay=False,
            control=True
            ).add_to(map)
            for x in my_parcels:
                folium.Polygon(
                    locations=list(x['location'].exterior.coords),
                    tooltip=x['name']
                    ).add_to(map)
            for y in my_sensors:
                name = y['ID']
                folium.Marker(
                    location=[y['location'].x, y['location'].y],
                    popup= f'<a href="/fig/{name}" target="_blank">{name}</a>'
                ).add_to(map)
            ui.html(map.get_root()._repr_html_()).classes('w-full h-full absolute-center items-center')
                
            with ui.column().classes('self-end'):
                
                """ Setting dialog to update users data """
                with ui.dialog() as setting_dialog,ui.row(), ui.card().classes('mx-auto'):
                    with ui.row().classes('w-full no-wrap'):
                        with ui.column().classes('w-1/2 gap-0'):
                            ui.label(lang_list[lg_id]['password_label']).classes('font-bold')
                            old_password = ui.input(placeholder=lang_list[lg_id]['old_password'], password=True, password_toggle_button=True).props('rounded-lg outlined dense').classes('text-xs mb-1').on('keydown.enter', change_password)
                            new_password = ui.input(placeholder=lang_list[lg_id]['new_password'], password=True, password_toggle_button=True).props('rounded-lg outlined dense').classes('text-xs mb-1')
                            retyped = ui.input(placeholder=lang_list[lg_id]['retype'], password=True, password_toggle_button=True).props('rounded-lg outlined dense').classes('text-xs mb-3').on('keydown.enter', change_password)
                            ui.button(lang_list[lg_id]['submit_btn'], on_click=change_password)
                        with ui.column().classes('items-end gap-0'):
                            ui.label(lang_list[lg_id]['setting_label']).classes('font-bold')
                            with ui.row().classes('no-wrap'):
                                ui.label(lang_list[lg_id]['phone']).classes('self-center w-1/2')
                                phone = ui.number(placeholder=current_user.phone, value=current_user.phone)
                            with ui.row().classes('no-wrap'):
                                ui.label(lang_list[lg_id]['email']).classes('text-xs self-center')
                                email = ui.switch(value=current_user.email_alert)
                            with ui.row().classes('no-wrap'):
                                ui.label(lang_list[lg_id]['sms']).classes('text-xs self-center')
                                sms = ui.switch(value=current_user.sms_alert)
                            ui.button(lang_list[lg_id]['submit_btn'], on_click=edit_user)
                
                """ Profile dialog to choose edit profile dialog or logout the system"""
                with ui.dialog().props('position=right') as profile_dialog:
                    with ui.row():
                        with ui.button(icon='settings', on_click=setting_dialog.open).props('round'):
                            ui.tooltip(lang_list[lg_id]['setting'])
                        with ui.button(on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login')), icon='logout').props('round'):
                            ui.tooltip(lang_list[lg_id]['logout']) 
                            
                """ Dialog to review alerts from sensors """
                with ui.dialog() as alert_dialog, ui.row().classes('w-[800px]'):
                    columns = [{'name': 'date', 'label': lang_list[lg_id]['alert_date'], 'field': 'date', 'align': 'left'},
                                {'name': 'text', 'label': lang_list[lg_id]['alert_msg'], 'field': 'text', 'align': 'left'},
                                {'name': 'parcel_id', 'label': lang_list[lg_id]['parcel_id'], 'field': 'parcel_id', 'align': 'left'},
                                {"name": "action", "label": "", "field": "id", "align": "center"}]
                    rows = []
                    for alert in active_alerts:
                        values = {}
                        values.update({'date': alert.date.strftime('%d-%m-%Y %H:%M'), 'text': alert.text, 'parcel_id': alert.parcel_id, 'id': alert.id})
                        rows.append(values)
                    with ui.table(title=lang_list[lg_id]['alert_table'], columns=columns, rows=rows, pagination=3).classes(
                                'justify-items-center').classes('w-full bordered') as user_alert_table:
                        with user_alert_table.add_slot('top-right'):
                            with ui.input(placeholder=lang_list[lg_id]['search']).props('type=search').bind_value(user_alert_table, 'filter').add_slot('append'):
                                ui.icon('search')
                        user_alert_table.add_slot(f'body-cell-action', """
                            <q-td :props="props">
                                <q-btn @click="$parent.$emit('update', props)" icon="delete" flat dense color='red'/>
                            </q-td>
                            """)
                        user_alert_table.on('update', lambda e: deactivate_alert(e.args["row"]["id"]))
                        
                """ Dialog to add new parcels """
                with ui.dialog() as create_parcel_dialog, ui.card():
                    ui.label(lang_list[lg_id]['add_parcel']).classes('w-full font-bold')
                    with ui.row().classes('no-wrap w-full justify-between'):
                        ui.label(lang_list[lg_id]['myparcel_name']).classes('self-center text-xs')
                        new_parcel_name = ui.input()
                    with ui.row().classes('no-wrap w-full justify-between'):
                        ui.label(lang_list[lg_id]['myparcel_crop']).classes('self-center text-xs')
                        new_parcel_crop = ui.select(crop_dict).classes('w-1/2')
                    ui.button(lang_list[lg_id]['submit_btn'], on_click=create_parcel).classes('w-full')
                
                # Function for drawing parcel
                async def draw_parcel(id:int):
                    draw_parcel_dialog.open()
                    data = await draw_parcel_dialog
                    geometry = shapely.geometry.shape(data)
                    wkb_geometry = shapely.wkb.dumps(geometry, hex=True, srid=4326)
                    occupied_parcels = []
                    all_parcels = session.query(models.Parcel).all()
                    for one_parcel in all_parcels:
                        e = one_parcel.location
                        if e:
                            all_locations = shapely.wkb.loads(bytes(e.data), hex=True)
                            occupied_parcels.append(all_locations)
                    condition_right = []
                    for x in occupied_parcels:
                        if x.intersects(geometry):
                            condition_right.append(False)   
                    if not False in condition_right:
                        entry = {}
                        entry['location'] = wkb_geometry
                        entry['date'] = datetime.now()
                        db_parcel = session.query(models.Parcel).filter(models.Parcel.id == id)
                        db_parcel.update(entry, synchronize_session=False)
                        session.commit()
                        ui.notify('Location created.', position='top', color='positive')
                    else:
                        ui.notify('Location exists.', position='top', color='negative')
                    get_parcel_dialog.close()
                    await asyncio.sleep(1)
                    ui.navigate.reload()
                
                # Call on drawable parcel dialog
                with ui.dialog() as draw_parcel_dialog, ui.card().classes('w-[600px] h-[350px]'):
                    polygon_1 = []
                    coordinates = [polygon_1]
                    geometry = {'type': 'Polygon', 'coordinates': coordinates}
                    def handle_parcel_draw(e: events.GenericEventArguments):
                        if e.args['layerType'] == 'polygon':
                            p.generic_layer(name='polygon', args=[e.args['layer']['_latlngs']])
                            polygon_points = e.args['layer']['_latlngs'][0]
                            for point in polygon_points:
                                polygon_1.append([point['lat'], point['lng']])
                    
                    parcel_draw_control = {
                        'draw': {
                            'polygon': True,
                            'marker': False,
                            'circle': False,
                            'rectangle': False,
                            'polyline': False,
                            'circlemarker': False,
                        },
                        'edit': False,
                    }
                    p = ui.leaflet(center=(44.5108, 16.4786), zoom=11, options={'attributionControl': 0}, draw_control=parcel_draw_control)
                    p.tile_layer(url_template='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}')
                    p.on('draw:created', handle_parcel_draw)
                    ui.button(lang_list[lg_id]['save'], on_click=lambda: draw_parcel_dialog.submit(geometry))
                
                # Function for editing parcel data
                async def edit_parcel(id:int):
                    edit_parcel_dialog.open()
                    data = await edit_parcel_dialog
                    changed_parcel = {
                        'owner_id': current_user.id,
                        'name': data['name'],
                        'crop_id': data['crop_id'],
                        'date': datetime.now()
                    }
                    db_parcel = session.query(models.Parcel).filter(models.Parcel.id == id)
                    db_parcel.update(changed_parcel, synchronize_session=False)
                    session.commit()
                    get_parcel_dialog.close()
                    ui.notify('Parcel data changed.', position='top', color='positive')
                    await asyncio.sleep(1)
                    ui.navigate.reload()
                async def sow_parcel(id: int):
                    entry = {'sow_complete': True, 'date': datetime.now()}
                    db_parcel = session.query(models.Parcel).filter(models.Parcel.id == id)
                    db_parcel.update(entry, synchronize_session=False)
                    session.commit()
                    ui.notify('Parcel sow completed', position='top', color='positive')
                    await asyncio.sleep(1)
                    ui.navigate.reload()
                # Call on editable dialog
                with ui.dialog() as edit_parcel_dialog, ui.card():
                    ui.label(lang_list[lg_id]['edit_parcel']).classes('w-full font-bold')
                    with ui.row().classes('no-wrap w-full justify-between'):
                        ui.label(lang_list[lg_id]['myparcel_name']).classes('self-center text-xs')
                        parcel_name = ui.input()
                    with ui.row().classes('no-wrap w-full justify-between'):
                        ui.label(lang_list[lg_id]['myparcel_crop']).classes('self-center text-xs')
                        parcel_crop = ui.select(crop_dict).classes('w-1/2')
                    ui.button(lang_list[lg_id]['submit_btn'], 
                            on_click=lambda: edit_parcel_dialog.submit({'name': parcel_name.value, 
                                                                        'crop_id': parcel_crop.value})).classes('w-full')
                
                """ Dialog to review status of parcels """
                with ui.dialog() as get_parcel_dialog, ui.row().classes('no-scroll'), ui.card():
                    columns = [{'name': 'date', 'label': lang_list[lg_id]['myparcel_date'], 'field': 'date', 'align': 'left'},
                                {'name': 'name', 'label': lang_list[lg_id]['myparcel_name'], 'field': 'name', 'align': 'left'},
                                {'name': 'crop_id', 'label': lang_list[lg_id]['myparcel_crop'], 'field': 'crop_id', 'align': 'left'},
                                {'name': 'sow_complete', 'label': lang_list[lg_id]['sow_complete'], 'field': 'sow_complete', 'align': 'left'},
                                {"name": "action", "label": "", "field": "id", "align": "center"}]
                    rows = []
                    for one in current_user.parcels:
                        crop = session.query(models.Crop).filter(models.Crop.id == one.crop_id).first()
                        row = {}
                        row.update({'date': one.date.strftime('%d-%m-%Y %H:%M'), 'name': one.name, 'crop_id': crop.name, 
                                    'sow_complete': one.sow_complete, 'id': one.id})
                        rows.append(row)
                    with ui.table(title=lang_list[lg_id]['parcel_table'], columns=columns, rows=rows, pagination=3).classes(
                                'justify-items-center').classes('w-full bordered') as myparcel_table:
                        with myparcel_table.add_slot('top-right'):
                            with ui.input(placeholder=lang_list[lg_id]['search']).props('type=search').bind_value(myparcel_table, 'filter').add_slot('append'):
                                ui.icon('search')
                        myparcel_table.add_slot(f'body-cell-action', """
                            <q-td :props="props">
                                <q-btn @click="$parent.$emit('sow', props)" icon="done" flat dense color='green'/>
                                <q-btn @click="$parent.$emit('draw', props)" icon="location_on" flat dense color='blue'/>
                                <q-btn @click="$parent.$emit('update', props)" icon="edit" flat dense color='green'/>
                                <q-btn @click="$parent.$emit('del', props)" icon="delete" flat dense color='red'/>
                            </q-td>
                            """)
                        myparcel_table.on('sow', lambda e: sow_parcel(e.args["row"]["id"]))
                        myparcel_table.on('draw', lambda e: draw_parcel(e.args["row"]["id"]))
                        myparcel_table.on('update', lambda e: edit_parcel(e.args["row"]["id"]))
                        myparcel_table.on('del', lambda e: delete_parcel(e.args["row"]["id"]))
                    ui.button(icon='add', on_click=create_parcel_dialog.open).props('round')
                create_parcel_dialog.tooltip(lang_list[lg_id]['add_parcel'])
                
                """ Dialog to add new sensors """
                with ui.dialog() as create_sensor_dialog, ui.card():
                    ui.label(lang_list[lg_id]['add_sensor']).classes('w-full font-bold')
                    with ui.row().classes('no-wrap w-full justify-between'):
                        ui.label(lang_list[lg_id]['mysensor_id']).classes('self-center text-xs')
                        sensor_id = ui.input()
                    with ui.row().classes('no-wrap w-full justify-between'):
                        ui.label(lang_list[lg_id]['mysensor_parcel']).classes('self-center text-xs')
                        parcel_id = ui.select(parcel_dict).classes('w-1/2')
                    ui.button(lang_list[lg_id]['submit_btn'], on_click=create_sensor).classes('w-full')
                
                # Function for drawing sensor
                async def draw_sensor(id:int):
                    draw_sensor_dialog.open()
                    data = await draw_sensor_dialog
                    sensor_geometry = {'type': 'Point', 'coordinates': data[0]}
                    point_geometry = shapely.geometry.shape(sensor_geometry)
                    wkb_geometry = shapely.wkb.dumps(point_geometry, hex=True, srid=4326)
                    sensor = session.query(models.Sensor).filter(models.Sensor.id == id).first()
                    sensor_parcel = session.query(models.Parcel).filter(models.Parcel.id == sensor.parcel_id).first()
                    parcel_coords = []
                    parcel_loc = sensor_parcel.location
                    if parcel_loc:
                        coord = shapely.wkb.loads(bytes(parcel_loc.data), hex=True)
                        parcel_coords.append(coord)
                    try:
                        if parcel_coords[0].contains(point_geometry):
                            entry = {}
                            entry['location'] = wkb_geometry
                            entry['date'] = datetime.now()
                            db_sensor = session.query(models.Sensor).filter(models.Sensor.id == id)
                            db_sensor.update(entry, synchronize_session=False)
                            session.commit()
                            ui.notify('Location created.', position='top', color='positive')
                    except IndexError:
                        ui.notify('Sensor must be placed on correct parcel.', position='top', color='negative')
                    get_sensor_dialog.close()
                    await asyncio.sleep(1)
                    ui.navigate.reload()
                
                # Call on drawable sensor dialog
                with ui.dialog() as draw_sensor_dialog, ui.card().classes('w-[600px] h-[350px]'):
                    sensor_coords = []
                    def handle_sensor_draw(e: events.GenericEventArguments):
                        if e.args['layerType'] == 'marker':
                            s.marker(latlng=(e.args['layer']['_latlng']['lat'],
                                             e.args['layer']['_latlng']['lng']))
                            sensor_point = e.args['layer']['_latlng']
                            sensor_coords.append([sensor_point['lat'], sensor_point['lng']])
                            
                    sensor_draw_control = {
                        'draw': {
                            'polygon': False,
                            'marker': True,
                            'circle': False,
                            'rectangle': False,
                            'polyline': False,
                            'circlemarker': False,
                        },
                        'edit': False,
                    }
                    s = ui.leaflet(center=(44.5108, 16.4786), zoom=11, options={'attributionControl': 0}, draw_control=sensor_draw_control)
                    s.tile_layer(url_template='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}')
                    s.on('draw:created', handle_sensor_draw)
                    ui.button(lang_list[lg_id]['save'], on_click=lambda: draw_sensor_dialog.submit(sensor_coords))
                
                # Function to edit existing sensor
                async def edit_sensor(id:int):
                    edit_sensor_dialog.open()
                    data = await edit_sensor_dialog
                    changed_sensor = {
                        'parcel_id': data['parcel_id'],
                        'date': datetime.now()
                    }
                    db_sensor = session.query(models.Sensor).filter(models.Sensor.id == id)
                    db_sensor.update(changed_sensor, synchronize_session=False)
                    session.commit()
                    get_sensor_dialog.close()
                    ui.notify('Sensor data changed.', position='top', color='positive')
                    await asyncio.sleep(1)
                    ui.navigate.reload()
                
                # Call on editable dialog
                with ui.dialog() as edit_sensor_dialog, ui.card().classes('w-[300px]'):
                    ui.label(lang_list[lg_id]['edit_sensor']).classes('w-full font-bold')
                    with ui.row().classes('no-wrap w-full justify-between'):
                        ui.label(lang_list[lg_id]['mysensor_parcel']).classes('self-center text-xs')
                        sensor_parcel = ui.select(parcel_dict).classes('w-1/2')
                    ui.button(lang_list[lg_id]['submit_btn'], 
                            on_click=lambda: edit_sensor_dialog.submit({'parcel_id': sensor_parcel.value})).classes('w-full')
                
                """ Dialog to review status of sensors """    
                with ui.dialog() as get_sensor_dialog, ui.row().classes('no-scroll'), ui.card():
                    columns = [{'name': 'date', 'label': lang_list[lg_id]['mysensor_date'], 'field': 'date', 'align': 'left'},
                                {'name': 'sensor_id', 'label': lang_list[lg_id]['mysensor_id'], 'field': 'sensor_id', 'align': 'left'},
                                {'name': 'parcel_id', 'label': lang_list[lg_id]['mysensor_parcel'], 'field': 'parcel_id', 'align': 'left'},
                                {"name": "action", "label": "", "field": "id", "align": "center"}]
                    rows = []
                    for device in devices:
                        row = {}
                        row.update({'date': device.date.strftime('%d-%m-%Y %H:%M'), 'sensor_id': device.sensor_id, 
                                    'parcel_id': parcel_dict[device.parcel_id], 'id': device.id})
                        rows.append(row)
                    with ui.table(title=lang_list[lg_id]['sensor_table'], columns=columns, rows=rows, pagination=3).classes(
                                'justify-items-center').classes('w-full bordered') as mysensor_table:
                        with mysensor_table.add_slot('top-right'):
                            with ui.input(placeholder=lang_list[lg_id]['search']).props('type=search').bind_value(mysensor_table, 'filter').add_slot('append'):
                                ui.icon('search')
                        mysensor_table.add_slot(f'body-cell-action', """
                            <q-td :props="props">
                                <q-btn @click="$parent.$emit('draw', props)" icon="location_on" flat dense color='blue'/>
                                <q-btn @click="$parent.$emit('update', props)" icon="edit" flat dense color='green'/>
                                <q-btn @click="$parent.$emit('del', props)" icon="delete" flat dense color='red'/>
                            </q-td>
                            """)
                        mysensor_table.on('draw', lambda e: draw_sensor(e.args["row"]["id"]))
                        mysensor_table.on('update', lambda e: edit_sensor(e.args["row"]["id"]))
                        mysensor_table.on('del', lambda e: delete_sensor(e.args["row"]["id"]))
                    ui.button(icon='add', on_click=create_sensor_dialog.open).props('round')
                
                """ Basic UI buttons """
                with ui.column().classes('h-full justify-between'):
                    with ui.row():
                        with ui.button(icon='notifications', on_click=alert_dialog.open).props('round'):
                            ui.badge(len(active_alerts), color='red').props('floating')
                            ui.tooltip(lang_list[lg_id]['alert'])
                        with ui.button(icon='perm_identity', on_click=profile_dialog.open).props('round'):
                            ui.tooltip(lang_list[lg_id]['profile'])
                    with ui.column().classes('p-3 absolute bottom-0 right-0'):
                        with ui.button(icon='map', on_click=get_parcel_dialog.open).props('round'):
                            ui.tooltip(lang_list[lg_id]['parcel'])
                        with ui.button(icon='sensors',on_click=get_sensor_dialog.open).props('round'):
                            ui.tooltip(lang_list[lg_id]['sensor'])
            
    if current_user.is_admin:
        with admin_frame():
            async def delete_user(id:int):
                db_user = session.query(models.User).filter(models.User.id == id)
                db_user.delete(synchronize_session=False)
                session.commit()
                ui.notify('User deleted.', position='top', color='negative')
                await asyncio.sleep(1)
                ui.navigate.reload()
            async def create_user():
                db_user = models.User(email=email.value, hashed_password=config.get_password_hash(password.value), phone=phone.value, 
                                      is_admin=False, email_alert=False, sms_alert=False)
                session.add(db_user)
                session.commit()
                create_user_dialog.close()
                ui.notify('User created.', position='top', color='positive')
                await asyncio.sleep(1)
                ui.navigate.reload()
            async def update_user(id: int):
                edit_user_dialog.open()
                data = await edit_user_dialog
                entry= {}
                entry['is_admin'] = data
                entry['date'] = datetime.now()
                db_user = session.query(models.User).filter(models.User.id == id)
                db_user.update(entry, synchronize_session=False)
                session.commit()
                edit_user_dialog.close()
                ui.notify('User rights changed.', position='top', color='positive')
                await asyncio.sleep(1)
                ui.navigate.reload()
            def change_admin_password():
                admin_entry = {}
                test_admin_password = config.verify_password(old_admin_password.value, user.hashed_password)
                if not test_admin_password:
                    ui.notify('Wrong password', position='top', color='negative')
                elif new_admin_password.value != retyped_pwd.value:
                    ui.notify('Both passwords must match each other!', position='top', color='negative')
                else:
                    admin_entry['hashed_password'] = config.get_password_hash(password=new_admin_password.value)
                    admin_entry['date'] = datetime.now()
                    db_user.update(admin_entry, synchronize_session=False)
                    session.commit()
                    ui.notify('Password changed.', position='top', color='positive')
                admin_dialog.close()
            
            with ui.dialog() as admin_dialog, ui.row(), ui.card().classes('mx-auto'):
                with ui.row().classes('w-full no-wrap'):
                    with ui.column().classes('w-full gap-0'):
                        ui.label(lang_list[lg_id]['password_label']).classes('font-bold')
                        old_admin_password = ui.input(placeholder=lang_list[lg_id]['old_password'], password=True, password_toggle_button=True).props('rounded-lg outlined dense').classes('text-xs mb-1').on('keydown.enter', change_password)
                        new_admin_password = ui.input(placeholder=lang_list[lg_id]['new_password'], password=True, password_toggle_button=True).props('rounded-lg outlined dense').classes('text-xs mb-1')
                        retyped_pwd = ui.input(placeholder=lang_list[lg_id]['retype'], password=True, password_toggle_button=True).props('rounded-lg outlined dense').classes('text-xs mb-3').on('keydown.enter', change_password)
                        ui.button(lang_list[lg_id]['submit_btn'], on_click=change_admin_password).classes('w-full')
                
            with ui.dialog().props('persistent') as edit_user_dialog, ui.card():
                ui.label(lang_list[lg_id]['edit_user']).classes('w-full font-bold')
                with ui.row():
                    ui.button(lang_list[lg_id]['turn_admin'], on_click=lambda: edit_user_dialog.submit(True))
                    ui.button(lang_list[lg_id]['keep_user'], color='secondary', on_click=lambda: edit_user_dialog.submit(False))
                
            with ui.dialog() as create_user_dialog, ui.card():
                    ui.label(lang_list[lg_id]['add_user']).classes('w-full font-bold')
                    with ui.row().classes('no-wrap w-full justify-between'):
                        ui.label(lang_list[lg_id]['user']).classes('self-center text-xs')
                        email = ui.input()
                    with ui.row().classes('no-wrap w-full justify-between'):
                        ui.label(lang_list[lg_id]['password']).classes('self-center text-xs')
                        password = ui.input()
                    with ui.row().classes('no-wrap w-full justify-between'):
                        ui.label(lang_list[lg_id]['phone']).classes('self-center text-xs')
                        phone = ui.number()
                    ui.button(lang_list[lg_id]['submit_btn'], on_click=create_user).classes('w-full')
            
            columns = [{'name': 'date', 'label': lang_list[lg_id]['myparcel_date'], 'field': 'date', 'align': 'left'},
                        {'name': 'email', 'label': lang_list[lg_id]['user'], 'field': 'email', 'align': 'left'},
                        {'name': 'is_admin', 'label': lang_list[lg_id]['admin'], 'field': 'is_admin', 'align': 'left'},
                        {"name": "action", "label": "", "field": "id", "align": "center"}]
            rows = []
            users = session.query(models.User).all()
            for user in users:
                values = {}
                values.update({'date': user.date.strftime('%d-%m-%Y %H:%M'), 'email': user.email, 'is_admin': user.is_admin, 'id': user.id})
                rows.append(values)
            with ui.table(title=lang_list[lg_id]['user_table'], columns=columns, rows=rows, pagination=5).classes(
                    'justify-items-center').classes('w-full bordered') as user_table:
                with user_table.add_slot('top-right'):
                    with ui.input(placeholder=lang_list[lg_id]['search']).props('type=search').bind_value(user_table, 'filter').add_slot('append'):
                        ui.icon('search')
            user_table.add_slot(f'body-cell-action', """
                            <q-td :props="props">
                                <q-btn @click="$parent.$emit('update', props)" icon="edit" flat dense color='green'/>
                                <q-btn @click="$parent.$emit('del', props)" icon="delete" flat dense color='red'/>
                            </q-td>
                            """)
            user_table.on('update', lambda e: update_user(e.args["row"]["id"]))
            user_table.on('del', lambda e: delete_user(e.args["row"]["id"]))
            with ui.row():
                ui.button(icon='add', on_click=create_user_dialog.open).props('round')
                ui.button(icon='settings', on_click=admin_dialog.open).props('round')

@router.page('/fig/{id}')
def fig(id: int):
    with user_frame():
        ui.label(id)         
        
@router.page('/alerts')    
def admin_alerts(session: Session= Depends(config.get_session)) -> None:
    current_user = session.query(models.User).filter(models.User.email == app.storage.user["username"]).first()
    if current_user.is_admin:
        with admin_frame():
            user_dict = {}
            parcel_dict = {}
            lg_id = app.storage.user['lang']
            users = session.query(models.User).all()
            for user in users:
                user_dict.update({user.id: user.email})
            parcels = session.query(models.Parcel).all()
            for parcel in parcels:
                parcel_dict.update({parcel.id: parcel.name})

            async def delete_alert(id: int):
                db_alert = session.query(models.Alert).filter(models.Alert.id == id)
                db_alert.delete(synchronize_session=False)
                session.commit()
                ui.notify('Alert deleted.', position='top', color='negative')
                await asyncio.sleep(1)
                ui.navigate.reload()

            columns = [{'name': 'date', 'label': lang_list[lg_id]['alert_date'], 'field': 'date', 'align': 'left'},
                        {'name': 'email', 'label': lang_list[lg_id]['user'], 'field': 'email', 'align': 'left'},
                        {'name': 'parcel_id', 'label': lang_list[lg_id]['myparcel_name'], 'field': 'parcel_id', 'align': 'left'},
                        {'name': 'text', 'label': lang_list[lg_id]['alert_msg'], 'field': 'text', 'align': 'left'},
                        {'name': 'is_active', 'label': lang_list[lg_id]['active'], 'field': 'is_active', 'align': 'left'},
                        {"name": "action", "label": "", "field": "id", "align": "center"}]
            rows = []
            alerts = session.query(models.Alert).all()
            for alert in alerts:
                owner = session.query(models.Parcel).filter(models.Parcel.id == alert.parcel_id).first()
                values = {}
                values.update({'date': alert.date.strftime('%d-%m-%Y %H:%M'), 'email': user_dict[owner.owner_id], 
                               'parcel_id': parcel_dict[alert.parcel_id],'text': alert.text ,'is_active': alert.is_active, 'id': alert.id})
                rows.append(values)
            with ui.table(title=lang_list[lg_id]['alert_table'], columns=columns, rows=rows, pagination=5).classes(
                            'justify-items-center').classes('w-full bordered') as alert_table:
                with alert_table.add_slot('top-right'):
                    with ui.input(placeholder=lang_list[lg_id]['search']).props('type=search').bind_value(alert_table, 'filter').add_slot('append'):
                        ui.icon('search')
            alert_table.add_slot(f'body-cell-action', """
                            <q-td :props="props">
                                <q-btn @click="$parent.$emit('del', props)" icon="delete" flat dense color='red'/>
                            </q-td>
                            """)
            alert_table.on('del', lambda e: delete_alert(e.args["row"]["id"]))
    
@router.page('/crops')
def admin_crops(session: Session= Depends(config.get_session)) -> None:
    current_user = session.query(models.User).filter(models.User.email == app.storage.user["username"]).first()
    if current_user.is_admin:
        with admin_frame():
            lg_id = app.storage.user['lang']
            async def edit_crop(id: int):
                crop_dialog.open()
                entry = await crop_dialog
                filled_entry = {}
                for k,v in entry.items():
                    if v:
                        filled_entry.update({k:v})
                filled_entry['date'] = datetime.now()
                db_crop = session.query(models.Crop).filter(models.Crop.id == id)
                db_crop.update(filled_entry, synchronize_session=False)
                session.commit()
                ui.notify('Crop updated.', position='top', color='positive')
                await asyncio.sleep(1)
                ui.navigate.reload()
                
            async def delete_crop(id: int):
                db_crop = session.query(models.Crop).filter(models.Crop.id == id)
                db_crop.delete(synchronize_session=False)
                session.commit()
                ui.notify('Crop deleted.', position='top', color='negative')
                await asyncio.sleep(1)
                ui.navigate.reload()
            async def create_crop():
                db_crop = models.Crop(name=add_name.value, temp_min=add_t_min.value, temp_max=add_t_max.value, moist_min=add_m_min.value,
                                      moist_max=add_m_max.value, altitude=add_altitude.value, variety=add_variety.value, clima=add_clima.value,
                                      distance=add_distance.value, density=add_density.value, depth=add_depth.value, norm=add_norm.value,
                                      method=add_method.value, min_temp=add_min_temp.value, fertilization=add_fertilization.value, watering=add_watering.value,
                                      care=add_care.value, protection=add_protection.value, utilization=add_utilization.value, harvest=add_harvest.value,
                                      storage=add_storage.value, season_start=add_season_start.value, season_end=add_season_end.value, rain=add_rain.value,
                                      crop_yield=add_crop_yield.value)
                session.add(db_crop)
                session.commit()
                create_crop_dialog.close()
                ui.notify('New crop added', position='top', color='positive')
                await asyncio.sleep(1)
                ui.navigate.reload()
                
            with ui.dialog() as crop_dialog, ui.card():
                with ui.column().classes('no-gap'):
                    ui.label(lang_list[lg_id]['edit_crop']).classes('font-bold self-center')
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['crop_name'])
                            edit_name = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['t_min'])
                            edit_t_min = ui.number()
                        with ui.row():
                            ui.label(lang_list[lg_id]['t_max'])
                            edit_t_max = ui.number()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['m_min'])
                            edit_m_min = ui.number()
                        with ui.row():
                            ui.label(lang_list[lg_id]['m_max'])
                            edit_m_max = ui.number()
                        with ui.row():
                            ui.label(lang_list[lg_id]['altitude'])
                            edit_altitude = ui.input()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['variety'])
                            edit_variety= ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['clima'])
                            edit_clima = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['distance'])
                            edit_distance = ui.input()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['density'])
                            edit_density= ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['depth'])
                            edit_depth = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['norm'])
                            edit_norm = ui.input()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['method'])
                            edit_method= ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['min_temp'])
                            edit_min_temp = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['fertilization'])
                            edit_fertilization = ui.input()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['watering'])
                            edit_watering= ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['care'])
                            edit_care = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['protection'])
                            edit_protection = ui.input()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['utilization'])
                            edit_utilization= ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['harvest'])
                            edit_harvest = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['storage'])
                            edit_storage = ui.input()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['crop_yield'])
                            edit_crop_yield = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['rain'])
                            edit_rain = ui.number(min=1, max=3).classes('w-full')
                    with ui.row().classes('no-wrap'):
                        with ui.input(lang_list[lg_id]['season_start']) as edit_season_start:
                            with ui.menu().props('no-parent-event') as start_edit_menu:
                                with ui.date().bind_value(edit_season_start):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=start_edit_menu.close).props('flat')
                            with edit_season_start.add_slot('append'):
                                ui.icon('edit_calendar').on('click', start_edit_menu.open).classes('cursor-pointer')
                        with ui.input(lang_list[lg_id]['season_end']) as (edit_season_end):
                            with ui.menu().props('no-parent-event') as end_edit_menu:
                                with ui.date().bind_value(edit_season_end):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=end_edit_menu.close).props('flat')
                            with edit_season_end.add_slot('append'):
                                ui.icon('edit_calendar').on('click', end_edit_menu.open).classes('cursor-pointer')
                    
                    ui.button(lang_list[lg_id]['edit_crop'], on_click=lambda: crop_dialog.submit(
                        {'name': edit_name.value, 'temp_min': edit_t_min.value, 'temp_max': edit_t_max.value, 'moist_min': edit_m_min.value,
                            'moist_max': edit_m_max.value, 'altitude': edit_altitude.value, 'variety': edit_variety.value, 'clima': edit_clima.value,
                            'distance': edit_distance.value, 'density':edit_density.value, 'depth': edit_depth.value, 'norm': edit_norm.value,
                            'method': edit_method.value, 'min_temp':edit_min_temp.value, 'fertilization':edit_fertilization.value, 'watering':edit_watering.value,
                            'care':edit_care.value, 'protection':edit_protection.value, 'utilization': edit_utilization.value, 'harvest':edit_harvest.value,
                            'storage':edit_storage.value, 'season_start':edit_season_start.value, 'season_end': edit_season_end.value, 
                            'crop_yield': edit_crop_yield.value, 'rain': edit_rain.value}
                        )).classes('w-full')
            
            with ui.dialog() as create_crop_dialog, ui.card():
                with ui.column().classes('no-gap'):
                    ui.label(lang_list[lg_id]['add_crop']).classes('font-bold self-center')
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['crop_name'])
                            add_name = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['t_min'])
                            add_t_min = ui.number()
                        with ui.row():
                            ui.label(lang_list[lg_id]['t_max'])
                            add_t_max = ui.number()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['m_min'])
                            add_m_min = ui.number()
                        with ui.row():
                            ui.label(lang_list[lg_id]['m_max'])
                            add_m_max = ui.number()
                        with ui.row():
                            ui.label(lang_list[lg_id]['altitude'])
                            add_altitude = ui.input()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['variety'])
                            add_variety= ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['clima'])
                            add_clima = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['distance'])
                            add_distance = ui.input()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['density'])
                            add_density= ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['depth'])
                            add_depth = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['norm'])
                            add_norm = ui.input()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['method'])
                            add_method= ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['min_temp'])
                            add_min_temp = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['fertilization'])
                            add_fertilization = ui.input()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['watering'])
                            add_watering= ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['care'])
                            add_care = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['protection'])
                            add_protection = ui.input()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['utilization'])
                            add_utilization= ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['harvest'])
                            add_harvest = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['storage'])
                            add_storage = ui.input()
                    with ui.row().classes('no-wrap'):
                        with ui.row():
                            ui.label(lang_list[lg_id]['crop_yield'])
                            add_crop_yield = ui.input()
                        with ui.row():
                            ui.label(lang_list[lg_id]['rain'])
                            add_rain = ui.number(min=1, max=3).classes('w-full')
                    with ui.row().classes('no-wrap'):
                        with ui.input(lang_list[lg_id]['season_start']) as add_season_start:
                            with ui.menu().props('no-parent-event') as start_menu:
                                with ui.date().bind_value(add_season_start):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=start_menu.close).props('flat')
                            with add_season_start.add_slot('append'):
                                ui.icon('edit_calendar').on('click', start_menu.open).classes('cursor-pointer')
                        with ui.input(lang_list[lg_id]['season_end']) as add_season_end:
                            with ui.menu().props('no-parent-event') as end_menu:
                                with ui.date().bind_value(add_season_end):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=end_menu.close).props('flat')
                            with add_season_end.add_slot('append'):
                                ui.icon('edit_calendar').on('click', end_menu.open).classes('cursor-pointer')
                    ui.button(lang_list[lg_id]['add_crop'], on_click=create_crop).classes('w-full')
                            
            
            columns = [{'name': 'date', 'label': lang_list[lg_id]['myparcel_date'], 'field': 'date', 'align': 'left'},
                        {'name': 'name', 'label': lang_list[lg_id]['myparcel_crop'], 'field': 'name', 'align': 'left'},
                        {'name': 'temp_min', 'label': lang_list[lg_id]['t_min'], 'field': 'temp_min', 'align': 'left'},
                        {'name': 'temp_max', 'label': lang_list[lg_id]['t_max'], 'field': 'temp_max', 'align': 'left'},
                        {'name': 'moist_min', 'label': lang_list[lg_id]['m_min'], 'field': 'moist_min', 'align': 'left'},
                        {'name': 'moist_max', 'label': lang_list[lg_id]['m_max'], 'field': 'moist_max', 'align': 'left'},
                        {'name': 'season_start', 'label': lang_list[lg_id]['season_start'], 'field': 'season_start', 'align': 'left'},
                        {'name': 'season_end', 'label': lang_list[lg_id]['season_end'], 'field': 'season_end', 'align': 'left'},
                        {"name": "action", "label": "", "field": "id", "align": "center"}]
            rows = []
            crops = session.query(models.Crop).all()
            for crop in crops:
                values = {}
                values.update({'date': crop.date.strftime('%d-%m-%Y %H:%M'), 'name': crop.name, 'temp_min': crop.temp_min,
                               'temp_max': crop.temp_max,'moist_min': crop.moist_min ,'moist_max': crop.moist_max,
                               'season_start': crop.season_start.strftime('%d-%m-%Y'), 'season_end': crop.season_end.strftime('%d-%m-%Y'), 'id': crop.id})
                rows.append(values)
            with ui.table(title=lang_list[lg_id]['crop_table'], columns=columns, rows=rows, pagination=5).classes(
                            'justify-items-center').classes('w-full bordered') as crop_table:
                with crop_table.add_slot('top-right'):
                    with ui.input(placeholder=lang_list[lg_id]['search']).props('type=search').bind_value(crop_table, 'filter').add_slot('append'):
                        ui.icon('search')
            crop_table.add_slot(f'body-cell-action', """
                            <q-td :props="props">
                                <q-btn @click="$parent.$emit('update', props)" icon="edit" flat dense color='green'/>
                                <q-btn @click="$parent.$emit('del', props)" icon="delete" flat dense color='red'/>
                            </q-td>
                            """)
            crop_table.on('update', lambda e: edit_crop(e.args["row"]["id"]))
            crop_table.on('del', lambda e: delete_crop(e.args["row"]["id"]))
            ui.button(icon='add', on_click=create_crop_dialog.open).props('round')

@router.page('/map')
def admin_map(session: Session= Depends(config.get_session)) -> None:
    current_user = session.query(models.User).filter(models.User.email == app.storage.user["username"]).first()
    if current_user.is_admin:
        parcels = session.query(models.Parcel).all()
        sensors = session.query(models.Sensor).all()
        all_parcels = []
        all_sensors = []
        for parcel in parcels:
            p = parcel.location
            if p:
                existing_parcels = shapely.wkb.loads(bytes(p.data), hex=True)
                all_parcels.append({'location':existing_parcels, 'name': parcel.name})
        for sensor in sensors:
            s = sensor.location
            if s:
                existing_sensors = shapely.wkb.loads(bytes(s.data), hex=True)
                all_sensors.append({'location':existing_sensors, 'name': sensor.sensor_id})
        with admin_frame():
            map = folium.Map(location=(44.5108, 16.4786), zoom_start=13, attributionControl=0)
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                attr='Google',
                name='Google Satellite',
                overlay=False,
                control=True
                ).add_to(map)
            for x in all_parcels:
                folium.Polygon(
                    locations=list(x['location'].exterior.coords),
                    tooltip=x['name']
                    ).add_to(map)
            for y in all_sensors:
                folium.Marker(
                    location=[y['location'].x, y['location'].y],
                    popup= y['name']
                ).add_to(map)
            ui.html(map.get_root()._repr_html_()).classes('w-full absolute-center items-center')