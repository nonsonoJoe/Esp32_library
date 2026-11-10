from PuWM import PuWM
class DimmableLed:
    """
    Questa classe modella un led dimmerabile.
    Espone i metodi costruttore(n,f), set_duty(d), set_angle(a), rilascia()
    Ricordati di importare PuWM e di collegare un resistore al led.
    """
    def __init__(self,n):
        """
        Inizializza una nuova istanza, forza il led a essere spento.
        :parameter n Il pin che va connesso al lato positivo del led.
        """
        self.pwm=PuWM(n,5000)
        
    def set_duty(self,d):
        """
        Forza una precisa luminosità del led.
        :parameter d Il duty cycle, un numero nell'intervallo [0,1023].
        """
        self.pwm.set_duty(d)
        
    
    def set_lum_perc(self,p):
        """
        Forza una precisa luminosità percentuale del led.
        :parameter p un numero nell'intervallo [0,100].
        """
        self.pwm.set_duty(int(1023/100*self.__check_perc(p)))
        
    def __check_perc(self,p):
        """
        PRIVATO.Controlla che la percentuale sia un valore accettabile.
        :parameter p la percentuale, limitata all'intervallo [0,100].
        :return p. Può lanciare eccezioni.
        """
        if(p<0 or p>100):
            raise Exception(f"Non puoi settare la luminosità del led al {p}%. Usa un numero tra 0 e 100!")
        return p
    
    def on(self):
        """
        Accende il led al massimo della luminosità
        """
        self.pwm.set_duty(1023)
        
        
    def off(self):
        """
        Spegne il led.
        """
        self.pwm.set_duty(0)
        