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
try: 
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
   font = ImageFont.truetype('visitor1.ttf', 30)
   font2 = ImageFont.truetype('visitor2.ttf', 18)
   font3 = ImageFont.truetype('visitor1.ttf', 19)
   draw.text((x + 3, top + 30), 'STARTING UP', font=font3, fill=255)  #display this while the system is booting
   disp.image(image)
   disp.display()
except:
    pass

########## END INIT DISPLAY ###############

GPIO.setwarnings(False)
#GPIO.setmode(GPIO.BOARD)

GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)   #play/pause,  longpress = stop, very long press = reboot
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)   #previous, longpress = position - 10, very long press = go to last song
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)   #next, longpress = position + 10, very long press = go to first song
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)   #toggle shuffle, longpress = switch playlist, very long press = shutdown
GPIO.setup(26, GPIO.OUT)
GPIO.output(26, GPIO.LOW)

#get the Audacious dbus environnement. Whatever this may be.
#env = check_output(['echo "$(strings /proc/"$(pidof audacious)"/environ | grep DBUS_SESSION_BUS_ADDRESS)"'], shell=True).decode("utf-8").rstrip()
env = check_output(['dbus-launch']).decode('utf_8').split('\n')[0]
#need to export this variable before each call to audtool, it appears
#print(env)

system("aplay /home/pi/online.wav")

system('{0} audacious -H &'.format(env))
#sleep(3)

for i in range(0,9):
    if i < 8:
        try:
           if check_output(["ps aux | grep audacious | grep -v grep"], shell=True):
              GPIO.output(26, GPIO.HIGH)
              break
        except:
              sleep(0.5)
              pass
    else:
        #print('error')
        system("{0} audtool shutdown".format(env))  #kill audacious (shouldn't matter if it isn't running).
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

        try:
           # clear screen
           draw.rectangle((0, 0, width, height), outline=0, fill=0)
           disp.image(image)
           disp.display()
        except:
           pass

        curSong = ''


        global running  # global variable to run/stop the thread
        running = 1

        while running == 1:
            try:
                s = check_output(["{0} audtool current-song".format(env)], shell=True).decode('utf_8').rstrip()
                #print(s)
                if not s == curSong:  # if the current song has changed, update the display. Otherwise, pass.

                    curSong = s
                    #print(curSong)
                    # reset the display
                    draw.rectangle((0, 0, width, height), outline=0, fill=0)
                    disp.image(image)
                    disp.display()

                    # should get something like 'Band - Album - Song'. Split to keep band and song
                    band = s.split(' -')[0].rstrip()  # remove trailing space. If the band name contains a -, the added space allows to get the full name.
                    # band will probably never be blank, but perhaps the song will (if no Album field for example. Handle the exception if so.
                    try:
                        song = s.split('- ')[2].lstrip()  # remove initial space (adding the extra space after the ' allows to get full title in case
                        #it includes the track number, e.g. "07-damage done"
                    except IndexError: #there should only be IndexError exceptions here.
                        try:
                            song = s.split('- ')[1].lstrip() #if no Album, then song title is probably at index 1
                        except IndexError:
                            song = ''
                            pass
                        pass
                    # got room for 12 characters with this font, and 4 rows. Split each string to occupy 2 rows if length is more than 12.
                    if len(band) > 12:
                        band1 = band[0:12]
                        if band[11] == ' ':   #if the 11th character is a space, somehow the next one is left out.
                            band2 = band[12:24]  # if longer than 24 characters, will be truncated anyway, no point keeping the extra stuff.
                        else:
                            band2 = band[13:24]
                        draw.text((x, top), band1, font=font3, fill=255)
                        draw.text((x, top + 15), band2, font=font3, fill=255)
                    else:
                        draw.text((x, top + 10), band, font=font3, fill=255)
                    if len(song) > 12:
                        song1 = song[0:12]
                        if len(song) > 12:
                            song1 = song[0:12]
                        if song[11] == ' ':
                            song2 = song[12:24]  # if longer than 24 characters, will be truncated anyway, no point keeping the extra stuff.
                        else:
                            song2 = song[13:24]
                        draw.text((x, top + 30), song1, font=font3, fill=255)
                        draw.text((x, top + 45), song2, font=font3, fill=255)
                    else:
                        draw.text((x, top + 40), song, font=font3, fill=255)

                    disp.image(image)
                    disp.display()  # display all the lines

                else:  # if the song hasn't changed since last check, do nothing
                    #print(curSong,s)
                    #system("{0} audtool playlist-advance".format(env))
                    pass

            except:
                try:
                   draw.text((x + 25, top + 30), 'ERROR', font=font, fill=255)
                   disp.image(image)
                   disp.display()
                except:
                    pass

                pass

            sleep(3) #let's update every 3s instead of 5, shouldn't put too much strain on the CPU.

try:
    displaySong = displaySong()  # start the thread
#displaySong.daemon = True #not working if set to True
    displaySong.start()
except:
    pass

######### END DISPLAY SONG ############################

######### START MANUAL DISPLAY SONG ###################

def manualSongUpdate():
    try:
            s = check_output(["{0} audtool current-song".format(env)], shell=True).decode('utf_8').rstrip()
            # reset the display
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
            disp.image(image)
            disp.display()
            band = s.split(' -')[0].rstrip()
            try:
                song = s.split('- ')[
                    2].lstrip()
            except IndexError:
                try:
                    song = s.split('- ')[1].lstrip()
                except IndexError:
                    song = ''
                    pass
                pass
            if len(band) > 12:
                band1 = band[0:12]
                if band[11] == ' ':
                    band2 = band[
                            12:24]  # if longer than 24 characters, will be truncated anyway, no point keeping the extra stuff.
                else:
                    band2 = band[13:24]
                draw.text((x, top), band1, font=font3, fill=255)
                draw.text((x, top + 15), band2, font=font3, fill=255)
            else:
                draw.text((x, top + 10), band, font=font3, fill=255)
            if len(song) > 12:
                song1 = song[0:12]
                if len(song) > 12:
                    song1 = song[0:12]
                if song[11] == ' ':
                    song2 = song[
                            12:24]  # if longer than 24 characters, will be truncated anyway, no point keeping the extra stuff.
                else:
                    song2 = song[13:24]
                draw.text((x, top + 30), song1, font=font3, fill=255)
                draw.text((x, top + 45), song2, font=font3, fill=255)
            else:
                draw.text((x, top + 40), song, font=font3, fill=255)

            disp.image(image)
            disp.display()  # display all the lines

    except:  #if any exception (like the display being used by the automatic update thread), just abort. Will update 5s later anyway.
        pass

playlistLength = int(check_output(["{0} audtool playlist-length".format(env)], shell=True).decode('utf_8').rstrip()) #self explanatory, yes ?

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
            global playlistLength
            playlistLength = int(check_output(["{0} audtool playlist-length".format(env)], shell=True).decode('utf_8').rstrip())  #need to update the playliste length
            #not sure this is right. Need to verify and perhaps make the variable global.
    except:
        pass  #if there are no files to add, it will raise an exception that we should ignore.


#CALLBACKS
def button1(channel):
   # print("button 1")
    for i in range(0,40):
        sleep(0.05)
       # print(i)
        if GPIO.input(17) != 0:
            if i > 1 & i <= 10:
                system(" {0} audtool playback-playpause".format(env))  # play/pause
                break
            elif i > 10 & i < 39:
                system("{0} audtool playback-stop".format(env))  # stop on longpress
                break
        elif i == 39:
            system("{0} audtool shutdown".format(env))  # reboot on very long press (2+s)
            system("aplay /home/pi/reboot.wav")
            try:
                global running
                running = 0
                displaySong.join()
                draw.rectangle((0, 0, width, height), outline=0, fill=0)
                disp.image(image)
                disp.display()
                draw.text((x + 5, top + 20), 'OFFLINE', font=font, fill=255)
                disp.image(image)
                disp.display()
            except:
                pass
            system("sudo reboot")

def button2(channel):   #PREVIOUS
    #print("button 2")
    global playlistLength
    for i in range(0,30):
        sleep(0.05)
       # print(i)
        if GPIO.input(27) != 0:
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
    #update the display manually. It may collide with the update thread however, to check. -- yes, it does. Disable.
    #manualSongUpdate()


def button3(channel):   #NEXT
    #print("button 3")
    global playlistLength
    for i in range(0,30):
        sleep(0.05)
        if GPIO.input(22) != 0:
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
    #manualSongUpdate()

def button4(channel):
    #print("button 4")
    global playlistLength
    for i in range(0,40):
        sleep(0.05)
     #   print(i)
        if GPIO.input(23) != 0:  # toggle shuffle on single press
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

            #update the playlist length variable with that of the other playlist.
                playlistLength = int(check_output(["{0} audtool playlist-length".format(env)], shell=True).decode('utf_8').rstrip())

            #manualSongUpdate()

                try:            #not sure this try block is useful, there is one in the function itself.
                   addTracks(playlist)
                except:
                   pass

                break

        elif i == 39:  # shut down on very long press
             system("{0} audtool shutdown".format(env))
             system("aplay /home/pi/shutdown.wav")

             try:
                 global running
                 running = 0
                 displaySong.join()
                 draw.rectangle((0, 0, width, height), outline=0, fill=0)
                 disp.image(image)
                 disp.display()
                 draw.text((x + 5, top + 20), 'OFFLINE', font=font, fill=255)
                 disp.image(image)
                 disp.display()
             except:
                 pass

             system("sudo shutdown -h now")

GPIO.add_event_detect(17, GPIO.FALLING, callback=button1, bouncetime=400)
GPIO.add_event_detect(27, GPIO.FALLING, callback=button2, bouncetime=400)
GPIO.add_event_detect(22, GPIO.FALLING, callback=button3, bouncetime=400)
GPIO.add_event_detect(23, GPIO.FALLING, callback=button4, bouncetime=400)

while True:
      #sleep(500)
      #pass
      pause()

#   Interrupts so no need for a while loop


#if __name__=="__main__":
#    controller()


