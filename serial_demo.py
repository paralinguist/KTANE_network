import serial, time
from bomb_network import BombServer
port = "/dev/tty.usbmodem14102"
#port = "/dev/tty.usbmodem14202"
baud = 115200

INITIALISING = 0
ACTIVE = 1
DEFUSED = 2
EXPLODED = 3

bomb_server = BombServer('127.0.0.1')
print(bomb_server.get_status())

ser = serial.Serial(port)
ser.baudrate = baud
registered = False
while True:
  if (ser.inWaiting()>0):
    data = ser.read().decode()
    if data == 'D':
      print('DISARM')
      bomb_server.disarm()
    elif data == 'S':
      print('STRIKE')
      bomb_server.strike()
    elif data == '!':
      registered = bomb_server.register()
      print(f'REGISTER: {registered}')
      if registered and bomb_server.get_status() == ACTIVE:
        ser.write('1'.encode())
      else:
        ser.write('0'.encode())
    else:
      print(f'? {data}')
  time.sleep(1)
