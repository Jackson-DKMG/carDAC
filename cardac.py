#!/usr/bin/python3

from os import system
from subprocess import check_output, STDOUT

from time import sleep
import RPi.GPIO as GPIO
from signal import pause
from glob import glob
from shutil import move


###### INITIALIZE DISPLAY #################
from threading import Thread
from Adafruit_SSD1306 import SSD1306_128_64
from PIL import Image, ImageDraw, ImageFont

RST = None
disp = SSD1306_128_64(rst=RST)
disp.begin()
disp.clear()
disp.display()
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, width, height), outline=0, fill=0)
padding = -2
top = padding
bottom = height - padding
x = 0
font = ImageFont.truetype('visitor1.ttf', 40)
font2 = ImageFont.truetype('visitor2.ttf', 18)
font3 = ImageFont.truetype('visitor1.ttf', 35)
draw.text((x + 5, top + 20), 'INITIALIZING', font=font3, fill=255)

########## END INIT DISPLAY ###############

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)   #play/pause  longpress = stop, very long press = reboot
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)   #previous, longpress = position - 10 ?
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)   #next, longpress = position + 10
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)   #toggle shuffle  longpress = switch playlist, very long press = shutdown
GPIO.setup(37, GPIO.OUT)
GPIO.output(37, GPIO.LOW)

#get the Audacious dbus environnement. Whatever this may be.
#env = check_output(['echo "$(strings /proc/"$(pidof audacious)"/environ | grep DBUS_SESSION_BUS_ADDRESS)"'], shell=True).decode("utf-8").rstrip()
env = check_output(['dbus-launch']).decode('utf_8').split('\n')[0]
#need to export this variable before each call to audtool, it appears
#print(env)

system("aplay /home/pi/online.wav")

system('{0} audacious -H &'.format(env))
#sleep(3)

for i in range(0,5):
    if i < 4:
        try:
           if check_output(["ps aux | grep audacious | grep -v grep"], shell=True):
              GPIO.output(37, GPIO.HIGH)
              break
        except:
              sleep(1)
              pass
    else:
        system("aplay /home/pi/failure.wav")
        system("sudo reboot")
		
#system("aplay /home/pi/online.wav")

#except:
#      pass

##### DISPLAY THE SONG. THREAD, CHECKING EVERY 5 SECONDS #########

class displaySong(Thread):

    def __init__(self):
        super().__init__()

    def run(self):  # display the current song on the OLED display. Update every 5s.

        # clear screen
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        disp.image(image)
        disp.display()

        curSong = ''




displaySong = displaySong()  # start the thread
#displaySong.daemon = True #not working if set to True
displaySong.start()

######### END DISPLAY SONG ############################

playlistLength = int(check_output(["{0} audtool playlist-length".format(env)], shell=True).decode('utf_8').rstrip())

#check_output(["{0} audtool playlist-length".format(env)], stderr=STDOUT, shell=True)

#print(playlistLength)

#check if new tracks and add them upon playlist change

def addTracks(playlist):    #check if new music files available, move to general folder and add to the concerned playlist.

    if playlist == 1:
        path = '/home/pi/newTracks/Metal'
    else:
        path = '/home/pi/newTracks/Soft'
    
   # print(path)

    newPath = '/home/pi/Music'

    try:
        files = [f for f in glob(path + '/*', recursive=True)]
       # print(files)
        for f in files:
            move(f, newPath)
            f = f.replace(path, newPath)
           # print(f)
            system("{0} audtool playlist-addurl '{1}'".format(env,f))
            playlistLength = int(check_output(["{0} audtool playlist-length".format(env)], shell=True).decode('utf_8').rstrip())  #need to update the playliste length

    except:
        pass  #if there are no files to add, it will raise an exception that we should ignore.


#CALLBACKS
def button1(channel):
   # print("button 1")
    for i in range(0,40):
        sleep(0.05)
       # print(i)
        if GPIO.input(11) != 0:
            if i > 1 & i <= 10:
                system(" {0} audtool playback-playpause".format(env))  # play/pause
                break
            elif i > 10 & i < 39:
                system("{0} audtool playback-stop".format(env))  # stop on longpress
                break
        elif i == 39:
            draw.text()
            system("{0} audtool shutdown".format(env))  # reboot on very long press (2+s)
            system("aplay /home/pi/reboot.wav")
            system("sudo reboot")

def button2(channel):   #PREVIOUS
    #print("button 2")
    for i in range(0,30):
        sleep(0.05)
       # print(i)
        if GPIO.input(13) != 0:
            if i >1 & i < 10:
                system("{0} audtool playlist-reverse".format(env))  # play/pause
                break
            elif i > 10 & i < 29:
                position = int(check_output(["{0} audtool playlist-position".format(env)], shell=True))
                new_pos = position - 10
                if new_pos < 1:
                    new_pos = playlistLength
                system("{0} audtool playlist-jump {1}".format(env, new_pos))
                break
        elif i == 29:                  #on very long press, jump to first item in playlist
                system("{0} audtool playlist-jump 1".format(env))
                break

def button3(channel):   #NEXT
    #print("button 3")
    for i in range(0,30):
        sleep(0.05)
        if GPIO.input(15) != 0:
            if i > 1 & i <= 10:
                system("{0} audtool playlist-advance".format(env))  # play/pause
                break
            elif i > 10 & i < 29:
                position = int(check_output(["{0} audtool playlist-position".format(env)], shell=True))
                new_pos = position + 10
                if new_pos > playlistLength:
                    new_pos = 1
                system("{0} audtool playlist-jump {1}".format(env, new_pos))
                break
        elif i == 29:                  #on very long press, jump to last item in playlist
                system("{0} audtool playlist-jump {1}".format(env, playlistLength))
                break

def button4(channel):
    #print("button 4")
    for i in range(0,40):
        sleep(0.05)
     #   print(i)
        if GPIO.input(16) != 0:  # toggle shuffle on single press
            if i > 1 & i <= 10:
                system("{0} audtool playlist-shuffle-toggle".format(env))
                break
            elif i > 10 & i < 39:  # switch playlist on long press and check if new tracks to add
            # cmd = "{0} audtool playlist-position".format(env)
                playlist = int(check_output(["{0} audtool current-playlist".format(env)], shell=True))
                if playlist == 1:
                   playlist = 2
                else:
                   playlist = 1

                system("{0} audtool playback-stop".format(env))
                system("{0} audtool set-current-playlist {1}".format(env, playlist))
                system("{0} audtool playback-playpause".format(env))

                try:            #not sure this try block is useful, there is one in the function itself.
                   addTracks(playlist)
                except:
                   pass

                break

        elif i == 39:  # shut down on very long press
             system("{0} audtool shutdown".format(env))
             system("aplay /home/pi/shutdown.wav")
             system("sudo shutdown -h now")

GPIO.add_event_detect(11, GPIO.FALLING, callback=button1, bouncetime=400)
GPIO.add_event_detect(13, GPIO.FALLING, callback=button2, bouncetime=400)
GPIO.add_event_detect(15, GPIO.FALLING, callback=button3, bouncetime=400)
GPIO.add_event_detect(16, GPIO.FALLING, callback=button4, bouncetime=400)

while True:
      #sleep(500)
      #pass
      pause()

#   Interrupts so no need for a while loop


#if __name__=="__main__":
#    controller()


