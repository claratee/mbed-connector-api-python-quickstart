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
from mbed_cloud.devices import DeviceAPI
import pybars              # use to fill in handlebar templates
import threading

BLINK_PATTERN_RESOURCE_PATH = "/3201/0/5853"
BUTTON_RESOURCE_PATH = "/3200/0/5501"

app = Flask(__name__)
socket = SocketIO(app, async_mode='threading', logger=True, engineio_logger=True)
api = DeviceAPI()

@app.route('/')
def index():
    devices = []
    for device, idx in api.list_connected_devices().iteritems():
        print("Device Found: {}".format(device.id))
        value = api.get_resource_value(device.id, BLINK_PATTERN_RESOURCE_PATH)
        devices.append({
            'id': device.id,
            'blinkPattern': value
        })

    # Fill out html using handlebar template
    comp = pybars.Compiler()
    with open("./views/index.hbs", 'r') as fh:
        source = unicode(fh.read())
        template = comp.compile(source)
        return "".join(template({'devices': devices}))

@socket.on('connect')
def connect():
    print('connect ')
    join_room('room')

@socket.on('disconnect')
def disconnect():
    print('Disconnect')
    leave_room('room')

@socket.on('subscribe_to_presses')
def subscribeToPresses(data):
    # Subscribe to all changes of resource /3200/0/5501 (button presses)
    print('subscribe_to_presses: ', data)

    # Note this is misspelled
    device_id = data['endpointName']
    eq = api.add_subscription(device_id, BUTTON_RESOURCE_PATH)

    # Get current value
    current_value = api.get_resource_value(device_id, BUTTON_RESOURCE_PATH)

    # Start background thread
    t = threading.Thread(target=subscription_handler, args=[current_value, device_id, eq])
    t.daemon = True
    t.start()

    print("Subscribed Successfully!")
    emit('subscribed-to-presses')


@socket.on('unsubscribe_to_presses')
def unsubscribeToPresses(data):
    print('unsubscribe_to_presses: ', data)
    api.delete_subscription(data['endpointName'], BUTTON_RESOURCE_PATH)
    print("Unsubscribed Successfully!")
    emit('unsubscribed-to-presses', {"endpointName": data['endpointName'], "value": 'True'})


@socket.on('get_presses')
def getPresses(data):
    # Read data from GET resource /3200/0/5501 (num button presses)
    print("get_presses ", data)
    value = api.get_resource_value(data['endpointName'], BUTTON_RESOURCE_PATH)

    emit('presses', {
        "endpointName": data['endpointName'],
        "value": value
    })

@socket.on('update_blink_pattern')
def updateBlinkPattern(data):
    # Set data on PUT resource /3201/0/5853 (pattern of LED blink)
    print('update_blink_pattern ', data)
    api.set_resource_value(data['endpointName'], BLINK_PATTERN_RESOURCE_PATH, data['blinkPattern'])

@socket.on('blink')
def blink(data):
    # POST to resource /3201/0/5850 (start blinking LED)
    print('blink: ', data)
    api.set_resource_value(data['endpointName'], BLINK_PATTERN_RESOURCE_PATH, None)

def subscription_handler(current_value, device_id, q):
    while True:
        new_value = q.get()
        if new_value != current_value:
            print("Emitting new value: %s" % new_value)
            socket.emit('presses', {
                'endpointName': device_id,
                'value': new_value
            })
            current_value = new_value

if __name__ == "__main__":
    api.start_long_polling()
    socket.run(app, host='127.0.0.1', port=8002)
