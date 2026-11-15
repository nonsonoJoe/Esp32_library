from machine import Pin
from Sequenziatore import Sequenziatore
class Led:
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
    ## Pin dell'ESP32 utilizzabili come uscita digitale per un led.
    _PIN_SICURI = (4, 13, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33)
    ## Strapping o segnali all'avvio: il led può lampeggiare al boot, ma funzionano.
    _PIN_CON_CAUTELA = (2, 5, 14, 15)

    def __init__(self, n):
        """!
        @brief Inizializza una nuova istanza e porta il led allo stato spento.
        @details Se il pin è tra quelli da usare con cautela, stampa un avviso sulla seriale.
        @param n Il numero del pin da associare al controllo del led.
        @exception ValueError se il pin non è tra quelli utilizzabili per i led.
        """
        if n in self._PIN_CON_CAUTELA:
            print(f"Il pin {n} può essere usato per i led, ma potrebbe lampeggiare all'avvio.")
        elif n not in self._PIN_SICURI:
            raise ValueError (f"Il pin {n} non può essere collegato a un led! Cambia pin!")
        
        self._pin=Pin(n, Pin.OUT, value=0)
        self._sequenziatore=Sequenziatore()
        self._stato=0
        

    def load (self,lista,ripeti=1):
        """!
        @brief Carica un comportamento da eseguire in modo non bloccante.
        @details La sequenza deve essere una tupla nella forma ((stato1, tempo1), (stato2, tempo2), ...)
        dove ogni stato vale 0 (spento) o 1 (acceso) e ogni tempo è espresso in ms.
        Se era già presente un comportamento, viene sostituito senza preavviso.
        I controlli sono eseguiti prima di modificare lo stato: in caso di errore
        il comportamento precedente resta invariato.
        @param lista La tupla dei passi.
        @param ripeti Il numero di volte che la sequenza deve essere eseguita, dove 0 indica che deve ripetersi sempre.
        @exception ValueError se uno stato non è 0 o 1, se la sequenza è vuota,
        se un tempo non è positivo o se ripeti è negativo.
        """
        for passo in lista:
            if passo[0] not in (0,1):
                raise ValueError(f"Il led non può avere come stato {passo[0]}. Usa un intero pari a 0 o 1!")
        self._sequenziatore.load_sequence(lista,ripeti)

    def stop (self):
        """!
        @brief Fa dimenticare al componente il comportamento caricato e spegne il led.
        """
        self._sequenziatore.unload_sequence()
        self.off()

    def async_execute(self):
        """!
        @brief Esegue il comportamento caricato in maniera non bloccante.
        @details Va chiamato ripetutamente a breve distanza dal loop principale.
        Scrive sul pin solo quando il passo corrente è diverso dall'ultimo stato applicato.
        Quando la sequenza termina, il led viene spento.
        @return True se non c'è nulla in corso o se la sequenza è appena terminata,
        False se la sequenza è ancora in corso.
        """
        if not self._sequenziatore.ongoing():
            return True

        prossimo_stato=self._sequenziatore.current_step()
        if prossimo_stato is None:
            self.off()
            return True
        elif prossimo_stato != self._stato:
            self._scrivi(prossimo_stato)
        return False

    def _scrivi(self,n):
        self._pin.value(n)
        self._stato=n

    
    def on (self):
        """!
        @brief Accende il led.
        """
        self._scrivi(1)
        
    def off (self):
        """!
        @brief Spegne il led.
        """
        self._scrivi(0)
        
    def toggle (self):
        """!
        @brief Commuta il led: se è acceso lo spegne, se è spento lo accende.
        """
        self._scrivi(1 if self._stato==0 else 0)


