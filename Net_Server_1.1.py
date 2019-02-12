import asyncio
import websockets
import json as jsn
import time as tm
import configparser #подключаем библиотеку для чтения файла конфигурации формата properties ( структура файла INI)
import traceback
import logging as lg
import logging.handlers as handlers

########################################################
# Read configuration parameters for web  socket server #
########################################################
config = configparser.ConfigParser()
config.read('config.properties')
v_params = config['config.vega']
h_params = config['websocket.server']
f_params = config['websocket.logs']
factory = config['config.factory']

########################################################
# Prepare logging                                      #
########################################################
logger = lg.getLogger('NetWork server for GF')
logger.setLevel(lg.INFO)

formatter = lg.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

loghandler = handlers.RotatingFileHandler('trace.log', maxBytes=20000000, backupCount=10)
loghandler.setFormatter(formatter)

errorhandler = handlers.RotatingFileHandler('error.log', maxBytes=20000000, backupCount=10)
errorhandler.setLevel(lg.ERROR)
errorhandler.setFormatter(formatter)

logger.addHandler(loghandler)
logger.addHandler(errorhandler)


def get_temp_tp_11(data):
    ma = [4, 20]
    temp = [-50, 150]
    value_tp = bytes.fromhex(data[12:16])
    value_tp = int.from_bytes(value_tp, byteorder='little', signed=True)
    d = value_tp / 100
    t_tp = round((d - ma[0]) / (ma[1] - ma[0]) * (temp[1] - temp[0]) - 50, 2)
    return t_tp

def get_battery_tp_11(data): #расчет заряда батареи на устройстве ТП-11
    return int((data[2:4]), 16)

def get_temp_td_11(data):
    value_td = bytes.fromhex(data[6:10])
    value_td = int.from_bytes(value_td, byteorder='little', signed=True)
    t_td = value_td / 10
    return t_td

def get_battery_td_11(data): #расчет заряда батареи на устройстве ТД-11
    return int((data[2:4]), 16)

def calcterm(a_val):
    return_val = {
        "GF": get_temp_tp_11(a_val),
        "ZapSib": get_temp_td_11(a_val)
    }
    return return_val[factory['plant']]

def calcbattery(a_val):  #функция выбора метода по расчету заряда батареи
    get_val = {
        "GF": get_battery_tp_11(a_val),
        "ZapSib": get_battery_td_11(a_val)
    }
    return get_val[factory['plant']]

async def get_devices(ws):
    await ws.send('{"cmd":"get_device_appdata_req"}')
    async for mess in ws:
        json_mess = jsn.loads(mess)
        if json_mess['cmd'] == 'get_device_appdata_resp':
            devices_list = json_mess['devices_list']
            sensor = {'cmd': 'get_devices', 'data': {
                'sensors': [{"devEui": item['devEui'], "description": item['devName']} for item in devices_list]}}
            js_str = jsn.dumps(sensor)
            return js_str


async def get_device_data(devEuiArr, ws):#обновляемая информация, запрашиваемая с сетевого сервера
    cli_str = '{"cmd":"get_data_req", "devEui":"%s", "select": {"limit": 1}}'
    # seconds = 43200  # 12 hours
    # from_date = tm.time() - seconds  # current time point minus 12 hours
    devEui_list = devEuiArr
    cmd_dict = {item: cli_str % (item) for item in devEui_list}
    res_list = []
    if len(devEui_list) == 0:
        return jsn.dumps({"cmd": "get_device_data", "data": res_list})
    for devEui, cmd in cmd_dict.items():
        await ws.send(cmd)
    async for mess in ws:
        json_mess = jsn.loads(mess)
        if json_mess['cmd'] == 'get_data_resp' and len(json_mess['data_list']) != 0:
            data = json_mess['data_list'][0]['data']
            ts = json_mess['data_list'][0]['ts']
            temp = calcterm(data)
            batt = calcbattery(data)
            res_list.append({"devEui": json_mess['devEui'], "temperature": temp, "timestamp": ts, "battery": batt})
            if len(res_list) == len(devEui_list):
                break
    return jsn.dumps({"cmd": "get_device_data", "data": res_list})


async def get_device_history(dev_eui, ts, ws):
    cli_str = '{"cmd":"get_data_req", "devEui":"%s", "select": {"date_from": %d}}'
    devEui_list = dev_eui
    date_from = ts
    result = []
    if len(devEui_list) == 0:
        return jsn.dumps({"cmd": "get_device_history", "data": result})
    for dev_eui in devEui_list:
        cmd = cli_str % (dev_eui, date_from)
        await ws.send(cmd)
    async for mess in ws:
        json_mess = jsn.loads(mess)
        if json_mess['cmd'] == 'get_data_resp':
            obj = {"devEui": json_mess['devEui'], "history": [{'utc_timestamp': item['ts'],
                                                               'temperature': calcterm(item['data'])}
                                                              for item in json_mess['data_list']]}
            result.append(obj)
            if len(result) == len(devEui_list):
                break
    return jsn.dumps({"cmd": "get_device_history", "data": result})


async def get_device_history1(dev_eui, ts, ws):
    cli_str = '{"cmd":"get_data_req", "devEui":"%s", "select": {"date_from": %d}}'
    devEui_list = dev_eui
    date_from = ts
    result = []
    for dev_eui in devEui_list:
        cmd = cli_str % (dev_eui, date_from)
        await ws.send(cmd)
        while True:
            mess = await ws.recv()
            json_mess = jsn.loads(mess)
            if json_mess['cmd'] == 'get_data_resp ':
                obj = {"devEui": json_mess['devEui'], "history": [{'utc_timestamp': item['ts'],
                                                                   'temperature': calcterm(item['data'])}
                                                                  for item in json_mess['data_list']]}
                result.append(obj)
                break
    return jsn.dumps({"cmd": "get_device_history", "data": result})


async def producer(message, params):
    async with websockets.connect(params['ws_path']) as ws:
        auth_cmd = '{"cmd":"auth_req", "login":"%s", "password":"%s"}' % (params['login'], params['pass'])
        await ws.send(auth_cmd)
        try:
            json_object = jsn.loads(message)
            func_name = json_object['cmd']
            if func_name == 'get_devices':
                return await get_devices(ws)
            elif func_name == 'get_device_data':
                return await get_device_data(json_object['devEui'], ws)
            elif func_name == 'get_device_history':
                return await get_device_history(json_object['devEui'], json_object['utc_timestamp'], ws)
            else:
                return "Bad function name"
        except Exception as ex:
            logger.error(ex)
            traceback.print_exc()
            return 'Bad message format'


async def echo(ws, path):
    logger.info('Start back-end server')
    async for message in ws:
        logger.info('Incoming message <======' + message)
        prod_mess = await producer(message, v_params)
        logger.info('Outgoing message =======>' + prod_mess)
        await ws.send(prod_mess)


start_server = websockets.serve(echo, h_params['host'], h_params['port'])
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()