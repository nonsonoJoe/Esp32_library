from machine import Pin, PWM
class PuWM:
    """
    @brief Questa classe modella un led o qualsiasi componente controllato con la PWM (pulse width modulation).
    @details Espone i metodi costruttore(n,f), set_duty(d), set_freq(f), get_duty()
    """
    PWM_PINS = (0, 1, 2, 3, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33)
    STRAPPING_PINS = (0,2,5,12,15)
    REPL_PINS = (1,3)

    def __init__(self, n, f=5000):
        """
        @brief Inizializza una nuova istanza.
        @param  n Il pin che va connesso al componente da controllare.
        @param  f Il valore della frequenza
        """
        self.__check_freq(f)
        self.__pwm=PWM(Pin(self.__check_pin(n)))
        self.set_duty(0)
        self.set_freq(f)#chiamata a __check_freq() ulteriore.

    def __check_pin(self,p):
        """
        @brief Valuta la correttezza del pin.
        @param  p Il pin che va connesso al componente da controllare.
        @return Il valore di p. Può sollevare eccezioni
        """
        if p not in self.PWM_PINS:
            raise ValueError(f"Il pin {p} non è un pin valido, usa uno dei pin {self.PWM_PINS}!")
        if p in self.STRAPPING_PINS:
            print(f"Il pin {p} è corretto ma è anche un pin di boot. Assicurati di non averli forzati a un certo valore all'avvio!")
        if p in self.REPL_PINS:
            print(f"Il pin {p} è corretto ma potrebbe disturbare la console. Se qualcosa va storto evita i pin {self.REPL_PINS}!")
        return p
    
    def __check_duty(self,d):
        if not isinstance(d, int):
            raise TypeError("Il duty deve essere un intero")
        if d<0 or d>1023:
            raise ValueError(f"Non puoi settare il duty a {d}!")
        return d
    
    def __check_freq(self,f):
        if not isinstance(f, int):
            raise TypeError("La frequenza deve essere un intero")
        if f>5000 or f<1: #meglio non gestire f=0 modificando il duty, principio del least surprise
            raise ValueError(f"Non puoi settare la frequenza a {f}!")
        return f
                    
    def set_duty(self,d):
        """
        @brief Setta una nuova duty.
        @param  d La nuova percentuale di tempo alto (espressa da 0 a 1023)
        @throws ValueError Se d è fuori range.
        @throws TypeError Se d non è un intero.
        """
        new_duty = self.__check_duty(d)
        self.__pwm.duty(new_duty)
        self.__duty=new_duty
        
    def get_duty(self):
        """
        @brief Getter del duty cycle.
        @return Il duty cycle (espresso come intero da 0 a 1023)
        """
        return self.__duty
        
    def set_freq(self,f):
        """
        @brief Setta una nuova frequenza.
        @param  f La nuova frequenza (come valore da 1 a 5000)
        """
        new_freq=self.__check_freq(f)
        self.__pwm.freq(new_freq)
        self.__freq=new_freq
    
    def get_freq(self):
        return self.__freq
    
    def deinit(self):
        """
        @brief Libera il canale PWM e il pin.
        @details Questa chiamata rende l'oggetto inutilizzabile
        """
        self.__pwm.deinit()
