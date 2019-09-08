#!/usr/bin/env python3
########################################################################
# Filename    : sysDroid.py
# Description : information système raspberry pi (température, CPU, mémoire)
# auther      : papsdroid
# modification: 2019/08/14
########################################################################
import RPi.GPIO as GPIO
import time, os
import threading
import psutil
from sysdroid_msg import  ScrollMsg #liste des messages qui seront affichés par le sysdroid

#classe affichage infos système (via thread)
#-----------------------------------------------------------------------------------------
class SysDroid(threading.Thread):
    def __init__(self, tFanMin=40, tFanMax=50, speedscroll=10, verbose=False):     
        threading.Thread.__init__(self)  # appel au constructeur de la classe mère Thread
        self.etat=False             # état du thread False(non démarré), True (démarré)
        self.dataPin      = 11      # DS Pin 74HC595(Pin14)
        self.latchPin     = 13      # ST_CP Pin 74HC595(Pin12)
        self.clockPin     = 15      # SH_CP Pin 74HC595(Pin11)
        self.buttonSuivantPin = 33  # bouton pour changement d'affichage matrice de leds
        self.buttonOffPin = 40      # bouton d'extinction
        self.picOff     = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00] # toutes leds etteintes
        self.pic_id     = 0         # affichage sur la matrice de leds:  0(cpu, mem, T°), 1(4 CPUs), 2(DISK)
        self.speedscroll = speedscroll  # vitesse de défilement des messages
        self.verbose = verbose      #True: active les print
        #pin associés à la matrice de leds
        GPIO.setup(self.dataPin, GPIO.OUT)
        GPIO.setup(self.latchPin, GPIO.OUT)
        GPIO.setup(self.clockPin, GPIO.OUT)
        #pin associés aux boutons poussoirs
        GPIO.setup(self.buttonSuivantPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)    # mode INPUT, pull_up=high
        GPIO.setup(self.buttonOffPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)        # mode INPUT, pull_up=high
        GPIO.add_event_detect(self.buttonSuivantPin,GPIO.FALLING,callback = self.buttonSuivantEvent, bouncetime=3000)
        GPIO.add_event_detect(self.buttonOffPin,GPIO.FALLING,callback=self.buttonOffEvent, bouncetime=300)
        # liste des messages qui seront affichés sur la matrice de leds.
        self.msg = ScrollMsg()      
        self.afficheMsg = False     # True: affichage d'un message en cours. False: affichage des infos système
        print ('Sysdroid démarre ... ')
        self.scrollmsg(self.msg.msg_ref("ecran1"))   # message relatif à l'écran 01
        self.readsys = ReadSys(tFanMin, tFanMax, verbose)   # thread de lecture des informations système 
        self.readsys.start()                                # démarrage du thread de lecture des info systèmes

    #fonction exécutée quand le bouton poussoir "OFF" est pressé
    def buttonOffEvent(self,channel):
        self.stop()
        print('Extinction Raspberry...')
        os.system('sudo halt')
        #raise SystemExit
    
        
    #fonction exécutée quand le bouton poussoir "suivant" est pressé
    def buttonSuivantEvent(self, channel):
        if not(self.afficheMsg):
            pic_id_next = (self.pic_id<2) * (self.pic_id + 1)
            if pic_id_next==0:
                if self.verbose:
                    print('ecran 01:', self.msg.msg_ref("ecran1"))
                self.scrollmsg(self.msg.msg_ref("ecran1"))
            elif pic_id_next==1:
                if self.verbose:
                    print('ecran 02:', self.msg.msg_ref("ecran2"))
                self.scrollmsg(self.msg.msg_ref("ecran2"))
            else:
                if self.verbose:
                    print('ecran 03:', self.msg.msg_ref("ecran3"))
                self.scrollmsg(self.msg.msg_ref("ecran3"))
            self.pic_id = pic_id_next #provoque l'affichage nouvel écran quand le scrolling est terminé

    #transmet un code binaire 8bit au convertisseur série->parallèle 74HC595
    def shiftOut(self,val):
        #balayage gauche vers la droite par défaut (MSBFIRST)
        for i in range(0,8):
            GPIO.output(self.clockPin,GPIO.LOW); 
            GPIO.output(self.dataPin,(0x80&(val<<i)==0x80) and GPIO.HIGH or GPIO.LOW) #transmet 1 bit puis passe au suivant (val<<i)
            GPIO.output(self.clockPin,GPIO.HIGH); #le passsage HIGH value permet au 74HC595 d'acquérir un bit sur son port //

    #dessine pic sur la matrice de leds selon les 8 codes binaires fournis dans la liste pic)
    def picture(self, pic_matrix):
        x=0b10000000   # 1ère colonne
        for i in range(0,8): #8 codes binaires à transmettre, 1 pour chaque colonne
            GPIO.output(self.latchPin,GPIO.LOW) # prépare un changement des sorties parallèles
            self.shiftOut(pic_matrix[i])        # 8bits transmis au 1er étage 74HC595 = une barre verticale de 8 Leds
            self.shiftOut(~x)                   # 8 bits correspondant à la colonne à activier (LOW sur cette colonne, HIGH sur les autres, d'où ~x )
            GPIO.output(self.latchPin,GPIO.HIGH)  # sorties parralèles mises à jour sur les 2 étages
            time.sleep(0.001)                   # petit temps d'attente
            x>>=1                               # décallage 1 bit vers la droite = colonne suivante

    #scroll un message sur la matrice de leds. msg = codes hexa des lettres à afficher
    def scrollmsg(self, msg_txt):
        self.afficheMsg=True                        # arrête l'affichage du thread principal sur la matrice
        msg_matrix = self.msg.create_msg(msg_txt)   # transforme le texte en codes binaires
        for n in range(0,len(msg_matrix)-8):
            for j in range(0,self.speedscroll):     # répétition pour contrôler la vitesse de défilement du msg
                x=0b10000000   # 1ère colonne
                for i in range(n,n+8):
                    GPIO.output(self.latchPin,GPIO.LOW) # prépare un changement des sorties parallèles
                    self.shiftOut(msg_matrix[i])        # 8 bits correspondant à une colonne d'une lettre à afficher
                    self.shiftOut(~x)                   # 8 bits correspondant à la colonne à activier (LOW sur cette colonne, HIGH sur les autres, d'où ~x )
                    GPIO.output(self.latchPin,GPIO.HIGH) # sorties parralèles mises à jour sur les 2 étages
                    time.sleep(0.001)                   # petit temps d'attente
                    x>>=1                               # colonne suivante
        self.afficheMsg=False                           # remet l'affichage du thread principal sur la matrice
        
    #exécution du thread
    def run(self):
        self.etat=True
        while (self.etat):
            #affichage indicateurs sur la matrice de leds
            if not(self.afficheMsg):
                self.picture(self.readsys.pic[self.pic_id])
            else:
                time.sleep(0.1) #mise en pause (sinon proc saturé par boucle infinie)
        
    #arrêt du thread
    def stop(self):
        self.etat=False
        self.readsys.stop()
        self.scrollmsg(self.msg.msg_ref("quit"))
        GPIO.cleanup()
        print('Sysdroid arrêté')

#classe de lecture des informations systèmes à lire
#-----------------------------------------------------------------------------------------
class ReadSys(threading.Thread):
    def __init__(self, tFanMin=40, tFanMax=50, verbose=False):
        threading.Thread.__init__(self)  # appel au constructeur de la classe mère Thread
        self.verbose = verbose      # True active les print
        self.etat=False                  # état du thread False(non démarré), True (démarré)
        self.delay = 30                  # délay en secondes entre chaque nouvelle lecture
        self.t_min = 30                  # température minimale (0% si en dessous)
        self.t_max = 80                  # température maximale (100% si au dessus)
        self.fan_tOn  = tFanMax          # température d'activation du ventilateur
        self.fan_tOff = tFanMin          # température d'extinction du ventilateur
        self.cpu_t=0                     # température du CPU  
        self.cpu_util   = 0              # CPU global utilisation (%)
        self.cpus_util  = [0,0,0,0]      # CPUs utilisation (%)
        self.mem_used   = 0              # mémoire physique utilisée (%)
        self.disk_used  = 0              # usage du disk à la racine ('/') en %
        self.fanPin    = 31              # GPIO pin: control fan power
        GPIO.setup(self.fanPin, GPIO.OUT)
        GPIO.output(self.fanPin,GPIO.LOW) # fan off au début
        self.fanOn    = False            # True: ventilateur en marche, False: ventilateur à l'arrêt

        # codes binaires 8bits représentant les dessins (1 code par colonne) sur la matrice de leds
        #pic[0] représente les niveaux CPU (global), MEME et T° CPU
        #pic[1] représente les niveaux des 4 CPUs
        #pic[2] représente les niveaux espace disque à la racine de la carte SD ('/')
        self.pic = [ [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],     # pic[0] par defaut toutes les leds etteintes
                     [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],     # pic[1] par defaut toutes les leds etteintes    
                     [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00] ]    # pic[3] par defaut toutes les leds etteintes    
        self.hexaNiv = [0x0, 0x01,0x03,0x07,0x0F,0x1F,0x3F,0x7F,0xFF] # correspondances des niveaux 0, 1/8, 2/8,... 8/8 en hexadécimal

    #lecture de la température CPU
    def get_cpu_temp(self):     
        tmp = open('/sys/class/thermal/thermal_zone0/temp')
        cpu = tmp.read()
        tmp.close()
        t=float(cpu)/1000
        if t<self.t_min:
            t=self.t_min
        if t>self.t_max:
            t=self.t_max
        return t 

    #converti la t° CPU en % entre t_min et t_max
    def convert_cpu_pct(self):
        return (float)(self.cpu_t-self.t_min)/(self.t_max-self.t_min)*100

    #active ou désactive le ventilateur
    def fan_chg(self, activation:True):
        GPIO.output(self.fanPin, activation and GPIO.HIGH or GPIO.LOW)
        self.fanOn = activation
        if self.verbose:
            print('Ventilateur', self.fanOn, 'cpu_t:',self.cpu_t,'°C')
        
    
    #démarrage du thread
    def run(self):
        self.etat=True
        if self.verbose:
            print('Thread lecture info système démarré')
        while (self.etat):
            #lecture et stockage des informations système
            self.cpu_t = self.get_cpu_temp()
            self.cpu_util = psutil.cpu_percent()
            self.cpus_util = psutil.cpu_percent(percpu=True)
            self.mem_used = psutil.virtual_memory()[2]
            self.disk_used = psutil.disk_usage('/')[3]
            if self.verbose:
                print ('CPU:', self.cpu_util,'CPUs:', self.cpus_util,'% MEM used:',self.mem_used,'CPU T°:', self.cpu_t,'°C', ' DISK:',self.disk_used)
            #défini les codes hexa à utiliser pour la matrice de leds
            self.pic_levels() 
            #fan control
            if not(self.fanOn) and (self.cpu_t >= self.fan_tOn):
                self.fan_chg(True)
            elif self.fanOn and (self.cpu_t < self.fan_tOff): #extinction ventilateur
                self.fan_chg(False)
            time.sleep(self.delay)

    #arrêt du thread
    def stop(self):
        self.etat=False
        if self.verbose:
            print('Thread lecture info système stoppé')

    #converti un niveau de 0 à 100% en code héxadécimal à 8 niveaux de 0x01 à 0xFF
    #  correspondant à une barre de 8leds sur une colonne de la matrice de leds
    #  0 leds alluméee: 00000000=0x00, 8 leds allumées: 11111111=0xFF etc...
    def convert_level_hexa(self, niv):
        r=self.hexaNiv[round(niv/100*8+0.4999)]
        return(r)

    #prépare l'affichage #1 sur la matrice de leds: cpu_util, mem_usage et cpu_T°
    def pic_levels(self):

        #affichage 0: CPU, MEM et T°
        #-------------------------------------------
        # 2 premieres colonnes: CPU utilisation
        self.pic[0][0] = self.convert_level_hexa(self.cpu_util)
        self.pic[0][1] = self.pic[0][0]
        self.pic[0][2] = 0x00 #leds etteintes
        # 2 colonnes suivantes: utilisation mémoire
        self.pic[0][3] = self.convert_level_hexa(self.mem_used)
        self.pic[0][4] = self.pic[0][3]
        self.pic[0][5] = 0x00 #leds etteintes
        # 2 colonnes suivantes: température CPU
        self.pic[0][6] = self.convert_level_hexa(self.convert_cpu_pct())
        self.pic[0][7] = self.pic[0][6]       

        #affichage 1: 4 CPUs
        #----------------------------------------------
        self.pic[1][0] = 0x00
        self.pic[1][1] = 0x00
        self.pic[1][2] = self.convert_level_hexa(self.cpus_util[0])
        self.pic[1][3] = self.convert_level_hexa(self.cpus_util[1])
        self.pic[1][4] = self.convert_level_hexa(self.cpus_util[2])
        self.pic[1][5] = self.convert_level_hexa(self.cpus_util[3])
        self.pic[1][6] = 0x00
        self.pic[1][7] = 0x00

        #affichage 2: disk usage. 1 led = 100/64 = 1.5625 % d'utilisation. 8 leds (1 colonne entière)=12.5%
        #-----------------------------------------------
        n = (int)(self.disk_used/12.5)          # nombre des barres verticales pleines 0 à 8
        r = (int)((self.disk_used%12.5)/1.5825) # différenciel avec barres pleines 0 à 7
        for i in range(n):
            self.pic[2][i] = 0xFF           # barres pleines = tranches d'utilisation à 12.5%
        if n<8:
            self.pic[2][n] = self.hexaNiv[r]    # résiduel avec barres pleines
            for i in range(n+1,8):
                self.pic[2][i] = 0x00           # barres vides
        
