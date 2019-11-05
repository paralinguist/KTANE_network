import time
import string
import random
import socket
import json
import pygame

from select import select

pygame.init()

leds_available = ['IBM', 'CAR', 'RAC', 'LIT', 'ARM']
leds_on = {'IBM': 'A', 'CAR': 'B', 'RAC': 'C', 'LIT': 'D', 'ARM': 'E'}

INITIALISING = 0
ACTIVE = 1
DEFUSED = 2
EXPLODED = 3

black = (0, 0, 0)
white = (255, 255, 255)
blue = (0, 0, 127)
bright_blue = (0, 0, 255)
red = (127, 0, 0)
green = (0, 127, 0)
dim_green = (0,60,0)
bright_green = (0, 255, 0)
bright_red = (255, 0, 0)

led_dimensions = (36,37)

green_led = pygame.image.load('green_led.png')
green_led = pygame.transform.scale(green_led, led_dimensions)
red_led = pygame.image.load('red_led.png')
red_led = pygame.transform.scale(red_led, led_dimensions)
blue_led = pygame.image.load('blue_led.png')
blue_led = pygame.transform.scale(blue_led, led_dimensions)
orange_led = pygame.image.load('orange_led.png')
orange_led = pygame.transform.scale(orange_led, led_dimensions)
purple_led = pygame.image.load('purple_led.png')
purple_led = pygame.transform.scale(purple_led, led_dimensions)

led_images = [orange_led, purple_led, blue_led]
off_led = pygame.image.load('off_led.png')
off_led = pygame.transform.scale(off_led, led_dimensions)

background = pygame.image.load('background.png')
info_screen = pygame.image.load('timer_screen.png')
info_screen = pygame.transform.scale(info_screen, (700, 55))
timer_screen = pygame.image.load('timer_screen.png')

display_width = 800
display_height = 600


clock = pygame.time.Clock()

gameDisplay = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption('Defuse the bomb!')

pygame.time.set_timer(pygame.USEREVENT, 1000)

def quitgame():
  pygame.quit()
  quit()

def text_objects(text, font, colour, background=None):
  textSurface = font.render(text, True, colour, background)
  return textSurface, textSurface.get_rect()

def button(msg, x, y, w, h, ic, ac, action=None):
  mouse = pygame.mouse.get_pos()
  click = pygame.mouse.get_pressed()
  if x + w > mouse[0] > x and y + h > mouse[1] > y:
    pygame.draw.rect(gameDisplay, ac, (x, y, w, h))
    if click[0] == 1 and action != None:
      action()
  else:
    pygame.draw.rect(gameDisplay, ic, (x, y, w, h))

  textSurf, textRect = text_objects(msg, smallText, white)
  textRect.center = ((x + (w / 2)), (y + (h / 2)))
  gameDisplay.blit(textSurf, textRect)

def format_time(timer):
  minutes = timer // 60
  seconds = timer % 60
  if seconds < 10:
    seconds = f"0{seconds}"
  return f"{minutes}:{seconds}"

def get_digits(toggle_compat=False):
  digits = '00'
  if toggle_compat:
    number = random.randint(5,31)
    if number > 10:
      digits = str(number)
    else:
      digits = '0' + str(number)
  else:
    digits = str(random.randint(0,99))
  return digits

#Faux-randomly generates a serial number with these constraints:
#CCNNCNNCNN (where C is a letter character and N is a digit)
#At least one S and one R character
#The first two digits following an S or R character shall be >=05 and <= 31
def generate_serial():
  letters = string.ascii_uppercase
  serial = ''
  die = random.randint(0,5)
  if die == 0:
    serial = 'S' + random.choice(letters)
  elif die == 1:
    serial = random.choice(letters) + 'S'
  elif die == 2:
    serial = random.choice(letters) + 'R'
  elif die == 3:
    serial = 'R' + random.choice(letters)
  else:
    serial = random.choice(letters) + random.choice(letters)
  serial += get_digits('S' in serial or 'R' in serial)
  if 'S' in serial:
    serial += random.choice(letters) + get_digits()
  else:
    serial += 'S' + get_digits(True)
  if 'R' in serial:
    serial += random.choice(letters) + get_digits()
  else: 
    serial += 'R' + get_digits(True)
  return serial

#Randomly selects 3 LEDs and uses a coin toss to turn them on or off
def generate_leds():
  leds = random.sample(range(0,4),3)
  led_code = ''
  for led in leds:
    if random.choice([True, False]):
      led_code += str(led)
    else:
      led_code += leds_on[leds_available[led]]
  return led_code

def decode_leds(code):
  #should ultimately return JSON?
  leds = {}
  for led in code:
    if led in '01234':
      leds[leds_available[int(led)]] = 'off'
    else:
      led = int(led, 16) - 10
      leds[leds_available[led]] = 'on'
  return leds

def new_bomb(timer):
  fuse_start = time.time() + 15
  fuse_end = fuse_start + timer*60
  serial = generate_serial()
  leds = generate_leds()
  status = INITIALISING
  strikes = 0
  max_strikes = 3
  modules = 0
  global module_leds
  module_leds = {}
  bomb = {'fuse_start':fuse_start, 'fuse_end':fuse_end, 'serial':serial, 'leds':leds, 'status':status, 'strikes':strikes, 'max_strikes':max_strikes, 'modules':modules}
  pygame.mixer.music.load('./setup.ogg')
  pygame.mixer.music.play(0)
  return bomb

def add_strike(bomb):
  if bomb['status'] == ACTIVE:
    bomb['strikes'] += 1
    if bomb['strikes'] >= bomb['max_strikes']:
      bomb['status'] = EXPLODED
      pygame.mixer.Sound.play(explode)
      pygame.mixer.music.stop()
    else:
      pygame.mixer.Sound.play(strike)
  return bomb

def disarm_module(bomb):
  if bomb['status'] == ACTIVE:
    bomb['modules'] -= 1
    if bomb['modules'] <= 0:
      bomb['status'] = DEFUSED
      pygame.mixer.Sound.play(success)
      pygame.mixer.music.stop()
    print(f"Modules: {bomb['modules']}")
  return bomb

def pick_led_colours(leds):
  led_colours = []
  for led in leds:
    led_colours.append(random.choice(led_images))
  return led_colours

bomb = new_bomb(5)
led_colours = pick_led_colours(bomb['leds'])
json_bomb = json.dumps(bomb)

CONNECTION_LIST = []
RECV_BUFFER = 4096
PORT = 9876

SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SERVER_SOCKET.bind(("", PORT)) #listens on all IPs

#10 connections
SERVER_SOCKET.listen(10)

CONNECTION_LIST.append(SERVER_SOCKET)
print("Bomb server started.")

def restart_bomb():
  global bomb 
  bomb = new_bomb(5)

#25 char display?
def info_display(message):
  gameDisplay.blit(info_screen, (display_width*0.065, 15))
  chars = len(message)
  diff = 25 - chars
  message = message + (' ' * diff)
  TextSurf, TextRect = text_objects(message, info_text, bright_green)
  TextRect.left = display_width * 0.085
  TextRect.top = 20
  gameDisplay.blit(TextSurf, TextRect)

def place_serial(serial):
  serial = 'SN- ' + serial
  TextSurf, TextRect = text_objects(serial, serial_text, white, black)
  TextRect.left = display_width * 0.02
  TextRect.top = display_height * 0.95
  gameDisplay.blit(TextSurf, TextRect)

def place_led(text, status, x, y, colour):
  TextSurf, TextRect = text_objects(text, serial_text, white, black)
  TextRect.left = x
  TextRect.top = y
  gameDisplay.blit(TextSurf, TextRect)
  if status == 'off':
    colour = off_led
  gameDisplay.blit(colour, (x - 40,y - 10)) 

def place_modules(leds):
  TextSurf, TextRect = text_objects('Modules to disarm', serial_text, white, black)
  TextRect.left = display_width * 0.65
  TextRect.top = display_height * 0.2
  gameDisplay.blit(TextSurf, TextRect)
  x = display_width * 0.65
  y = display_height * 0.2 + 40
  item = 0
  for led in leds:
    gameDisplay.blit(leds[led], (x, y))
    x = x + 100
    item += 1
    if item % 3 == 0:
      y += 50
      x = display_width * 0.65
  for i in range(0,6-len(leds)):
    gameDisplay.blit(off_led, (x, y))
    x = x + 100
    item += 1
    if item % 3 == 0:
      y += 50
      x = display_width * 0.65

def place_strikes(strikes):
  x = h_centre - 110
  y = display_height * 0.8
  exes = ' ' + strikes * 'X '
  blanks = ' X X X '

  TextSurf, TextRect = text_objects('STRIKES', serial_text, white, black)
  TextRect.left = x + 55
  TextRect.top = y - 30
  gameDisplay.blit(TextSurf, TextRect)

  TextSurf, TextRect = text_objects(blanks, strike_text, black, black)
  TextRect.left = x
  TextRect.top = y
  gameDisplay.blit(TextSurf, TextRect)

  TextSurf, TextRect = text_objects(exes, strike_text, red, black)
  TextRect.left = x
  TextRect.top = y
  gameDisplay.blit(TextSurf, TextRect)

v_centre = display_height // 2
h_centre = display_width // 2

#Hard coded max of 6 modules
module_leds = {}

#Set up fonts
info_text = pygame.font.Font('./fonts/led_dots.ttf', 50)
serial_text = pygame.font.Font('./fonts/emboss.ttf', 20)
strike_text = pygame.font.Font('./fonts/inlanders.otf', 80)
largeText = pygame.font.Font('./fonts/digital-7.ttf', 115)
timer_backing = pygame.font.Font('./fonts/digital-7.ttf', 115)
smallText = pygame.font.Font('./fonts/inlanders.otf', 20)

#Set up sounds
pygame.mixer.init()
beep = pygame.mixer.Sound("./beep.ogg")
strike = pygame.mixer.Sound("./error.ogg")
explode = pygame.mixer.Sound("./explode.ogg")
success = pygame.mixer.Sound("./success.ogg")
  
while True:
  for event in pygame.event.get():
    if event.type == pygame.USEREVENT:
      if bomb['status'] == INITIALISING:
        if time.time() > bomb['fuse_start']:
          if bomb['modules'] > 0:
            bomb['status'] = ACTIVE
            pygame.mixer.music.stop()
            pygame.mixer.music.load('./strings.ogg')
            pygame.mixer.music.play(0)
          else:
            bomb['status'] = DEFUSED
            bomb = new_bomb(5)
            led_colours = pick_led_colours(bomb['leds'])
      elif bomb['status'] == ACTIVE:
        pygame.mixer.Sound.play(beep)
        if time.time() > bomb['fuse_end']:
          #kaboom
          bomb['status'] = EXPLODED

  gameDisplay.fill(black)
  timer = '0:00'

  gameDisplay.blit(background, (0,0))

  #TODO: Create a function for writing to the middle message
  if bomb['status'] == INITIALISING:
    info_display('Bomb is arming...')
    timer = format_time(int(bomb['fuse_start']-time.time()))
  elif bomb['status'] == ACTIVE:
    info_display('Bomb is active!')
    timer = format_time(int(bomb['fuse_end']-time.time()))
  elif bomb['status'] == DEFUSED:
    info_display('Bomb has been defused') #TODO: have a nice day
  elif bomb['status'] == EXPLODED:
    info_display('Bomb exploded.') #TODO: Sad face

  timer_screen = pygame.transform.scale(timer_screen, (218, 88))
  gameDisplay.blit(timer_screen, (h_centre - 109, v_centre - 40))
  TimerSurf, TimerRect = text_objects(timer, largeText, bright_green)
  TimerRect.center = ((display_width / 2), (display_height / 2))
  back_surf, back_rect = text_objects('8:88', timer_backing, dim_green)
  back_rect.center = ((display_width / 2), (display_height / 2))
  gameDisplay.blit(back_surf, back_rect)
  gameDisplay.blit(TimerSurf, TimerRect)
  
  led_x = display_width * 0.9
  led_y = display_height - 150
  leds = decode_leds(bomb['leds'])
  led_colour = 0
  for led in leds:
    place_led(led, leds[led], led_x, led_y, led_colours[led_colour])
    led_y += 50
    led_colour += 1

  place_strikes(bomb['strikes'])

  place_serial(bomb['serial'])

  place_modules(module_leds)

  button("Restart", 150, 450, 100, 50, green, bright_green, restart_bomb)

  pygame.display.update()
  dt = clock.tick(15)

  READ_SOCKETS, WRITE_SOCKETS, ERROR_SOCKETS = select(CONNECTION_LIST, [], [],0)
  for SOCK in READ_SOCKETS:
    if SOCK == SERVER_SOCKET:
      SOCKFD, ADDR = SERVER_SOCKET.accept()
      CONNECTION_LIST.append(SOCKFD)
      print(f'\rClient {ADDR[0]} {ADDR[1]} connected.')
    else:
      try:
        DATA = SOCK.recv(RECV_BUFFER)
        if DATA:
          request = DATA.decode().strip()
          if 'status' == request:
            print('Requested status...')
            SOCK.send(str(bomb['status']).encode())
          elif 'serial' == request:
            print('Requested serial...')
            SOCK.send(bomb['serial'].encode())
          elif 'leds' == request:
            print('Requested LEDs')
            SOCK.send(bomb['leds'].encode())
          elif 'strikes' == request:
            print('Requested strikes')
            SOCK.send(str(bomb['strikes']).encode())
          elif 'defuser' == request:
            print('Requested defuser name.')
            #TODO: not part of object yet
          elif 'fuse_start' == request:
            print('Requested fuse start time.')
            SOCK.send(str(bomb['fuse_start']).encode())
          elif 'fuse_end' == request:
            print('Requested fuse end time.')
            SOCK.send(str(bomb['fuse_end']).encode())
          elif 'time_remaining' == request:
            print('Requested time remaining.')
            SOCK.send(str(int(bomb['fuse_end']-time.time())).encode())
          elif 'add_strike' == request:
            print('Adding a strike.')
            bomb = add_strike(bomb)
            SOCK.send(str(bomb['strikes']).encode())
          elif 'disarm' in request:
            #TODO: allow only one disarm per module registered
            mod_id = request[6:]
            print(f'Disarm request: {mod_id}')
            bomb = disarm_module(bomb)
            module_leds[mod_id] = green_led
            SOCK.send(str(bomb['status']).encode())
          elif 'register' in request:
            mod_id = request[8:]
            registered = 0
            print(f'Register module: {mod_id}')
            if bomb['status'] == INITIALISING and not (mod_id in module_leds):
              bomb['modules'] += 1
              module_leds[mod_id] = red_led
              registered = 1
              print('Registered!')
              print(f"Modules: {bomb['modules']}")
            elif bomb['status'] == ACTIVE and mod_id in module_leds:
              registered = 1
              print('Already registered!')
            SOCK.send(str(registered).encode())
          elif 'bomb_object' == request:
            print('Requested whole object.')
            SOCK.send(json_bomb.encode())
          else:
            print('Unknown request...')
      except Exception as msg:
        print(type(msg).__name__, msg)
        print(f'\rClient {ADDR[0]} {ADDR[1]} disconnected.')
        SOCK.close()
        try:
          CONNECTION_LIST.remove(SOCK)
        except ValueError as msg:
          print(f'{type(msg).__name__}:{msg}')
        continue
SERVER_SOCKET.close()
