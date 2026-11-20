from machine import Pin, I2C
import ssd1306
import framebuf
import time

#risoluzione del display OLED: 128x64 pixel
WIDTH = 128
HEIGHT = 64
SCL_PIN = 22
SDA_PIN = 21

#inizializzo l'interfaccia ic2
#0 indica che vuoi usare il bus I2C numero 0.
#1 indica che vuoi usare il bus I2C numero 1.
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
display = ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)

class Display:
    """!
    @brief Questa classe modella un led collegato a un pin dell'ESP32.

    @details Espone il costruttore Led(n) e i metodi on(), off(), toggle(), load(), stop()
    e async_execute(). Un led appena inizializzato è sempre spento.
    Il led può essere comandato in due modi: direttamente con on(), off() e toggle(),
    oppure caricando un comportamento con load() ed eseguendolo in modo non bloccante
    chiamando async_execute() a intervalli brevi e regolari nel loop principale.
    Se on(), off() o toggle() vengono chiamati mentre una sequenza è in corso, alla prima
    chiamata di async_execute() il led torna al valore del passo corrente. Per dare la
    precedenza al comando manuale bisogna chiamare prima stop() o load().
    """
    def __init__(self):
        pass

    def aggiornamento_schermo(display):
    global lum_registrata, ldr_lum
    
    if round(ldr_lum)!=lum_registrata:
        lum_registrata= round(ldr_lum)
        display.fill_rect(0,0,128,64,0)
        display.text("{:2.2f}".format(ldr_lum), 40, 20,1)
        display.show()

    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
    display = ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)
    display.text("Smarterra", 0, 0,1)
    display.rect(0, 10, 128, 1, 1)

    
    
    def aggiorna_schermo(display):
    global ldr_lum,temperatura,umidita,causa, angolo_ventilazione, target_step
    global auto1
    lum_registrata= round(ldr_lum)
    display.fill_rect(0,12,128,64,0)
    display.text("TEMP:{:2.2f}C".format(temperatura), 0, 12,1)
    display.text("UMID:{:2.0f}%".format(umidita), 0, 20,1)
    display.text("LUCE:{:2.0f}%".format(ldr_lum), 0, 28,1)
    if angolo_ventilazione==0:
        vent="APERTA"
    else:
        vent="CHIUSA"
    display.text(f"VENT:{vent}", 0, 36,1)
    if target_step==0:
        tent="APERTA"
    else:
        tent="CHIUSA"
    display.text(f"TENDA:{tent}", 0, 44,1)


    #display.fill_rect(70,0,50,9,0)
    if causa==0:
        c="SISTEMA OK"
    elif causa==1:
        c="ALLARME UMID"
    elif causa==2:
        c="ALLARME TEMP"
    elif causa==3:
        c="ALLARME TEMP + UMID"
    display.text(f"{c}", 0, 52,1)
    
    if auto1:
        mode="AUTO"
    else:
        mode="MANUAL"
    if causa!=0:
        mode="ALARM"
    display.fill_rect(0,80,60,8,0)
    display.text(f"{mode}", 80, 0,1)
    display.show()

    def clear():
    # schermo bianco
    display.fill(0)
    display.show()


display.fill(1)                         # fill entire screen with white colour

display.rect(10, 10, 107, 43, 0)        # draw a rectangle outline 10,10 to width=107, height=53, colour=1 (black)
display.show()
time.sleep(1)
# draw battery percentage
# x_pos coordinate orizzontali dei blocchi che riempiono la batteria
# percentages: valori percentuali da mostrare (25%, 50%, 75%, 100%).
x_pos = [12, 25, 38, 51, 64, 77, 90,103]
percentages = [.12,.25,.37, .50,.62, .75,.87, 1.0]
while True:
    #Cicla 4 volte per simulare la carica crescente.
    for ctr in range(8):
        #fill_rect: disegna un blocco pieno all’interno del rettangolo batteria.
        display.fill_rect(x_pos[ctr],11,12,40,0)
        display.fill_rect(0,56,128,40,1)
        #text(...): mostra la percentuale (es. "25%").
        display.text("{:.0%}".format(percentages[ctr]), 11, 56,0)
        #show(): aggiorna il display.
        display.show()
        time.sleep_ms(1000)
    
    # This will clear the battery charge percentage 
    for ctr in range(8):
        display.fill_rect(x_pos[ctr],11,12,40,1)
        
    display.show()

    for image in images_list:
            buffer = image
    
            fb = framebuf.FrameBuffer(buffer, 128, 64, framebuf.MONO_HLSB)
            display.fill(0)
            display.blit(fb, 8, 0)
    
            display.show()
            utime.sleep_ms(2000)

