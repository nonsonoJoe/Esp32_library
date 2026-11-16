from AtDC import AtDC

class Potentiometer:
    """!
    @brief Questa classe modella un potenziometro.
    @details Un oggetto Potentiometer è composto da un AtDC, che gestisce la lettura e la
    validazione del pin. Espone il costruttore Potentiometer(n, min_value, max_value) e i metodi
    read(), value(), value_between(min_v, max_v) e still_in_range(n).
    Il terminale centrale del potenziometro va connesso al pin n, e gli altri due a 3V3 e GND.
    I pin del gruppo ADC2 non funzionano quando il WiFi è attivo (vedi AtDC), quindi, se il
    programma usa la rete, bisogna preferire i pin dell'ADC1.
    @note La classe ricorda l'ultima lettura fatta con read(), value() o value_between(), insieme
    al metodo usato, per permettere il confronto di still_in_range().
    """

    def __init__(self, n, min_value=0, max_value=100):
        """!
        @brief Inizializza una nuova istanza.
        @details I controlli sul pin e sull'intervallo sono eseguiti dall'AtDC interno.
        @param n Il numero del pin da connettere al terminale di mezzo del potenziometro.
        @param min_value Il valore minimo della lettura normalizzata (manopola a un estremo).
        @param max_value Il valore massimo della lettura normalizzata (manopola all'altro estremo).
        @exception ValueError se il pin non è utilizzabile come ADC o se min_value non è minore di max_value.
        """
        ## ADC che esegue le letture
        self._atdc = AtDC(n, min_value, max_value)
        ## Metodo dell'ultima lettura: 1 = read(), 2 = value(), 3 = value_between(), None = nessuna
        self._last_mode = None
        ## Ultimo valore restituito al chiamante
        self._last_read = None
        ## Estremo minimo usato nell'ultima chiamata di value_between()
        self._last_read_min = None
        ## Estremo massimo usato nell'ultima chiamata di value_between()
        self._last_read_max = None

    def read(self):
        """!
        @brief Legge direttamente il valore grezzo della tensione.
        @details Memorizza la lettura come riferimento per still_in_range().
        @return Un intero tra 0 e 4095.
        """
        self._last_read = self._atdc.read()
        self._last_mode = 1
        return self._last_read

    def value(self):
        """!
        @brief Legge la tensione e la normalizza nell'intervallo scelto nel costruttore.
        @details Memorizza la lettura come riferimento per still_in_range().
        @return Un valore in virgola mobile tra min_value e max_value.
        """
        self._last_read = self._atdc.value()
        self._last_mode = 2
        return self._last_read

    def value_between(self, min_v, max_v):
        """!
        @brief Legge la tensione e la normalizza in un intervallo passato come argomento.
        @details L'intervallo vale solo per questa lettura e non modifica quello del costruttore.
        Memorizza la lettura e l'intervallo come riferimento per still_in_range().
        @param min_v Il valore minimo dell'intervallo.
        @param max_v Il valore massimo dell'intervallo.
        @return Un valore in virgola mobile tra min_v e max_v.
        @exception ValueError se min_v non è minore di max_v.
        """
        self._last_read = self._atdc.value_between(min_v, max_v)
        self._last_mode = 3
        self._last_read_min = min_v
        self._last_read_max = max_v
        return self._last_read

    def still_in_range(self, n):
        """!
        @brief Controlla se la manopola è ancora vicina all'ultima lettura memorizzata.
        @details Esegue una nuova lettura con lo stesso metodo (e lo stesso intervallo) dell'ultima
        lettura e la confronta con questa. Il controllo non conta come lettura: il riferimento
        resta quello dell'ultima chiamata diretta di read(), value() o value_between(). Per
        spostare il riferimento dopo un cambiamento bisogna quindi rifare una lettura.
        La tolleranza n è espressa nell'unità dell'ultima lettura (grezza, normalizzata o tra
        gli estremi passati a value_between()). Una lettura fatta da un altro punto del
        programma sullo stesso oggetto sposta il riferimento.
        @param n La tolleranza ammessa, non negativa.
        @return True se la differenza assoluta tra la lettura attuale e quella di riferimento è al più n.
        @exception ValueError se n è negativo o se non è stata fatta alcuna lettura precedente.
        """
        if n < 0:
            raise ValueError(f"La tolleranza non può essere {n}. Usa un numero non negativo!")
        if self._last_mode is None:
            raise ValueError("Nessuna lettura precedente con cui confrontare!")
        precedente = self._last_read
        if self._last_mode == 1:
            attuale = self.read()
        elif self._last_mode == 2:
            attuale = self.value()
        else:
            attuale = self.value_between(self._last_read_min, self._last_read_max)
        self._last_read = precedente
        return abs(attuale - precedente) <= n