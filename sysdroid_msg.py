#!/usr/bin/env python3
########################################################################
# Filename    : srollmsg.py
# Description : scroll un message sur la matrice de leds
# auther      : papsdroid
# modification: 2019/09/07
########################################################################
import RPi.GPIO as GPIO
import time

#classe pour scroller des msg sur la matrice de leds
#-----------------------------------------------------------------------------------------
class ScrollMsg():
    def __init__(self):
        #dictionnaire des codes binaires représentant chaque charactère au format 5x3
        self.font5x3 = {    
            "0" : [0b11111, 0b10001, 0b11111], # "0"
            "1" : [0b01001, 0b11111, 0b00001], # "1"
            "2" : [0b10011, 0b10101, 0b01001], # "2"
            "3" : [0b10101, 0b10101, 0b11111], # "3"
            "4" : [0b00110, 0b01010, 0b11111], # "4"
            "5" : [0b11101, 0b10101, 0b10111], # "5"
            "6" : [0b11111, 0b10101, 0b10111], # "6"
            "7" : [0b10001, 0b10110, 0b11000], # "7"
            "8" : [0b11111, 0b10101, 0b11111], # "8"
            "9" : [0b11101, 0b10101, 0b11111], # "9"
     
            "A" : [0b01111, 0b10100, 0b01111], # "A"
            "B" : [0b11111, 0b10101, 0b01010], # "B"
            "C" : [0b01110, 0b10001, 0b10001], # "C"
            "D" : [0b11111, 0b10001, 0b01110], # "D"
            "E" : [0b11111, 0b10101, 0b10101], # "E"
            "F" : [0b01111, 0b10100, 0b10100], # "F"
            "G" : [0b01110, 0b10001, 0b11101], # "G"
            "H" : [0b11111, 0b00100, 0b11111], # "H"
            "I" : [0b00000, 0b10111, 0b00000], # "I"
            "J" : [0b00011, 0b00001, 0b11110], # "J"
            "K" : [0b11111, 0b00100, 0b11011], # "K"
            "L" : [0b11110, 0b00001, 0b00001], # "L"
            "M" : [0b11111, 0b01000, 0b11111], # "M"
            "N" : [0b11111, 0b10000, 0b01111], # "N"
            "O" : [0b01110, 0b10001, 0b01110], # "O"
            "P" : [0b11111, 0b10100, 0b01100], # "P"
            "Q" : [0b01110, 0b10010, 0b01101], # "Q"
            "R" : [0b11111, 0b10110, 0b01101], # "R"
            "S" : [0b01001, 0b10101, 0b10011], # "S"
            "T" : [0b10000, 0b11111, 0b10000], # "T"
            "U" : [0b11110, 0b00001, 0b11110], # "U"
            "V" : [0b11100, 0b00011, 0b11100], # "V"
            "W" : [0b11111, 0b00100, 0b11111], # "W"
            "X" : [0b11011, 0b00100, 0b11011], # "X"
            "Y" : [0b11000, 0b00111, 0b11000], # "Y"
            "Z" : [0b10011, 0b10101, 0b11001], # "Z"
 
            "." : [0b00001],                    # "."
            "," : [0b00001, 0b00010],           # ","
            ":" : [0b01010],                    # ":"
            "-" : [0b00100, 0b00100],           # "-"
            "°" : [0b01000, 0b10100, 0b01000],  # "°"
            "*" : [0b01010, 0b00100, 0b01010],  # "*"
            " " : [ 0, 0, 0]                    # " "
        }

        #disctionnaires de messages prédéfinis
        self.dicmsg = {
            "test"   :  " 0123456789 ABCDEFGHIJKLMNOPQRSTUVWXYZ °.,:-* ",
            "ecran1" :  " CPU-RAM-T° ",
            "ecran2" :  " 4*CPU ",
            "ecran3" :  " DISK ",
            "quit"   :  " BYE "
            }

    #retourne le message du dictionnaire dicmsg correspondant à une référence
    def msg_ref(self, ref):
        return self.dicmsg[ref]
            
    #générèe la liste des codes binaires correspondant à un texte
    def create_msg(self, text):
        matrix= []
        for i in range(len(text)):
            if text[i].upper() in self.font5x3: # recherche dans le dictionnaire l'existance du charactère
                matrix = matrix + self.font5x3[text[i].upper()]     # ajout des codes binaires correpondant à la lettre
                matrix = matrix + [0]                               # ajout d'une colonne vide pour séparrer chaque lettre.
        #print('matrix=', matrix)
        return matrix

    
        
        

    
        
        
