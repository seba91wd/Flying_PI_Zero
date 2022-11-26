#!/usr/bin/python

# import GPS
import os
from gps import *
from time import *
import time
import threading

# import LCD
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import subprocess

#import buzzer
import RPi.GPIO as GPIO

#seting the global variable(GPSD)
gpsd = None

#seting the global variable(LCD)
RST = None
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

#Seting GPOI mode (BUZZER)
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.OUT)

# Initialize LCD library.
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
font = ImageFont.load_default()

# bep_bep et beeep du buzzer
def bep_bep():
    GPIO.output(4, True)
    time.sleep(0.1)
    GPIO.output(4, False)
    time.sleep(0.1)
    GPIO.output(4, True)
    time.sleep(0.1)
    GPIO.output(4, False)
    time.sleep(1)
	
def beeep():
    GPIO.output(4, True)
    time.sleep(3)
    GPIO.output(4, False)

os.system('gpsd /dev/ttyS0 -F /var/run/gpsd.sock') #Initialize GPSD
os.system('clear') #clear the terminal (optional)

#Introduction
print ' FLYING PI ZERO'
print ' V1.83-TX'

draw.text((x, top), 'FLYING PI ZERO', font=font, fill=255)
draw.text((x, top + 10), 'V1.83-TX', font=font, fill=255)
disp.image(image)
disp.display()

bep_bep()
bep_bep()
bep_bep()

time.sleep(4)

#Tableau des stat
disp.clear()
disp.display()
draw.rectangle((0, 0, width, height), outline=0, fill=0)

cmd = "hostname -I | cut -d\' \' -f1"
IP = subprocess.check_output(cmd, shell=True)
cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
CPU = subprocess.check_output(cmd, shell=True)
cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
MemUsage = subprocess.check_output(cmd, shell=True)
cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
Disk = subprocess.check_output(cmd, shell=True)

draw.text((x, top), "IP: " + str(IP), font=font, fill=255)
draw.text((x, top + 8), str(CPU), font=font, fill=255)
draw.text((x, top + 16), str(MemUsage), font=font, fill=255)
draw.text((x, top + 25), str(Disk), font=font, fill=255)

disp.image(image)
disp.display()
time.sleep(4)
disp.clear()
disp.display()

class GpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global gpsd #bring it in scope
        gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
        self.current_value = None
        self.running = True #setting the thread running to true
 
    def run(self):
        global gpsd
        while gpsp.running:
            gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer

#Condition de creation du .csv
with open("/home/seb/gps_data.csv", 'w') as f:
    f.write("Heure; Latitude; Longitude; Altitude; Vitesse horizontal m/s; Vitesse vertical m/s \n")

if __name__ == '__main__':
    gpsp = GpsPoller() # create the thread
    try:
        gpsp.start() # start it up
        while True:
            heure = time.strftime('%X',time.localtime()) #Heure du system (Paris)
            os.system('clear')

            print
            print ' GPS reading'
            print '----------------------------------------'
            print 'Latitude     ' , gpsd.fix.latitude
            print 'Longitude    ' , gpsd.fix.longitude
            print 'Heure        ' , heure
            print 'Altitude     ' , gpsd.fix.altitude, 'm'
            print 'EPS          ' , gpsd.fix.eps
            print 'EPX          ' , gpsd.fix.epx
            print 'EPV          ' , gpsd.fix.epv
            print 'EPT          ' , gpsd.fix.ept
            print 'Vitesse hori ' , gpsd.fix.speed, 'm/s'
            print 'Vitesse vert ' , gpsd.fix.climb, 'm/s'
            print 'track        ' , gpsd.fix.track
            print 'mode         ' , gpsd.fix.mode
            print
            #print 'sats        ' , gpsd.satellites


            #Affiche les info sur le LCD
            draw.rectangle((0, 0, 128, 32), outline=0, fill=0)
            draw.text([(0, -2)], text="Lat: %s" % gpsd.fix.latitude, fill=255)
            draw.text([(0, 8)], text="Long: %s" % gpsd.fix.longitude, fill=255)
            draw.text([(0, 18)], text="Fixe mode: %s" % gpsd.fix.mode, fill=255)
            disp.image(image)
            disp.display()
            disp.clear()

            #ecriture dans le .cvs
            f = open("/home/seb/gps_data.csv", 'a')
            f.write("\n%s;%s;%s;%s;%s;%s" % (
                heure, gpsd.fix.latitude, gpsd.fix.longitude, gpsd.fix.altitude, gpsd.fix.speed, gpsd.fix.climb,))

            #ecriture dans le .txt
            k = open("/home/seb/gps_data.txt", 'w+')
            k.write("http://maps.google.fr/maps?f=q&hl=fr&q=%s,%s" % (gpsd.fix.latitude, gpsd.fix.longitude,))

            #ecriture dans le .url
            p = open("/home/seb/gps_data.url", 'w+')
            p.write(
                "[{000214A0-0000-0000-C000-000000000046}] \n"
                "Prop3=19,2 \n"
                "[InternetShortcut] \n"
                "URL=http://maps.google.fr/maps?f=q&hl=fr&q=%s,%s \n" % (gpsd.fix.latitude, gpsd.fix.longitude))

            #émission radio 1 pulses a 107.9 mhz
            os.system('sudo cat /home/seb/PiFmRds/src/pulses.wav | sudo /home/seb/PiFmRds/src/pi_fm_rds -freq 107.9 -ps Flying_pizero -audio -') 

            time.sleep(5) #set to whatever

    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        print "\nKilling Thread..."
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing

        disp.clear() #eteind le LCD
        disp.display()

        bep_bep() # Death beeep
        bep_bep()
        beeep()

    print "Done.\nExiting."