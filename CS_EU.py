#!/usr/bin/python3
# add this so that the program runs imidiately after the raspberry turns on

#----------------IMPORTS----------------
import os
import math
import datetime
#-------LoRa------{
from time import sleep
from SX127x.LoRa import *
from SX127x.board_config import BOARD
#}
#-------BMP-------{
import time
from bmp_280 import BMP280
#}
#-------GPS-------{
import board
import busio
import adafruit_gps
import serial
#}
#------BUZZER------{
from gpiozero import Button
from gpiozero import Buzzer
#}
#------CAMERA------{
from time import *
from picamera import PiCamera
#}
#-------UPS--------{
from libINA219 import *
#}
#------NN----{
import numpy as np
from PIL import Image
#}

# -------------------------------------------- HILL -------------------------------------------- #
# use this dictionary for character to number mapping. case sensitivity doesn't apply any more
char2num = {
      "0": 0, "A": 26, "B": 1, "b": 1, "C": 2, "c": 2, "D": 3, "d": 3, "E": 4, "e": 4, "F": 5, "f": 5, "G": 6, "g": 6, "H": 7, "h": 7, "I": 8, "i": 8, "J": 9, "j": 9,
      "K": 10, "k": 10, "L": 11, "l": 11, "M": 12, "m": 12, "N": 13, "n": 13, "O": 14, "o": 14, "P": 15, "p": 15, "Q": 16, "q": 16,"R": 17, "r": 17, "S": 18, "s": 18,
      "T": 19, "t": 19, "U": 20, "u": 20, "V": 21, "v": 21, "W": 22, "w": 22, "X": 23, "x": 23, "Y": 24, "y": 24, "Z": 25, "z": 25, "a": 26, "1": 27, "2": 28, "3": 29,
      "4": 30, "5": 31, "6": 32, "7": 33, "8": 34, "9": 35, ".": 36}

num2char = { 
# same mapping, but from number to character
      26: "A", 1: "B", 2: "C", 3:"D", 4:"E", 5:"F", 6:"G", 7:"H", 8:"I", 9:"J", 10:"K", 11:"L", 12:"M", 13:"N", 14:"O", 15:"P", 16:"Q", 17:"R", 18:"S", 19:"T", 20:"U",
      21:"V", 22:"W", 23:"X", 24:"Y", 25: "Z", 0 :"0", 27:"1",28: "2", 29: "3",30: "4", 31: "5", 32:"6",33: "7",34: "8", 35:"9",36: "."}


def get_text2num(text):
    """
    Converts letters to numbers based on the mapping above
    
    In case the number of letters is odd, append one more element at the end in order for the algoritm to work

    Return: List of converted characters
    """
    numerictext=[]

    for letter in text:
        numerictext.append(char2num[letter])
    if len(numerictext) %2 != 0:
        numerictext.append(0)

    return numerictext


def encryptS(msg, key):
    """
    Symmetric encryption/decryption

    Return: list of characters
    """
    init_msg = get_text2num(msg)

    encryptedtext=[]
    for i in range(0,len(init_msg)):
        # Split message in pairs.
        if i%2==0:
            # if the position is even (0, 2, 4,...), calculate the encrypted/decrypted value and append it in a temp list
            temp=(init_msg[i]*key[0]+init_msg[i+1]*key[1])%37
        else:
            # same precedure for odd position
            temp=(init_msg[i-1]*key[2]+init_msg[i]*key[3])%37
        # save the value in the temp list, in a strict sequence (1st_odd-1st_even-2nd_odd...)
        encryptedtext.append(num2char[temp]) 

    return encryptedtext


# -------------------------------------------- RSA -------------------------------------------- #
def rsa(msg, key, n):
    """
    RSA process, similar for encryption and decryption, key changes

    Return: changed (encrypted or decrypted) message
    """
    res = 1

    msg = msg % n

    if (msg == 0):
        return 0

    while (key > 0):
        if ( (key & 1) == 1):
            res = (res * msg) % n

        key = key >> 1

        msg = (msg * msg) % n

    return res

def encrypt(x, key, n):
    """
    Takes as a parameter an ascii code (number), encrypts it using RSA and converts
    the result to a 3-character string, adding 0 at the start.

    Return: the encrypted and converted string
    """
    x = rsa(x, key, n)
    xx = str(x)
    lx = len(xx)
    for i in range(lx, 3):
        xx = "0" + xx

    return xx

def decrypt(x, key, n):
    """
    Takes as parameter a 3-character string and after converting it to an int
    it decrypts it using RSA

    Return: the decrypted int
    """
    x = int(x)
    x = rsa(x, key, n)

    return x

# -------------------------------------------- AFTER-LANDING ROUTINE -------------------------------------------- #
def send_gps():
    """
    After the CanSat lands, send continuously the last valid position
    """
    if gps.has_fix:
        latitude = str(gps.latitude)
        longitude = str(gps.longitude)
        for i in range(len(latitude), 10):
            latitude = latitude + "0"
        for i in range(len(longitude), 10):
            longitude = longitude + "0"
    else:
        latitude="0000000000"
        longitude="0000000000"
        
    templist=[]
    templist.append(ord('X'))
    for i in latitude:
        templist.append(ord(i))
    templist.append(ord('Y'))
    for i in longitude:
        templist.append(ord(i))

    templist.append(ord('T'))

    # get temperatrue from BMP sensor asd convert it to a string
    temperature = bmp280.read_temperature()

    # do the same for the pressure
    pressure = bmp280.read_pressure()


    temperature = str(temperature)
    for i in range(len(temperature),5):
        temperature= temperature + "0"
    
    pressure = str(pressure)
    for i in range(len(pressure),7):
        pressure = pressure + "0"
    

    for i in range(0,5):
        templist.append(ord(temperature[i]))
            
    templist.append(ord('P'))
    for i in range(0,7):
        templist.append(ord(pressure[i]))

    
    lora.write_payload(templist)
    lora.set_mode(MODE.TX)
    lora.clear_irq_flags(TxDone=1)

# -------------------------------------------- MLP -------------------------------------------- #

def sigmoid(x):
    """
    Activation function, Sigmoid function

    Return: x run through the Sigmoid Function
    """
    sx = 1 / (1 + math.exp((-1.0) * x))
    return sx


def run_nn(picName):
    """
    Neural Network prediction function

    Parameter: image name

    Return: number between 0-1, probability of fire being in the image
    """
    noInputs = 64*64*3
    noHidden = 200
    noOutputs = 1

    img = Image.open(picName)
    img = img.resize((64,64))

    # we take the rgb info from each pixel in the list
    pixels = list(img.getdata())
    # the list becomes a numpy array with one row and three columns for each pixel
    inputs = np.array(pixels)
    # the array becomes one-dimensional, where 'r' 'g' 'b' are in this order for each pixel
    inputs = inputs.flatten()

    # normalization so the inputs have values between 0-1
    for i in range(0, len(inputs)):
        inputs[i] = inputs[i] / 255.0

    output = 0

    # hidden calculation - dot product
    # inputs: noInputs
    # hw: noInputs x noHidden
    # hidden: noHidden
    hidden = np.dot(inputs, hw)

    # adding hiddenBiases
    hidden = np.add(hidden, hb)

    # for each hidden we calculate the sigmoid
    for i in range(0,  noHidden):
        hidden[i] = sigmoid(hidden[i])

    # output calculation - multiply elementwise
    # hidden: noHidden
    # ow: noHidden
    # temp: noHidden
    temp = np.multiply(hidden, ow)

    # we add all elements from temp and the outputBias and run the output through sigmoid
    output = np.sum(temp)
    output = sigmoid(output + ob)

    return output


# -------------------------------------------- CLASS DECLARATION -------------------------------------------- {
class vspaceLORA(LoRa):
    
    def __init__(self, verbose=False):
        """ 
        vspaceLORA object initiation, inherits the LoRa class from the library
        """

        super(vspaceLORA, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)

        self.localAddress = "CS"

        # our addition: list for each character fot the message that cansat send to the ground station
        self.outgoing = []

        self.incoming = []


        # This dictionary contains the name of a device and a list. In the list, the first two numbers are 
        # the public key of that device. We decided that all public keys are known to all devices.
        # The third number is that device's symmetric key. At first, it will be 0 and updated to a 4
        # digit number after a handshake with a device is done. 
        self.cs_dict = {'DA':[95, 247, 0], 'LH':[139, 403, 0], 'DB':[281, 323, 0], 'GS':[67, 377, 1234]}

        self.keyCS = 193    # public
        self.keyCS2 = 157   # private
        self.nCS = 341

        self.end = False
        self.counter = 0

        self.picCounter = 0


    def start(self):
        """
        Main method with which vspaceLORA works. It already exists in the LoRa class, but we changed it
        and added some commands to send data to ground station
        """
        global f1,f2
        # set communication frequency to 434 MHz
        self.set_freq(434)
        self.reset_ptr_rx()
        # get into recieve mode
        self.set_mode(MODE.RXCONT)

        # loop infinetly
        while self.end == False:
            sleep(0.25)
            gps.update()
            sleep(0.25)
            gps.update()
            sleep(0.25)
            gps.update()
            sleep(0.25)
            rssi_value = self.get_rssi_value()
            status = self.get_modem_status()
            sys.stdout.flush()

            # the cansat sends to the ground station one message per second. so each time, increase this counter
            # by one, meaning that one second has passed. use this character to determine if a specific action
            # needs to be taken e.g. take a photo, update data ect.

            self.counter = self.counter + 1;

            # 10 seconds after the cansat get out of the rocket,take fisrt picture
            if self.counter == 10:
                camera.capture("/home/cansat/cansatPic1.jpg")
                pic_taken.append("/home/cansat/cansatPic1.jpg")

            # 20 seconds in, add the symmetric key for communication with Device B
            # Note: this is done as a safety messure in case the handshake is not successful. This should already be done by now
            #       so if the handshake between DB and CanSat was successful, this key already exists in the dictionary.
            if self.counter == 20:
                self.cs_dict['DB'][2]=1357

            # 30 second in, take the second picture
            if self.counter == 30:
                camera.capture("/home/cansat/cansatPic2.jpg")
                pic_taken.append("/home/cansat/cansatPic2.jpg")

            # after 90 seconds, close the current log files (for safety) and open new ones
            if self.counter == 90:
                f1.close()
                f2.close()
                print("files 0 closed")
                f1 = open("/home/cansat/first_mission1.txt", "w")
                f2 = open("/home/cansat/sec_mission1.txt", "w")

            # after two minutes, the mission is considered finished, so close log files and return from start
            if self.counter == 180:
                self.end = True
                f1.close()
                f2.close()
                print("files 1 closed")
                return 

            # creating the outgoing message for the ground station, based on the protocol
            # append each character one-by-one, after they have been converted to ascii

            # use append() to add characters at the end of the list
            # use ord() to convert characters to ascii

            # add (not encrypted) the following:
            # 1. the sender
            self.outgoing.append(ord('C'))
            self.outgoing.append(ord('S'))
            # 2. next recipient
            self.outgoing.append(ord('G'))
            self.outgoing.append(ord('S'))

            # make the list for the message that will be encrypted
            templist = []
            # add final recipient
            templist.append('G')
            templist.append('S')
            # the type if message (M->simple message)
            templist.append('M')
            # Temperature identifier
            templist.append('T')

            # get temperature and pressure from sensor
            temperature = bmp280.read_temperature()
            pressure = bmp280.read_pressure()

            # use the formula for the acceleration of gravity to calculate the altitude
            # read from the ground, or have the ground station send it in the begining
            groundPressure = 1013.25
            bmpAltitude = ((pow((groundPressure / pressure), (1.0/5.257))-1) * (temperature + 273.15))/ 0.0065
            #print("ΥΨΟΜΕΤΡΟ:" + str(bmpAltitude))


            temperature = str(temperature)
            pressure = str(pressure)
            
            # add zeros if digits are not the appropriate amount that the protocol defines
            for i in range(len(temperature),5):
                temperature= temperature + "0"
            
            for i in range(len(pressure),7):
                pressure = pressure + "0"
    
            for i in range(0,5):
                templist.append(temperature[i])

            # Pressure identifier
            templist.append('P')

            for i in range(0,7):
                templist.append(pressure[i])


            # based on the code in the library, we get the gps values
            # convert the from numbers to string 

            if gps.has_fix:
                latitude = str(gps.latitude)
                longitude = str(gps.longitude)
                altitude = str(gps.altitude_m)                

                for i in range(len(latitude), 10):
                    latitude = latitude + "0"
                for i in range(len(longitude), 10):
                    longitude = longitude + "0"
                for i in range(len(altitude), 6):
                    altitude = altitude + "0"
            else:
                latitude="0000000000"
                longitude="0000000000"
                altitude="000000"
                
            #print(latitude)
            #print(longitude)
            #print(altitude)

            # Add X, Y and H parameters based on the protocol
            templist.append('X')

            for i in latitude:
                templist.append(i)


            templist.append('Y')

            for i in longitude:
                templist.append(i)


            templist.append('H')

            for i in altitude:
                templist.append(i)

            # add to the message the battery presentage
            bus_voltage = ina219.getBusVoltage_V()
            p = (bus_voltage - 6)/2.4*100
            if(p > 100):
                p = 100
            if(p < 0):
                p = 0
            p=str(p)
            templist.append('V')
            for i in range(0,len(p)):
                templist.append(p[i])

            
            # add to the log file the final message which has not been encrypted yet, along with a timestamp
            timestamp = datetime.datetime.now()
            if self.end == False:
                f1.write(timestamp.strftime("%H")+":"+timestamp.strftime("%M")+":"+timestamp.strftime("%S")+" "+str(self.outgoing)+str(templist)+"\n")

            # encrypt the message using the symmetric key for the communication with GS
            templist = encryptS(templist, [1, 2, 3, 4])

            # add the encrypted message to the outgoing list
            for item in templist:
                self.outgoing.append(ord(item))


            # acording to the library, the following commands send the message
            self.write_payload(self.outgoing)
            self.set_mode(MODE.TX)
            self.clear_irq_flags(TxDone=1)
            #sleep(.2)

            # clear the list right after the message is sent
            self.outgoing = []

            # get into recieve mode before repeating the loop
            self.set_mode(MODE.RXCONT) 

    def on_rx_done(self):
        # get the message
        self.clear_irq_flags(RxDone=1)
        self.incoming = self.read_payload(nocheck=True)
        print ("Receive: ")
        print(bytes(self.incoming).decode("utf-8",'ignore')) # Receive DATA

        # Wait for the client be ready
        time.sleep(0.2) 

        #timestamp = str(datetime.datetime.now())
        timestamp  = datetime.datetime.now()

        # convert the incoming list to string
        inc = ""
        for item in self.incoming:
            inc = inc + str(chr(item))

        sender = inc[0:2]
        nextNode = inc[2:4]


        # variable action is used to have a simple control of what must be done at each step of an incoming message

        # check if the next recipient (nextNode) is the CanSat or not and set action accordingly
        if nextNode != self.localAddress:
            action = "IGNORE"
            if self.end == False:		
                f2.write(timestamp.strftime("%H")+":"+timestamp.strftime("%M")+":"+timestamp.strftime("%S")+" IGNORED:"+inc+"\n")
        else:                       
            action = "DECRYPT"


        
        # identify what decryption algorithm must be used

        if action == "DECRYPT":
            if (sender in self.cs_dict) and (self.cs_dict[sender][2] == 0):
                # if nextNode is cansat and the symmetric key of the comunication with the sender doesn't exist, decrypt using RSA
                # (it's a handshake message which contains the symmetric key)
                # if the message type is different, the cansat ignores it, otherwise, it updates the dictionary contaning the keys


                # save here the final recipient
                destination_r = str(chr(decrypt(inc[4:7], self.keyCS2, self.nCS))) + str(chr(decrypt(inc[7:10], self.keyCS2, self.nCS)))

                # find the message type
                a = str(chr(decrypt(inc[10:13], self.keyCS2, self.nCS)))
                a = a + str(chr(decrypt(inc[13:16], self.keyCS2, self.nCS)))
                a = a + str(chr(decrypt(inc[16:19], self.keyCS2, self.nCS)))

                msgType = str(chr(decrypt(a, self.cs_dict[sender][0], self.cs_dict[sender][1])))

                # first digit of the symmetric key
                a = str(chr(decrypt(inc[19:22], self.keyCS2, self.nCS)))
                a = a + str(chr(decrypt(inc[22:25], self.keyCS2, self.nCS)))
                a = a + str(chr(decrypt(inc[25:28], self.keyCS2, self.nCS)))

                # text message
                msgText = str(chr(decrypt(a, self.cs_dict[sender][0], self.cs_dict[sender][1])))

                # in the incoming list, the first digit of the first number of the symmetric key
                # must be at location 13 and the first digit of the last number at location 22

                a = str(chr(decrypt(inc[28:31], self.keyCS2, self.nCS)))
                a = a + str(chr(decrypt(inc[31:34], self.keyCS2, self.nCS)))
                a = a + str(chr(decrypt(inc[34:37], self.keyCS2, self.nCS)))
                msgText = msgText + str(chr(decrypt(a, self.cs_dict[sender][0], self.cs_dict[sender][1])))
               
                a = str(chr(decrypt(inc[37:40], self.keyCS2, self.nCS)))
                a = a + str(chr(decrypt(inc[40:43], self.keyCS2, self.nCS)))
                a = a + str(chr(decrypt(inc[43:46], self.keyCS2, self.nCS)))
                msgText = msgText + str(chr(decrypt(a, self.cs_dict[sender][0], self.cs_dict[sender][1])))

                a = str(chr(decrypt(inc[46:49], self.keyCS2, self.nCS)))
                a = a + str(chr(decrypt(inc[49:52], self.keyCS2, self.nCS)))
                a = a + str(chr(decrypt(inc[52:55], self.keyCS2, self.nCS)))
                msgText = msgText + str(chr(decrypt(a, self.cs_dict[sender][0], self.cs_dict[sender][1])))
                

                print("DECRYPTED--> " + msgType + msgText)
                # the action changes only if the message has been decrypted
                action = "PROCESS" 

                if self.end == False:
                    # write in a log file the decrypted message with a timestamp
                    f2str = sender+nextNode+destination_r+msgType+msgText
                    #f2.write(f2str+" "+timestamp+"\n")
                    f2.write(timestamp.strftime("%H")+":"+timestamp.strftime("%M")+":"+timestamp.strftime("%S")+" RSA DECRYPTION:"+f2str+"\n")

            
            # if the necxt recipient is the cansat and for the sender exists the symmetric key in the dictionary, then
            # decryption is performed using the hill algorithm
            if sender in self.cs_dict and self.cs_dict[sender][2] > 0:

                # differentiating the part of the list that starts from position 4 (in positions 0-3 are the sender and the nextNode)
                incomingMsg = inc[4:]
                incomingMsg = list(incomingMsg)

                # get the symmetric key from the dictionary
                incomingKey = []
                for i in str(self.cs_dict[sender][2]):
                    incomingKey.append(int(i))

                # and decrypt using that key
                incomingMsg = encryptS(incomingMsg, incomingKey)

                # save here the final recipient
                destination_r = str(incomingMsg[0] + incomingMsg[1])

                # save the type message (F for photo, TI for text or instruction)
                if destination_r == self.localAddress and sender == "GS":
                    msgType = "F"
                else:
                    msgType = "TI"

                # text message
                msgText = ""
                for i in incomingMsg[2:]: 
                    msgText = msgText + str(i)
                print(msgType +str('+')+ msgText)

                # the action changes only if the message has been decrypted
                action = "PROCESS" 

                if self.end == False: 
                    # write in a log file the decrypted message with a timestamp
                    f2str = sender+nextNode+destination_r+msgType+msgText 
                    #f2.write(f2str+" "+timestamp+"\n")
                    f2.write(timestamp.strftime("%H")+":"+timestamp.strftime("%M")+":"+timestamp.strftime("%S")+" HILL DECRYPTION:"+f2str+"\n")

        if action == "PROCESS":

            # Αν το μνμ είναι κανονικό μνμ χειραψίας, ενημερωνει
            # το λεξικό με το συμμετρικό κλειδί του αποστολέα
            # if msgType is Handshake (H), update the dictionary
            if msgType == "H":
                self.cs_dict[sender][2] = int(msgText)
                action = "END"
                print(self.cs_dict)
                
                if self.end == False:   
                    # wirte in a log file the action allong with a timestamp
                    f2str  = sender + " key: " + msgText
                    f2.write(timestamp.strftime("%H")+":"+timestamp.strftime("%M")+":"+timestamp.strftime("%S")+" HANDSHAKING:"+f2str+"\n")

            
            # if the message is for the cansat and the type is F, a photo is taken
            # the name of the photo file changes with the help of picCounter
            if msgType == "F":
                if self.counter>30:
                    camera.capture("/home/cansat/button_cansatPic"+str(self.picCounter)+".jpg")
                    pic_taken.append("/home/cansat/button_cansatPic"+str(self.picCounter)+".jpg")
                    self.picCounter = self.picCounter+1
                    
                    if self.end == False:   
					    # wirte in a log file the action allong with a timestamp
                        f2str  = "/home/cansat/button_cansatPic"+str(self.picCounter-1)+".jpg"
                        f2.write(timestamp.strftime("%H")+":"+timestamp.strftime("%M")+":"+timestamp.strftime("%S")+" CAMERA:"+f2str+"\n")


            # if the message for the cansat is of type "T" (text) or "I" (instructio),
            # promotes the message to the final recipient (if it has it's symmetric key), or 
            # to the Ground Station (if it doesn't have the symmetrci key)
            if msgType == "TI":

                if (destination_r != self.localAddress) and (destination_r in self.cs_dict):
                    if self.cs_dict[destination_r][2] > 0:
                        # it will be immidiately promoted to the final recipient
                        destination_s = destination_r
                        action = "FORWARD"
                    else:
                        # it will be promoted to GS
                        destination_s = "GS"
                        action = "FORWARD"
                elif (destination_r == self.localAddress) and (destination_r in self.cs_dict):
                    print("<---IotCtl---> I got a new mesage :" + msgText)
                    action = "END"												
                else:
                    action = "END"


        if action == "FORWARD":
            # we change the sender and the next recipient
            self.outgoing = []
            # sender
            self.outgoing.append(ord('C')) 
            self.outgoing.append(ord('S'))

            # next recipient
            self.outgoing.append(ord(destination_s[0])) 
            self.outgoing.append(ord(destination_s[1]))


            # we encrypt the rest of the message with the symmetric key of the next recipient
            # at first the rest of the message is added to the templist
            templist = []
            templist.append(destination_r[0])
            templist.append(destination_r[1])
            #for i in msgType:
                #templist.append(i)
            for i in msgText:  #einai mesa ksana apostoleas, msgType kai msgText
                templist.append(i)
            
            # write it in the lof file before encrypting
            if self.end == False:
                f2str = str(self.outgoing)+str(templist)
                f2.write(timestamp.strftime("%H")+":"+timestamp.strftime("%M")+":"+timestamp.strftime("%S")+" FORWARD:"+f2str+"\n")

            # we convert the symmetric key of the next recipient to a list 
            key = []
            for i in str(self.cs_dict[destination_s][2]):
                key.append(int(i))

            # symmetric encryption, produces a list
            templist = encryptS(templist, key)

            # add the encrypted part of the message to the outgoing list
            for item in templist:
                self.outgoing.append(ord(item))

            # εκτύπωση για να δούμε εμείς το μνμ
            print(self.outgoing)

            #if self.end == False:
            # εγγραφή του μνμ στο αρχείο με timestamp
            #    f2.write(str(self.outgoing)+" "+str(timestamp)+"\n")

            action = "END"

            # send the message
            self.write_payload(self.outgoing)
            self.set_mode(MODE.TX)
            self.clear_irq_flags(TxDone=1)
            #sleep(.5)

            self.outgoing = []




# ----------------------------------------- MAIN PROGRAM ----------------------------------------- #


#-----------------SETUP-----------------{
# create timestamp for the logfiles
#timestamp = str(datetime.datetime.now())
timestamp = datetime.datetime.now()

# create GPS object
uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=10)
gps = adafruit_gps.GPS(uart, debug=False)
gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
gps.send_command(b"PMTK220,1000")


# define GPIO pins that will be used for the button and buzzer
button = Button(5)
buzzer = Buzzer(20)

# prepare the bmp
try: #trial for bmp connection
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

# create object bmp280
# ATTENTION: the mode must be NORMAL_MODE and not the default
bus = SMBus(1)
bmp280 = BMP280(port=1, mode=BMP280.NORMAL_MODE, oversampling_p=BMP280.OVERSAMPLING_P_x16, oversampling_t=BMP280.OVERSAMPLING_T_x1,filter=BMP280.IIR_FILTER_OFF, standby=BMP280.T_STANDBY_1000)

# create object ina219
ina219 = INA219(addr=0x42)


# from the library for the LoRa setup
BOARD.setup()

# create lora object
lora = vspaceLORA(verbose=False)
lora.set_mode(MODE.STDBY)
#  Medium Range  Defaults after init are 434.0MHz, Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on 13 dBm
lora.set_pa_config(pa_select=1)

camera = PiCamera()
camera.resolution = (1280, 720)
camera.contrast = 10

# deactivate the buzzer
buzzer.off()


# send message "READY" 5 times to confirm communication
CS_READY = []
strREADY = "READY"
for i in strREADY:
     CS_READY.append(ord(i))

for i in range (0,5):
    # send meassage
     lora.write_payload(CS_READY)	
     lora.set_mode(MODE.TX)
     lora.clear_irq_flags(TxDone=1)
     sleep(1)
     print('stelnww ready')

lora.set_mode(MODE.SLEEP) #enters receive mode TODO place before sleep??


# the program freezes here until the wire is put in the cansat, which 
# simulates a button press. This happens in order to have enough time
# for the GPS to find fix
#button.wait_for_press()
while (button.is_pressed == False):
    gps.update()
    sleep(0.25)


# once the wire is inputted (with the folded parachute)
# send 5 more messages for confiramtion
CS_READY = []
strREADY = "GOODLUCK"
for i in strREADY:
     CS_READY.append(ord(i))
for i in range (0,5):
     lora.write_payload(CS_READY)	#send
     lora.set_mode(MODE.TX)
     lora.clear_irq_flags(TxDone=1)
     sleep(1)
     print('stelnww good luck')

lora.set_mode(MODE.SLEEP)

# get temperature from sensor
temperature = bmp280.read_temperature()		
pressure = bmp280.read_pressure()
groundPressure = 1013.25		


# the code fereezes here until the wire is taken out (which will happen only when the parachute opens
# so when the cansat comes out of the rocket) and which simulates the "unpressing" of a button
#button.wait_for_release()
while (button.is_pressed == True):
    gps.update()
    sleep(0.25)

pic_taken=[]

f1 = open("/home/cansat/first_mission0.txt", "w")
f2 = open("/home/cansat/sec_mission0.txt", "w")

# start normal function
print("Starting lora")
lora.start()

# close file
print("mission finished")

lora.set_mode(MODE.SLEEP)

try:
    
    # the MLP will run when the mission is finished, so that means after "start"
    # the weight are loaded in binary format
    hw = np.load("/home/cansat/unit_tests/CanSat/hw.npy")
    ow = np.load("/home/cansat/unit_tests/CanSat/ow.npy")
    hb = np.load("/home/cansat/unit_tests/CanSat/hb.npy")
    ob = 0.05550793

    print("NN load ok")

    # create file which wil write the prediction for each photo
    fnn = open("/home/cansat/NN_run_output.txt","w")

    # the prediction runs for each photo

    for pic in pic_taken:
        is_fire=run_nn(pic)
        fnn.write(pic+" "+str(is_fire))

        if is_fire>0.5:
            fnn.write("->Fire\n")
            print(pic+" ->Fire")
        else:
            fnn.write("->No fire\n")
            print(pic+" ->No fire")
except:
    print("Exception in NN")

fnn.close()

# activate buzzer
while True:
     buzzer.on()

     
    # in order for the GPS to send correct data (even if it loses fix at some point)
    # it needs many sequencial gps.update()
     sleep(0.25)
     gps.update()
     sleep(0.25)
     gps.update()
     sleep(0.25)
     gps.update()
     sleep(0.25)
     gps.update()
     buzzer.off()
     sleep(0.25)
     gps.update()
     sleep(0.25)
     gps.update()
     sleep(0.25)
     gps.update()
     sleep(0.25)
     gps.update()


     # send the values that ut took from the gps (help with finding it) 
     send_gps()

     # it will stop the while loop once it is found and
     # the wire is put back in place
     if button.is_pressed:
          break

#}
print('vgikaaaaaa')
# raspberry shutdown 
os.system("shutdown -h 0")
