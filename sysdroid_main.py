#!/usr/bin/env python3
########################################################################
# Filename    : SysDroid_main.py
# Description : information système raspberry pi (température, CPU, mémoire)
# auther      : papsdroid.fr
# modification: 2019/08/14
########################################################################

import RPi.GPIO as GPIO
import time
from sysdroid import  SysDroid

#classe application principale
#------------------------------------------------------------------------------
class Application():
    def __init__(self,tFanMin=40, tFanMax=50, speedscroll=10, verbose=False):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)  # localisation physique des GPIOs
        self.sysdroid = SysDroid(tFanMin, tFanMax, speedscroll, verbose) 
        self.sysdroid.start()     # démarrage du thread de surveillance système
     	
    def loop(self):
        while True:
            time.sleep(1)
            continue

    def destroy(self):          # fonction exécutée sur appui CTRL-C
        self.sysdroid.stop()    # arrêt du thread de surveillance système


if __name__ == '__main__':     # Program start from here
    appl=Application(verbose=True)  
    try:
        appl.loop()
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        appl.destroy()    


