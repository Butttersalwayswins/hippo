import asyncio
import websockets
import json
import time
import datetime
import traceback
import argparse
import _thread

import robot_util
import serial_interface as interface

# Global control websocket
currentWebsocket = {'control': None}
lastPongTime = {'control': datetime.datetime.now()}

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--robot-id", required=True)
parser.add_argument("--stream-key", required=True)
parser.add_argument("--serial-port", required=True)
parser.add_argument("--baudrate", type=int, default=9600)
parser.add_argument("--secure-cert", action="store_true")
commandArgs = parser.parse_args()

# Initialize serial port
interface.init(port=commandArgs.serial_port, baudrate=commandArgs.baudrate)

def getControlHost():
    apiHost = "https://api.robotstreamer.com"

    url = apiHost + '/v1/get_service/rscontrol'
    response = robot_util.getNoRetry(url, secure=commandArgs.secure_cert)
    response = json.loads(response)
    print("response:", response)

    if response is not None:
        response['protocol'] = 'wss'
        print("get_service response:", response)

    if response is None:
        url = apiHost + '/v1/get_endpoint/rscontrol_robot/' + commandArgs.robot_id
        response = robot_util.getNoRetry(url, secure=commandArgs.secure_cert)
        response = json.loads(response)

        if response is not None:
            response['protocol'] = 'ws'
            print("get_endpoint response:", response)

    return response

async def handleControlMessages():
    h = getControlHost()
    url = '%s://%s:%s/echo' % (h['protocol'], h['host'], h['port'])
    print("CONTROL url:", url)

    async with websockets.connect(url) as websocket:
        print("CONTROL: control websocket object:", websocket)

        if h['protocol'] == 'wss':
            await websocket.send(json.dumps({
                "type": "robot_connect",
                "robot_id": commandArgs.robot_id,
                "stream_key": commandArgs.stream_key
            }))
        else:
            await websocket.send(json.dumps({"command": commandArgs.stream_key}))

        currentWebsocket['control'] = websocket

        while True:
            print("CONTROL: awaiting control message")
            message = await websocket.recv()
            j = json.loads(message)
            print("CONTROL message: ", j)

            if j.get('command') == "RS_PONG":
                lastPongTime['control'] = datetime.datetime.now()

            if j.get('type') == "RS_PING":
                lastPongTime['control'] = datetime.datetime.now()

            elif j.get('command') and j.get('key_position'):
                _thread.start_new_thread(interface.handleCommand, (
                    j["command"],
                    j["key_position"],
                    j.get('command_price', 0)
                ))

def startControl():
    print("CONTROL: waiting a few seconds")
    time.sleep(6)

    while True:
        print("CONTROL: starting control loop")
        try:
            asyncio.new_event_loop().run_until_complete(handleControlMessages())
        except:
            print("CONTROL: error")
            traceback.print_exc()
        print("CONTROL: event handler died")
        time.sleep(2)
        interface.movementSystemActive = False

if __name__ == '__main__':
    startControl()
