from machine import Pin
import time

class Button:
    """
    Questa classe modella un bottone.
    Espone i metodi costruttore(n,mode,bounce_time), true_press() e set_handler(func).
    Dopo aver inizializzato un bottone, ricordati di settare l'handler. C'è un metodo apposito.
    """
    def __init__(self, n, mode, bounce_time):
        """
        Inizializza una nuova istanza.
        :parameter n           Il pin di ingresso.
        :parameter mode        Può asssumere due valori (+1 per la configurazione in pull up e -1 per la conf. in pull down)
        :parameter bounce_time Indica il tempo in ms sotto il quale una pressione del tasto è da ignorare
        """
        if(n<0 or n>39):
            self.__fatalError(1,n)
        elif(6<=n<=11):
            self.__fatalError(2,n)
        elif(34<=n<=39):
            print ("--- WARNING: i pin dal 34 al 39 non hanno le resistenze di pullup o pulldown. Mettile tu o cambia pin! ---")
        
        if (mode==+1):
            self.button=Pin(n, Pin.IN, Pin.PULL_UP)
        elif (mode==-1):
            self.button=Pin(n, Pin.IN, Pin.PULL_DOWN)
        else:
            self.__fatalError(3,mode)
        self.mode=mode
        if (bounce_time<0):
            self.__fatalError(4,bounce_time)
        self.last_press_time=-bounce_time
        self.bounce_time=bounce_time
            
        
    def __fatalError (self,err,arg):
        """PRIVATO. Arresta il sistema se succede qualcosa di inaspettato"""
        print("--- ERRORE ---")
        if (err==1):
            raise Exception(f"Il pin {arg} non è un pin valido!")
        elif (err==2):
            raise Exception(f"Il pin {arg} non è utilizzabile per i bottoni!")
        elif (err==3):
            raise Exception(f"L'argomento {arg} non è valido. Inserisci -1 o +1 per configurare il bottone in modalità pull up o pull down!")
        elif (err==4):
            raise Exception(f"Il tempo {arg} è negativo. Metti 0 o un numero positivo in ms!")
        elif (err==5):
            raise Exception(f"L'evento {arg} non è valido. Metti 1,10 o 11!")

        
    def true_press (self):
        """
        Da chiamare ogni volta che il bottone viene premuto.
        :return un booleano per confermare che la pressione di un tasto non sia conseguenza del bouncing.	
        """
        current_time=time.ticks_ms()
        delay = time.ticks_diff(current_time, self.last_press_time)
        self.last_press_time=current_time
        if (delay>self.bounce_time):
            return True
        else:
            return False
            
    def set_handler (self, func, event):
        """
        Associa una funzione handler alla pressione del bottone
        :parameter func           La funzione che opera da handler
        :parameter event           L'evento che chiama l'handler (10= press, 1=release, 11= press e release)
        """
        if(event not in (10,11,1)):
            self.__fatalError(5,event)
        
        if(event==11):
            self.button.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler = func)
        elif(self.mode==1):
            if(event==10):
                self.button.irq(trigger=Pin.IRQ_FALLING, handler = func)
            else:
                self.button.irq(trigger=Pin.IRQ_RISING, handler=func)
        else:
            if(event==10):
                self.button.irq(trigger=Pin.IRQ_RISING, handler=func)
            else:
                self.button.irq(trigger=Pin.IRQ_FALLING, handler = func)
              



