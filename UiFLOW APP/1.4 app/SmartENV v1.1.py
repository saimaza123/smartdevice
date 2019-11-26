#Smart device test code based on weather station demo
# version 2.2, added LCD BK light control, 2019.7.17
# version 2.03, added I2C detection,CPU T altitude calculation compensation, 2019.7.8
# version 1.02, added run cnt, altitude calculation,, 2019.7.2
#Author ling zhou, last edit 26.06.2019
#ENV Unit:集成DHT12(环境温湿度传感器)和压强传感器BMP280; Address: 0x5C, 0x76
#T范围: 20 ~ 60℃, ±0.2
#H范围: 20 ~ 95℃  0.1%
#A范围: 300 ~ 1100hPa

from micropython import const
import gc
from m5stack import *
from m5ui import *
from uiflow import *
import  unit 
import  machine
from mstate import *
import i2c_bus
import esp32
import network
from utime import sleep_ms
import math




#machine.freq(160000000)  bugs!
IIC_Address_ENV = 0x5C
LED_EN = 0
CPU_freq=machine.freq()/1000000



BH1750_add = 0x23

class BH1750():

    """Micropython BH1750 ambient light sensor driver."""
     


    PWR_OFF = 0x00

    PWR_ON = 0x01

    RESET = 0x07



    # modes

    CONT_LOWRES = 0x13

    CONT_HIRES_1 = 0x10

    CONT_HIRES_2 = 0x11

    ONCE_HIRES_1 = 0x20

    ONCE_HIRES_2 = 0x21

    ONCE_LOWRES = 0x23



    # default addr=0x23 if addr pin floating or pulled to ground

    # addr=0x5c if addr pin pulled high
    # private function start with __
    def __init__(self, bus, addr=0x23):

        self.bus = bus

        self.addr = addr

        self.off()

        self.reset()



    def off(self):

        """Turn sensor off."""

        self.set_mode(self.PWR_OFF)



    def on(self):

        """Turn sensor on."""

        self.set_mode(self.PWR_ON)



    def reset(self):

        """Reset sensor, turn on first if required."""

        self.on()

        self.set_mode(self.RESET)



    def set_mode(self, mode):

        """Set sensor mode."""

        self.mode = mode

        self.bus.writeto(self.addr, bytes([self.mode]))



    def luminance(self, mode):

        """Sample luminance (in lux), using specified sensor mode."""

        # continuous modes

        if mode & 0x10 and mode != self.mode:

            self.set_mode(mode)

        # one shot modes

        if mode & 0x20:

            self.set_mode(mode)  #iic write occurs

        # earlier measurements return previous reading

        sleep_ms(24 if mode in (0x13, 0x23) else 180)

        data = self.bus.readfrom(self.addr, 2)

        factor = 2.0 if mode in (0x11, 0x21) else 1.0

        return (data[0]<<8 | data[1]) / (1.2 * factor)




#toggle RGB led
def buttonC_wasPressed():
  # global params
  global LED_EN
  speaker.tone(446, 120, 1)
  LED_EN =1 -LED_EN
  if LED_EN==0:
     rgb.setBrightness(0)
  wait(0.1)
  pass

#Btn B: DISPLAY BK light control
def buttonB_wasPressed():
  # global params
  global LCD_EN
  speaker.tone(646, 120, 1)
  LCD_EN = LCD_EN-1
  if LCD_EN < 0:
     LCD_EN = 20
  wait(0.1)
  pass

def buttonA_wasPressed():
  # global params
  speaker.tone(860, 120, 1)
  LCD_EN = 0
  wait(0.1)
  pass


setScreenColor(0x000000)
lcd.setBrightness(25)
#lcd.image(lcd.CENTER, lcd.CENTER, 'img/combitac_logo_b.jpg')
#time.sleep(1) 
lcd.image(lcd.CENTER, lcd.CENTER, 'res/SmartENV_logo.jpg')
#lcd.image(lcd.CENTER, lcd.CENTER, 'res/SmartENV_logo.jpg')

#time.sleep(1) 
#lcd.image(lcd.CENTER, lcd.CENTER, 'image_app/p2.jpg')
#lcd.image(lcd.CENTER, lcd.CENTER, 'image_app/ghost_in_the_shell.jpg')
#lcd.image(lcd.CENTER, lcd.CENTER, 'res/error.jpg')
time.sleep(1) 
#wait(1) #OK!
setScreenColor(0x1111111)

#lcd.image(lcd.CENTER, lcd.CENTER, 'img/dot.jpg')
#time.sleep(0.5)


#save some power
wlan = network.WLAN(network.STA_IF) # create station interface
wlan.active(False) 

LCD_EN = 10
title = M5Title(title="   Smart Device demo Zell 2019 v1", x=3 , fgcolor=0xff9900, bgcolor=0x1F1F1F)
circle4 = M5Circle(250, 50, 19, 0x1111111, 0x1111111)#sun
circle_T = M5Circle(308, 92, 3, 0xFFFF00, 0x1111111)#degree
circle_T.setBorderColor(0xFFFF00)
circle_T.setBgColor(0x1111111)
label0 = M5TextBox(20, 30, "Enviroment sensors 4in1", lcd.FONT_Default,0xAFFFFF, rotate=0)
#label0 = M5TextBox(176, 100, "Temp:", lcd.FONT_Default,0xFFFF00, rotate=0)
label1 = M5TextBox(150, 130, "Air P:", lcd.FONT_DejaVu18,0xAAFFFF, rotate=0)
label1B = M5TextBox(150, 160, "Alt.:", lcd.FONT_DejaVu18,0xAAFFBB, rotate=0)
label_lux1 = M5TextBox(70, 160, "Lux", lcd.FONT_DejaVu18,0xFEFE33, rotate=0)
#label11 = M5TextBox(280 163, "hpa", lcd.FONT_Default,0xAAFFFF, rotate=0)  #bug??
#label2 = M5TextBox(20, 90, "Hum:", lcd.FONT_Default,0xAAAAFF, rotate=0)
#label_light = M5TextBox(20, 110, "Light:", lcd.FONT_DejaVu18,0xFEFEFE, rotate=0)
lcd.image(10, 60, 'res/Hum.jpg')
lcd.image(0, 115, 'res/light_s.jpg')
image_T_icon = M5Img(172, 56, "res/T_symbol_64.jpg", True)
#values from sensors
label3 = M5TextBox(220, 85, "T", lcd.FONT_Comic,0xFFFF00, rotate=0)
label4 = M5TextBox(210, 125, "A", lcd.FONT_DejaVu24,0xAAFFFF, rotate=0)
label_alt = M5TextBox(210, 155, "Al", lcd.FONT_DejaVu24,0xAAFFBB, rotate=0)
label5 = M5TextBox(70, 85, "H", lcd.FONT_Comic,0xAAAAFF, rotate=0)
label_lux = M5TextBox(50, 135, "Lux_val", lcd.FONT_DejaVu24,0xFEFEFE, rotate=0)

#Vb values
label6 = M5TextBox(20, 220, "Text", lcd.FONT_Default,0xFFFFAA, rotate=0)
label_data_T_CPU = M5TextBox(125, 220, "T_CPU:", lcd.FONT_Default,0xAFCFFF, rotate=0)
label_cnt = M5TextBox(220, 220, "CNT: ", lcd.FONT_Default,0xFFEEBB, rotate=0)
label_sys = M5TextBox(20, 200, "sys: ", lcd.FONT_Default,0xF0EEAA, rotate=0)
label_sys.setText("Free HEAP: "+str(gc.mem_free())+" B" )
label_CPU = M5TextBox(176, 200, "CPU:", lcd.FONT_Default,0xAAAAFF, rotate=0)
label_CPU_S = M5TextBox(218, 200, "CPU:", lcd.FONT_Default,0xAAAAFF, rotate=0)
label_CPU_S.setText(str(CPU_freq)+"MHz" )
# ------------- I2C -------------
i2c = i2c_bus.get(i2c_bus.M_BUS)
#If an error is encountered, a try block code execution is stopped and transferred down to the except block. 
#The code in the finally block will be executed regardless of whether an exception occurs.
try:
            env0 = unit.get(unit.ENV, unit.PORTA)
            lcd.print("%.1f" % env.temperature+"'C", 210, 120)
            lcd.print("%.1f" % env.humidity+"%",     210, 138)
            lcd.print("%.1f" % env.pressure+"Pa",     208, 156)
except:
            label3.setText("N.A. ")
            ENV_insert = 1
            while ENV_insert:
               if i2c.is_ready(IIC_Address_ENV):
                ENV_insert =0
                env0 = unit.get(unit.ENV, unit.PORTA)
               wait_ms(200) 
            pass

# light
iic_a = i2c_bus.get(i2c_bus.PORTA)
BH =BH1750(iic_a)
try:   
    BH_data=BH.luminance(BH1750.ONCE_HIRES_1)
except:
    label_lux.setText("Light: N.A.")
    pass




run_cnt = 0
#dac = machine.DAC(25)
adc = machine.ADC(35) 
#------------ADC V akku G35
adc.atten(adc.ATTN_11DB)
#adc.width(WIDTH_10BIT)
import random

random2 = None
i = None
#--------cloud??
#m5cloud = M5Cloud()

# gc.collect()

# Why this work error, look run error..........
# gc.threshold(1000)

#m5cloud.run(thread=False)

while True:
  
  #------------ADC V akku G34
 #adc = machine.ADC(35)
# Per design the ADC reference voltage is 1100mV, however the true reference voltage can range from 1000mV to 1200mV amongst different ESP32s
  # value: ATTN_0DB (range 0 ~ 1.1V)
#        ATTN_2_5DB (range 0 ~ 1.5V)
#        ATTN_6DB (range 0 ~ 2.5V)
#        ATTN_11DB (range 0 ~ 3.9V)  11db==> Vi/Vo = 3.548, 1.1V*3.548=3.9
 #adc.atten(adc.ATTN_9DB)  11: 1 dB, 10: 6 dB, 01: 3 dB, 00: 0 dB,
# value: WIDTH_9BIT - capture width is 9Bit
#        WIDTH_10BIT - capture width is 10Bit
#        WIDTH_11BIT - capture width is 11Bit
#        WIDTH_12BIT - capture width is 12Bit
#adc.width( WIDTH_12BIT)
# Read the ADC value as voltage (in mV)
  if btnC.isPressed():
    buttonC_wasPressed() 
  if btnB.isPressed():
    buttonB_wasPressed() 
  if btnA.isPressed():
    buttonA_wasPressed() 

  lcd.setBrightness(LCD_EN)

  
  try:   
           BH_data=BH.luminance(BH1750.ONCE_HIRES_1)
           #label_lux.setText(str("%.1f" % BH_data)+"lux") 
           if (BH_data<1000):
              label_lux.setText("  "+str("%.1f" % BH_data)) 
           else:
              label_lux.setText(str("%.0f" % BH_data)) 
  except:
           pass







  Vb_data = adc.readraw()
  ratio =2
  Vb= Vb_data/4096*1.05*3.55*ratio
  Vb="%.3f" % Vb
  #Vb= Vb_data/4096*2.5
  label6.setText("Akku: "+str(Vb)+"V")
  #label6.setText(str(Vb_data)+" :"+str(Vb)+"V")
 #obj['adc'] = adc
  label3.setText(str(env0.temperature))
  #label3.setText(str(env0.temperature)+" '")
  #label4.setText("%.1f" % env0.pressure+" hpa")
  label4.setText("%.1f" % env0.pressure)
  Altitude = 8.5*(1013.25-env0.pressure) # in meter @ 25 degree
  Altitude = Altitude + (env0.temperature-22)*0.2273# compensation for temperature, 
  #https://www.mide.com/pages/air-pressure-at-altitude-calculator
  label_alt.setText("%.1f" % Altitude+" M")
  label5.setText("%.1f" % (env0.humidity)+" %")
  wait(0.1)
  if (env0.humidity) >= 55:
        #---------------breath RGB LED based on humidity and temperature
    #humidity: left rgb leds
    if (LED_EN):
     R = 11
     G = 55
     B = int (100+ 2*(env0.humidity-50))
    #temp right leds
    #Rt = int (env0.temperature/50*255)
     Rt = int (100+ 20*(env0.temperature-20))
     if Rt>255:
      Rt=255
     Gt = 55
     Bt = 0
     for i in range(10, 180, 10):
      rgb.setColorFrom(6 , 10 ,(R << 16) | (G << 8) | B)
      rgb.setColorFrom(1 , 5 ,(Rt << 16) | (Gt << 8) | Bt)
      rgb.setBrightness(i)
      wait_ms(1)
     for i in range(180, 10, -10):
      rgb.setColorFrom(6 , 10 ,(R << 16) | (G << 8) | B)
      rgb.setColorFrom(1 , 5 ,(Rt << 16) | (Gt << 8) | Bt)
      rgb.setBrightness(i)
      wait_ms(10)
     #fade time step
  else: #sunny


    #rgb.setColorAll(0xff6600)
        #---------------breath RGB LED based on humidity and temperature
    #humidity: left rgb leds
    if (LED_EN):
     R = 11
     G = 55
     B = int (100+ 2*(env0.humidity-50))
     #temp right leds
     #Rt = int (env0.temperature/50*255)
     Rt = int (100+ 20*(env0.temperature-20))
     if Rt>255:
       Rt=255
     Gt = 55
     Bt = 0
     for i in range(10, 180, 10):
      rgb.setColorFrom(6 , 10 ,(R << 16) | (G << 8) | B)
      rgb.setColorFrom(1 , 5 ,(Rt << 16) | (Gt << 8) | Bt)
      rgb.setBrightness(i)
      wait_ms(1)
     for i in range(180, 10, -10):
      rgb.setColorFrom(6 , 10 ,(R << 16) | (G << 8) | B)
      rgb.setColorFrom(1 , 5 ,(Rt << 16) | (Gt << 8) | Bt)
      rgb.setBrightness(i)
      wait_ms(10)
     #fade time step


    lcd.circle(250, 51, 30, color=0x221100)
  tmp_str= str ("%.1f" % ((esp32.raw_temperature() -32)/1.8))
  label_data_T_CPU.setText("T_CPU: "+tmp_str )
  run_cnt = run_cnt+1
  label_cnt.setText("Run: "+str(run_cnt) )  
  label_sys.setText("Free HEAP: "+str(gc.mem_free())+" B" )
  label_CPU_S.setText(str(CPU_freq)+"MHz" )
  wait_ms(50)



