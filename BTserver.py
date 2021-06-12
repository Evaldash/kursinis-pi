import bluetooth
import RPi.GPIO as GPIO
import os
import subprocess
from subprocess import Popen

GPIO.setmode(GPIO.BOARD) #setup
GPIO.setwarnings(False)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)

fwd = GPIO.PWM(13, 100)
bck = GPIO.PWM(11, 100)
left = GPIO.PWM(18, 100)
right = GPIO.PWM(16, 100)

def startCamera():
    subprocess.Popen(['./mjpg-streamer.sh start'], shell=True, cwd="/home/pi/mjpg-streamer")
    
def stopCamera():
    subprocess.Popen(['./mjpg-streamer.sh stop'], shell=True, cwd="/home/pi/mjpg-streamer")
    
def restart():
    fwd.stop()
    bck.stop()
    left.stop()
    right.stop()
    
    startCamera()

    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)

    port = server_sock.getsockname()[1]

    uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

    bluetooth.advertise_service(server_sock, "SampleServer", service_id=uuid,
                                service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
                                profiles=[bluetooth.SERIAL_PORT_PROFILE],
                                )
    print("Waiting for connection on RFCOMM channel", port)

    client_sock, client_info = server_sock.accept()
    print("Accepted connection from", client_info)
    try:
        while True:
            data = client_sock.recv(1024)

            if not data:
                GPIO.cleanup()
                break
            if data:
                    if data == 'U': #up start
                        fwd.start(80)
                    elif data == 'u':
                        fwd.stop()
                    elif data == 'D': #down start
                        bck.start(80)
                    elif data == 'd':
                        bck.stop()
                    elif data == 'R':
                        right.start(90)
                    elif data == 'r': #right stop
                        right.stop()
                    elif data == 'L':
                        left.start(90)
                    elif data == 'l':
                        left.stop()
            print("Received", data)
    except bluetooth.btcommon.BluetoothError:
        print("Bluetooth connection lost!. Reloading program...")
        client_sock.close()
        server_sock.close()
        restart()

restart()