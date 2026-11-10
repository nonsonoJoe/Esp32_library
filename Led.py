from machine import Pin
class Led:
    """ 
    Questa classe gestisce un led.
    Espone i metodi costruttore(n), on(), off() e toggle().
    Dopo che hai inzializzato il led, ricordati di forzarlo a uno stato iniziale
    """
    def __init__(self, n):
        """
        Inizializza una nuova istanza.
        :parameter n    Il pin da associare al controllo del led.
        """
        if(n<0 or n>39):
            self.__fatalError(1,n)
        elif(6<=n<=11 or 34<=n<=39):
            self.__fatalError(2,n)
        self.led=Pin(n, Pin.OUT)
        
    def __fatalError (self,err,arg):
        """PRIVATO. Arresta il sistema se succede qualcosa di inaspettato"""
        print("--- ERRORE ---")
        if (err==1):
            raise Exception(f"Il pin {arg} non è un pin valido!")
        elif (err==2):
            raise Exception(f"Il pin {arg} non è utilizzabile per i led!")
        
        
    def on (self):
        """
        Accende il led.
        """
        self.led.value(1)
        
    def off (self):
        """
        Spegne il led
        """
        self.led.value(0)
        
    def toggle (self):
        """
        Commuta il led
        """
        self.led.value(not self.led.value())


