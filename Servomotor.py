from PuWM import PuWM
class Servomotor:
    """
    Questa classe modella un servomotore.
    Espone i metodi costruttore(n,f), set_duty(d), set_angle(a), rilascia()
    Ricordati di importare PuWM e che marrone=massa, rosso=5V, giallo=pin dell'esp
    """
    def __init__(self,n):
        """
        Inizializza una nuova istanza, non forza un angolo sul servomotore.
        :parameter n Il pin che va connesso al componente da controllare.
        """
        self.pwm=PuWM(n,50)
        
    def set_duty(self,d):
        """
        Forza un preciso angolo del servomotore basato sul duty cycle
        :parameter d Il duty cycle, limitato al range [26,128].
        """
        self.pwm.set_duty(self.__check_duty(d))
        
    def __check_duty(self,d):
        """
        PRIVATO.Controlla se il valore di duty è accettabile per un servomotore.
        :parameter d Il duty cycle, limitato al range [26,128].
        :return il duty cycle. Può lanciare eccezioni.
        """
        if(d<26 or d>128):
            raise Exception(f"Non puoi settare il duty cycle del servomotore a {d}. Usa un intero tra 26 e 128!")
        return d
    
    def set_angle(self,a):
        """
        Forza un preciso angolo del servomotore
        :parameter a L'ampiezza dell'angolo in gradi, limitato all'intervallo [0°,180°].
        La formula è l'approssimazione lineare del duty a 0°(=26) e a 180°(=128)
        """
        self.pwm.set_duty(int(26+(102/180)*self.__check_angle(a)))
        
    def __check_angle(self,a):
        """
        PRIVATO.Controlla l'angolo forzato è un valore accettabile.
        :parameter a l'angolo, limitato all'intervallo [0°,180°].
        :return a. Può lanciare eccezioni.
        """
        if(a<0 or a>180):
            raise Exception(f"Non puoi settare l'angolo del servomotore a {a}. Usa un intero tra 0 e 180!")
        return a
    
    def rilascia(self):
        """
        Costringe il servomotore a non forzare più un angolo
        """
        self.pwm.set_duty(0)