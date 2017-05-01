# Copyright ARM Limited 2017
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from flask import Flask    # framework for hosting webpages
from flask_socketio import emit
from flask_socketio import join_room
from flask_socketio import leave_room
from flask_socketio import SocketIO
import logging
from mbed_cloud.connect import ConnectAPI

import os
import pybars              # use to fill in handlebar templates
import six
import sys
import threading

BLINK_PATTERN_RESOURCE_PATH = "/3201/0/5853"
BLINK_RESOURCE_PATH = "/3201/0/5850"
BUTTON_RESOURCE_PATH = "/3200/0/5501"

# Use 'threading' async_mode, as we don't use greenlet threads for background threads
# in SDK - and thus we can't use eventlet or gevent.
async_mode = 'threading'

# API key from https://portal.mbedcloud.com/. Can also be set by setting the value
# with ACCESS_KEY environment variable.
api_key = ""

app = Flask(__name__)
socket = SocketIO(app, async_mode=async_mode, logger=True, engineio_logger=True)
#api = DeviceAPI({"api_key": os.environ.get("ACCESS_KEY", api_key)})
api = ConnectAPI({"api_key": os.environ.get("ACCESS_KEY", api_key)})
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

@app.route('/')
def index():
    devices = []
    for device, idx in api.list_connected_devices():
        logging.info("Device Found: {}".format(device.id))
        value = api.get_resource_value(device.id, BLINK_PATTERN_RESOURCE_PATH)
        devices.append({
            'id': device.id,
            'blink_pattern': value.decode('utf-8')
        })

    # Fill out html using handlebar template
    comp = pybars.Compiler()
    with open("./views/index.hbs", 'r') as fh:
        template = comp.compile(six.u(fh.read()))
        return "".join(template({'devices': devices}))

@socket.on('connect')
def connect():
    logging.info('connect ')
    join_room('room')

@socket.on('disconnect')
def disconnect():
    logging.info('Disconnect')
    leave_room('room')

@socket.on('subscribe_to_presses')
def subscribe_to_presses(data):
    # Subscribe to all changes of resource /3200/0/5501 (button presses)
    logging.info('subscribe_to_presses: ', data)

    device_id = data['device_id']
    eq = api.add_subscription(device_id, BUTTON_RESOURCE_PATH)

    # Get current value
    current_value = api.get_resource_value(device_id, BUTTON_RESOURCE_PATH)

    # Start background thread
    t = threading.Thread(target=subscription_handler, args=[current_value, device_id, eq])
    t.daemon = True
    t.start()

    logging.info("Subscribed Successfully!")
    emit('presses', {
        'device_id': device_id,
        'value': current_value.decode('utf-8')
    })

@socket.on('unsubscribe_to_presses')
def unsubscribe_to_presses(data):
    logging.info('unsubscribe_to_presses: ', data)

    device_id = data["device_id"]
    api.delete_subscription(device_id, BUTTON_RESOURCE_PATH)
    logging.info("Unsubscribed Successfully!")

    emit('unsubscribed-to-presses', {
        "device_id": device_id,
        "value": 'True'
    })

@socket.on('get_presses')
def get_presses(data):
    # Read data from GET resource /3200/0/5501 (num button presses)
    logging.info("get_presses ", data)
    value = api.get_resource_value(data['device_id'], BUTTON_RESOURCE_PATH)

    emit('presses', {
        "device_id": data['device_id'],
        "value": value.decode('utf-8')
    })

@socket.on('update_blink_pattern')
def update_blink_pattern(data):
    # Set data on PUT resource /3201/0/5853 (pattern of LED blink)
    logging.info('update_blink_pattern ', data)
    api.set_resource_value(data['device_id'], BLINK_PATTERN_RESOURCE_PATH, data['blink_pattern'])

@socket.on('blink')
def blink(data):
    # POST to resource /3201/0/5850 (start blinking LED)
    logging.info('blink: ', data)
    api.set_resource_value(data['device_id'], BLINK_RESOURCE_PATH, None)

def subscription_handler(current_value, device_id, q):
    while True:
        new_value = q.get()
        if new_value != current_value:
            logging.info("Emitting new value: %s" % new_value)
            socket.emit('presses', {
                'device_id': device_id,
                'value': new_value.decode('utf-8')
            })
            current_value = new_value

if __name__ == "__main__":
    api.start_notifications()
    socket.run(app, host='127.0.0.1', port=8002)
