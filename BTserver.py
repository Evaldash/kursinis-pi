import bluetooth
import RPi.GPIO as GPIO
import os
import subprocess
from subprocess import Popen
import asyncio
import select

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

client_sock = None
server_sock = None

fwd_command_count=0
bck_command_count=0
timeout = 2

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
        fwd_command_count=0
        bck_command_count=0
        client_sock.setblocking(0)
        while True:
            ready = select.select([client_sock], [], [], 2)
            if ready[0]:
                data = client_sock.recv(1024)
    
                if not data:
                    GPIO.cleanup()
                    break
                if data:
                    if data == 'U'.encode(): #up start
                        fwd.start(80)
                    elif data == 'u'.encode():
                        fwd.stop()
                    elif data == 'D'.encode(): #down start
                        bck_command_count+=1
                        bck.start(80)
                    elif data == 'd'.encode():
                        bck.stop()
                    elif data == 'R'.encode():
                        right.start(90)
                    elif data == 'r'.encode(): #right stop
                        right.stop()
                    elif data == 'L'.encode():
                        left.start(90)
                    elif data == 'l'.encode():
                        left.stop()
                print("Received", data)
            else:
                fwd.stop()
                bck.stop()
                right.stop()
                left.stop()
            
    except bluetooth.btcommon.BluetoothError:
        print("Bluetooth connection lost!. Reloading program...")
        client_sock.close()
        server_sock.close()
        restart()
try:
    restart()
except(KeyboardInterrupt):
    print ('Finishing up')
    GPIO.cleanup()
    stopCamera()
    
    if not(server_sock is None):
        server_sock.close()
    if not(client_sock is None):
        client_sock.close()
    quit()