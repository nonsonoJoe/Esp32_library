from machine import ADC, Pin

class AtDC:
    """!
    @brief Questa classe modella un pin dell'ESP32 usato come Analog to Digital Converter (ADC).
    @details Espone il costruttore AtDC(n, min_value, max_value) e i metodi read(), value()
    e value_between(min_v, max_v). L'ADC legge la tensione di segnali analogici continui
    con una risoluzione di 12 bit (valori grezzi da 0 a 4095), con attenuazione a 11 dB
    per leggere tensioni fino a circa 3,3 V. 
    I pin del gruppo ADC2 non funzionano quando il WiFi è attivo, quindi, se il programma
    usa la rete, bisogna preferire i pin dell'ADC1.
    """
    ## Pin dell'ADC1: sempre utilizzabili (34, 35, 36 e 39 sono solo ingresso).
    _PIN_ADC1 = (32, 33, 34, 35, 36, 39)
    ## Pin dell'ADC2: non funzionano se il WiFi è attivo.
    _PIN_ADC2 = (2, 4, 13, 14, 15, 25, 26, 27)

    def __init__(self, n, min_value=0, max_value=100):
        """!
        @brief Inizializza una nuova istanza.
        @details Se il pin appartiene all'ADC2, stampa un avviso.
        @param n Il numero del pin che opera come ADC.
        @param min_value Il valore minimo della lettura normalizzata (corrisponde alla lettura 0).
        @param max_value Il valore massimo della lettura normalizzata (corrisponde alla lettura 4095).
        @exception ValueError se il pin non è utilizzabile come ADC o se min_value non è minore di max_value.
        """
        if n in self._PIN_ADC2:
            print(f"Il pin {n} non funziona se il WiFi è attivo. Fai attenzione!")
        elif n not in self._PIN_ADC1:
            raise ValueError(f"Il pin {n} non è utilizzabile come pin per l'ADC. Cambialo!")
        self._check_values(min_value, max_value)
        ## Oggetto ADC hardware associato al pin
        self._adc = ADC(Pin(n))
        self._adc.atten(ADC.ATTN_11DB)
        ## Valore normalizzato corrispondente alla lettura 0
        self._min_value = min_value
        ## Incremento del valore normalizzato per ogni unità di lettura grezza
        self._scala = (max_value - min_value) / 4095

    def _check_values(self, min_value, max_value):
        """!
        @brief Verifica che l'intervallo sia valido.
        @param min_value Il valore minimo dell'intervallo.
        @param max_value Il valore massimo dell'intervallo.
        @exception ValueError se min_value non è minore di max_value.
        """
        if min_value >= max_value:
            raise ValueError(f"Il valore minimo ({min_value}) deve essere più piccolo del valore massimo ({max_value})!")

    def read(self):
        """!
        @brief Legge direttamente il valore della tensione.
        @return Un intero tra 0 e 4095.
        """
        return self._adc.read()

    def value(self):
        """!
        @brief Legge la tensione e la normalizza nell'intervallo scelto nel costruttore.
        @return Un valore in virgola mobile tra min_value e max_value.
        """
        return self._min_value + self._scala * self.read()

    def value_between(self, min_v, max_v):
        """!
        @brief Legge la tensione e la normalizza in un intervallo passato come argomento.
        @details L'intervallo passato vale solo per questa lettura e non modifica quello
        impostato nel costruttore. Non si può precalcolare la scala, quindi è leggermente
        più costoso di value().
        @param min_v Il valore minimo dell'intervallo (corrisponde alla lettura 0).
        @param max_v Il valore massimo dell'intervallo (corrisponde alla lettura 4095).
        @return Un valore in virgola mobile tra min_v e max_v.
        @exception ValueError se min_v non è minore di max_v.
        """
        self._check_values(min_v, max_v)
        return min_v + (max_v - min_v) * self.read() / 4095