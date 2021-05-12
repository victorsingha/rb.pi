import time
import serial
import RPi.GPIO as GPIO
import spidev
import os

from time import sleep
from array import array

#import IoTSend
import numpy
import http.client
import urllib.request, urllib.parse, urllib.error

import pygame
import picamera

print("Libraries Updated")

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

Water_key1 = 37
Help_key2 = 38
IR_Obstacle = 16
Motor_1 = 13
Motor_2 = 15

GPIO.setup(Water_key1, GPIO.IN)
GPIO.setup(Help_key2, GPIO.IN )
GPIO.setup(IR_Obstacle, GPIO.IN)

GPIO.setup(Motor_1, GPIO.OUT)
GPIO.setup(Motor_2, GPIO.OUT)

print("Port Initialized")

usbport = '/dev/ttyS0'
ser_UART = serial.Serial(usbport, 9600)

UART_Rx_Str = ""
Drug_Alarm_Flag = 0

print("Motor Anti Clock - Open")
GPIO.output(Motor_1, False)
GPIO.output(Motor_2, True)
sleep(0.5)
GPIO.output(Motor_1, False)
GPIO.output(Motor_2, False)
sleep(0.5)

print("Motor Clock - Close")
GPIO.output(Motor_1, True)
GPIO.output(Motor_2, False)
sleep(0.5)
GPIO.output(Motor_1, False)
GPIO.output(Motor_2, False)
sleep(0.5)

pygame.mixer.init()
pygame.mixer.music.load('water.mp3')
print("Water Sound Play")
pygame.mixer.music.play()
sleep(10)
pygame.mixer.music.stop()
print("Water Sound Stop")

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

# Function to read SPI data from MCP3008 chip
# Channel must be an integer 0-7
def ReadChannel(channel):
  adc = spi.xfer2([1,(8+channel)<<4,0])
  data = ((adc[1]&3) << 8) + adc[2]
  return data
 
# Function to convert data to voltage level,
# rounded to specified number of decimal places.
def ConvertVolts(data,places):
  volts = (data * 3.3) / float(1023)
  volts = round(volts,places)
  volts=(int)(volts * 100)
  return volts

print("start camera")
camera = picamera.PiCamera()
camera.start_preview()
sleep(5)
camera.stop_preview()
sleep(0.5)
print("stop Camera")

camera.vflip = True
camera.hflip = True
camera.brightness = 60

print("capturing image")
for i in range(0,2):
    camera.capture('img%02d.jpg' % i, resize=(500,281))
    sleep(2)
    
print("capturing image done")

line = ""
GSM_Tx_Arr = ""
Drug = 0
Position = "0"

def GSM_Send_SMS( Mobile, SMS ):
    ser_UART.write(str.encode("AT+CMGS=\""))
    ser_UART.write(str.encode(Mobile))
    ser_UART.write(str.encode("\"\r"))
    sleep( 2 )
    ser_UART.write(str.encode(SMS))
    ser_UART.write(str.encode("\x1A"))
    sleep( 4 )

ser_UART.write(str.encode("AT\r"))
sleep(3)
ser_UART.flushInput()
print("GSM INITIALIZED")
      
GSM_Send_SMS( "7353028027", "SYSTEM START" )
sleep(6)
ser_UART.flushInput()
print ("TEST SMS SENT")

key ='ETJSOVHNJH52ZVX9'  # Thingspeak channel to update 3HEXXTITMR9I5I9   JRAI9MM3TER6F8P
# ----------------------------------------------------------------------
def send_IoTData(field1,field2,field3):
    try:
        params = urllib.parse.urlencode({'field1': field1, 'field2': field2, 'field3': field3, 'key':key })
        headers = {"Content-typZZe": "application/x-www-form-urlencoded","Accept": "text/plain"}
        conn = http.client.HTTPConnection("api.thingspeak.com:80")

        conn.request("POST", "/update", params, headers)
        response = conn.getresponse()
        print((response.status, response.reason))
        data = response.read()
        conn.close()
    except:
        return
    
def send_IoTDataField1(field1):
    try:
        params = urllib.parse.urlencode({'field1': field1, 'key':key })
        headers = {"Content-typZZe": "application/x-www-form-urlencoded","Accept": "text/plain"}
        conn = http.client.HTTPConnection("api.thingspeak.com:80")

        conn.request("POST", "/update", params, headers)
        response = conn.getresponse()
        print((response.status, response.reason))
        data = response.read()
        conn.close()
    except:
        return

def send_IoTDataField2(field2):
    print("in Func")
    try:
        print("in try")
        params = urllib.parse.urlencode({'field2': field2, 'key':key })
        headers = {"Content-typZZe": "application/x-www-form-urlencoded","Accept": "text/plain"}
        conn = http.client.HTTPConnection("api.thingspeak.com:80")
        conn.request("POST", "/update", params, headers)
        response = conn.getresponse()
        print((response.status, response.reason))
        data = response.read()
        conn.close()
    except:
        print("exception caught")
        return

Time_Count = 0
Drug_Alarm_Flag = 0
while True:
    print("------------------------")
    sleep(0.2)
    Time_Count = Time_Count + 1

    if( GPIO.input(Water_key1) == True ):
        print("WATER")
        pygame.mixer.init()
        pygame.mixer.music.load('water.mp3')
        print("Water Sound Play")
        pygame.mixer.music.play()
        sleep(10)
        pygame.mixer.music.stop()
        print("Water Sound Stop")

    if( GPIO.input(Help_key2) == True ):
        print("HELP")
        pygame.mixer.init()
        pygame.mixer.music.load('help.mp3')
        print("Help Sound Play")
        pygame.mixer.music.play()
        sleep(10)
        pygame.mixer.music.stop()
        print("Help Sound Stop")

    # Read chan 0
#     temp_level = ReadChannel(0)
#     temp_volts = ConvertVolts(temp_level,2)
#     print(temp_volts)
#     sleep(1)
#     send_IoTDataField1(temp_volts)
#     if( (temp_volts >= 40 ) ):
#         print("HIGH TEMPERATURE")
#         sleep(2)

    temp_level = ReadChannel(0)
    temp_volts = ConvertVolts(temp_level,2)
    print ("temperature Value")
    print (temp_volts)
    sleep(2)
    send_IoTDataField1(temp_volts)
    if( temp_volts > 40):
        print ("high temperature")
        sleep(2)
        GSM_Send_SMS( "7353028027", "HIGH TEMPERATURE" )
        sleep(6)
        ser_UART.flushInput()
        print("SMS SENT")
      
    print("Time = ", Time_Count)
    if( Time_Count == 5 ):
        Motor_Flag = 1

    sleep(1)
    if( (Time_Count >= 5) and (Time_Count <= 10) and (Drug == 0) ):
        print("Medicine Time")
        sleep(1)
        if( Motor_Flag == 1 ):
            Motor_Flag = 0
            print("Motor Anti Clock - Open")
            GPIO.output(Motor_1, False)
            GPIO.output(Motor_2, True)
            sleep(0.5)
            GPIO.output(Motor_1, False)
            GPIO.output(Motor_2, False)
            sleep(0.5)

        if(GPIO.input(IR_Obstacle) == False):
            print("Medicine Consumed")
            Drug = 1
            sleep(1)
            print("Motor Clock - Close")
            GPIO.output(Motor_1, True)
            GPIO.output(Motor_2, False)
            sleep(0.5)
            GPIO.output(Motor_1, False)
            GPIO.output(Motor_2, False)
            sleep(0.5)

    elif( (Time_Count == 11) and (Drug == 0) ):
        print("Medicine not Consumed")
        Drug = 0
        sleep(1)
        GSM_Send_SMS( "7353028027", "Medicine not Consumed " )
        sleep(6)
        print("Motor Clock - Close")
        GPIO.output(Motor_1, True)
        GPIO.output(Motor_2, False)
        sleep(0.5)
        GPIO.output(Motor_1, False)
        GPIO.output(Motor_2, False)
        sleep(0.5)
        GSM_Send_SMS( "7353028027", "HIGH TEMPERATURE" )
        sleep(6)
        ser_UART.flushInput()
        print("SMS SENT")
        
        
