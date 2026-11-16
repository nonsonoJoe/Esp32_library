from PuWM import PuWM
from Sequenziatore import Sequenziatore
class DimmableLed:
    """!
    @brief Questa classe modella un led dimmerabile, cioè con luminosità regolabile in PWM.
    
    @details Espone il costruttore DimmableLed(n) e i metodi set_duty(), set_lum_perc(), on(), off(),
    load(), stop(), async_execute() e il metodo statico rampa().
    Il led può essere comandato direttamente oppure caricando una sequenza di luminosità
    con load() ed eseguendola in modo non bloccante chiamando async_execute()
    a intervalli brevi e regolari nel loop principale.
    Se set_duty(), set_lum_perc(), on() o off() vengono chiamati mentre una sequenza è
    in corso, alla prima chiamata di async_execute() il led torna alla luminosità del
    passo corrente. Per dare la precedenza al comando manuale bisogna chiamare prima stop().
    
    @note Ricordati di collegare un resistore al led.
    """
    def __init__(self,n):
        """!
        @brief Inizializza una nuova istanza e forza il led a essere spento.
        
        @param n Il numero del pin da connettere al lato positivo del led.
        
        @exception ValueError se il pin non è valido (controllo di PuWM).
        """
        ## Canale PWM che pilota il led (frequenza fissa a 5000 Hz)
        self.pwm=PuWM(n,5000)
        ## Sequenziatore che gestisce la sequenza caricata
        self._sequenziatore=Sequenziatore()
        
    def set_duty(self,d):
        """!
        @brief Forza una precisa luminosità del led.
        
        @param d Il duty cycle, un intero nell'intervallo [0,1023].
        
        @exception ValueError se d è fuori range (controllo di PuWM).
        @exception TypeError se d non è un intero (controllo di PuWM).
        """
        self.pwm.set_duty(d)
        
    
    def set_lum_perc(self,p):
        """!
        @brief Forza una precisa luminosità percentuale del led.
        
        @param p Un numero nell'intervallo [0,100].
        
        @exception Exception se p è fuori dall'intervallo [0,100].
        """
        self.pwm.set_duty(int(1023/100*self.__check_perc(p)))
        
    def __check_perc(self,p):
        """!
        @brief PRIVATO. Controlla che la percentuale sia un valore accettabile.
        
        @param p La percentuale, limitata all'intervallo [0,100].
        
        @return Il valore di p.
        
        @exception Exception se p è fuori dall'intervallo [0,100].
        """
        if(p<0 or p>100):
            raise Exception(f"Non puoi settare la luminosità del led al {p}%. Usa un numero tra 0 e 100!")
        return p
    
    def on(self):
        """!
        @brief Accende il led al massimo della luminosità.
        """
        self.pwm.set_duty(1023)
        
        
    def off(self):
        """!
        @brief Spegne il led.
        """
        self.pwm.set_duty(0)

    def load(self,lista,ripeti=1):
        """!
        @brief Carica una sequenza di luminosità da eseguire in modo non bloccante.
        
        @details La sequenza è una tupla nella forma ((duty1, tempo1), (duty2, tempo2), ...)
        dove ogni duty è un intero in [0,1023] e ogni tempo è un intero positivo in ms.
        Se era già presente una sequenza, viene sostituita senza preavviso.
        
        @param lista La tupla dei passi (per le dissolvenze vedi rampa()).
        @param ripeti Il numero di volte che la sequenza deve essere eseguita, dove 0 indica che deve ripetersi sempre.
        
        @exception ValueError se un duty non è un intero in [0,1023], se la sequenza è vuota,
        se un tempo non è positivo o se ripeti non è valido.
        """
        for passo in lista:
            d=passo[0]
            if not isinstance(d,int) or d<0 or d>1023:
                raise ValueError(f"Il duty {d} non è valido. Usa un intero tra 0 e 1023!")
        self._sequenziatore.load_sequence(lista,ripeti)

    def stop(self):
        """!
        @brief Fa dimenticare al componente la sequenza caricata e spegne il led.
        """
        self._sequenziatore.unload_sequence()
        self.off()

    def async_execute(self):
        """!
        @brief Esegue la sequenza caricata in maniera non bloccante.
        
        @details Va chiamato ripetutamente a breve distanza dal loop principale.
        Scrive sul PWM solo quando il duty del passo corrente è diverso da quello attuale.
        Quando la sequenza termina, il led viene spento.
        
        @return True se non c'è nulla in corso o se la sequenza è appena terminata,
        False se la sequenza è ancora in corso.
        """
        if not self._sequenziatore.ongoing():
            return True

        duty=self._sequenziatore.current_step()
        if duty is None:
            self.off()
            return True
        if duty!=self.pwm.get_duty():
            self.pwm.set_duty(duty)
        return False

    @staticmethod
    def rampa(da,a,durata_ms,passi=20):
        """!
        @brief Costruisce una dissolvenza lineare da usare con load().
        
        @details Si possono concatenare più rampe con l'operatore +, ad esempio per un
        effetto "respiro":
        
        @code
        led.load(DimmableLed.rampa(0,1023,1000)+DimmableLed.rampa(1023,0,1000),0)
        @endcode
        
        @param da Il duty iniziale, in [0,1023].
        @param a Il duty finale, in [0,1023].
        @param durata_ms La durata totale della rampa in ms.
        @param passi In quanti gradini suddividere la rampa (più passi = più morbida).
        
        @return Una tupla di coppie (duty, tempo_ms).
        
        @exception ValueError se passi è minore di 1 o se durata_ms è minore di passi.
        """
        if passi<1:
            raise ValueError("passi deve essere almeno 1!")
        if durata_ms<passi:
            raise ValueError("durata_ms deve essere almeno pari a passi (1 ms per gradino)!")
        tempo=durata_ms//passi
        if passi==1:
            return ((a,tempo),)
        return tuple((da+(a-da)*i//(passi-1),tempo) for i in range(passi))
        