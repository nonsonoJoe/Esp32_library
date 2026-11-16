from AtDC import AtDC

class LDR:
    """!
    @brief Questa classe modella un fotoresistore (light dependent resistor, LDR).
    @details Un oggetto LDR è composto da un AtDC, che gestisce la lettura e la validazione del pin.
    Espone il costruttore LDR(n, min_value, max_value, invertito) e i metodi read(), value(),
    value_between(min_v, max_v) e still_in_range(n).
    Il fotoresistore va collegato in un partitore di tensione e il pin n va connesso al
    terminale di mezzo. Con il fotoresistore tra 3V3 e il pin (e la resistenza verso GND)
    più luce dà una tensione più alta. Con il cablaggio opposto la lettura è
    invertita: in quel caso si passa invertito=True, così il resto del programma ragiona
    sempre in termini di "più luce, più valore".
    I pin del gruppo ADC2 non funzionano quando il WiFi è attivo (vedi AtDC), quindi, se il
    programma usa la rete, bisogna preferire i pin dell'ADC1.
    @note La classe ricorda l'ultima lettura fatta con read(), value() o value_between(), insieme
    al metodo usato, per permettere il confronto di still_in_range().
    """

    def __init__(self, n, min_value=0, max_value=100, invertito=False):
        """!
        @brief Inizializza una nuova istanza.
        @details I controlli sul pin e sull'intervallo sono eseguiti dall'AtDC interno.
        @param n Il numero del pin da connettere al terminale di mezzo dell'LDR.
        @param min_value Il valore minimo della lettura normalizzata (corrisponde al buio).
        @param max_value Il valore massimo della lettura normalizzata (corrisponde alla luce).@param invertito Se True, le letture vengono invertite per compensare il cablaggio opposto.
        @exception ValueError se il pin non è utilizzabile come ADC o se min_value non è minore di max_value.
        """
        ## ADC che esegue le letture
        self._atdc = AtDC(n, min_value, max_value)
        ## True se le letture vanno invertite
        self._invertito = invertito
        ## Valore minimo della lettura normalizzata
        self._min = min_value
        ## Valore massimo della lettura normalizzata
        self._max = max_value
        ## Ultimo valore restituito al chiamante (già invertito se necessario)
        self._last_read = None
        ## Metodo dell'ultima lettura: 1 = read(), 2 = value(), 3 = value_between(), None = nessuna
        self._last_read_mode = None
        ## Estremo minimo usato nell'ultima chiamata di value_between()
        self._last_read_min = None
        ## Estremo massimo usato nell'ultima chiamata di value_between()
        self._last_read_max = None

    def read(self):
        """!
        @brief Legge direttamente il valore grezzo della tensione.
        @details Se l'LDR è invertito il valore restituito è FONDO_SCALA meno la lettura.
        Memorizza la lettura come riferimento per still_in_range().
        @return Un intero tra 0 e 4095.
        """
        valore = self._atdc.read()
        if self._invertito:
            valore = self._atdc.FONDO_SCALA - valore
        self._last_read_mode = 1
        self._last_read = valore
        return valore

    def value(self):
        """!
        @brief Legge la tensione e la normalizza nell'intervallo scelto nel costruttore.
        @details Se l'LDR è invertito il valore restituito è rispecchiato dentro l'intervallo.
        Memorizza la lettura come riferimento per still_in_range().
        @return Un valore in virgola mobile tra min_value e max_value.
        """
        valore = self._atdc.value()
        if self._invertito:
            valore = self._max - valore + self._min
        self._last_read_mode = 2
        self._last_read = valore
        return valore

    def value_between(self, min_v, max_v):
        """!
        @brief Legge la tensione e la normalizza in un intervallo passato come argomento.
        @details L'intervallo vale solo per questa lettura e non modifica quello del costruttore.
        Se l'LDR è invertito il valore restituito è rispecchiato dentro l'intervallo passato.
        Memorizza la lettura e l'intervallo come riferimento per still_in_range().
        @param min_v Il valore minimo dell'intervallo.
        @param max_v Il valore massimo dell'intervallo.
        @return Un valore in virgola mobile tra min_v e max_v.
        @exception ValueError se min_v non è minore di max_v.
        """
        valore = self._atdc.value_between(min_v, max_v)
        if self._invertito:
            valore = max_v - valore + min_v
        self._last_read_mode = 3
        self._last_read_min = min_v
        self._last_read_max = max_v
        self._last_read = valore
        return valore

    def still_in_range(self, n):
        """!
        @brief Controlla se la luce attuale è ancora vicina all'ultima lettura memorizzata.
        @details Esegue una nuova lettura con lo stesso metodo (e lo stesso intervallo) dell'ultima
        lettura e la confronta con questa. Il controllo non conta come lettura: il riferimento
        resta quello dell'ultima chiamata diretta di read(), value() o value_between(), quindi
        una variazione lenta della luce prima o poi esce dal range.
        La tolleranza n è espressa nell'unità dell'ultima lettura (grezza, normalizzata o tra
        gli estremi passati a value_between()). Una lettura fatta da un altro punto del
        programma sullo stesso oggetto sposta il riferimento.
        @param n La tolleranza ammessa, non negativa.
        @return True se la differenza assoluta tra la lettura attuale e quella di riferimento è al più n.
        @exception ValueError se n è negativo o se non è stata fatta alcuna lettura precedente.
        """
        if n < 0:
            raise ValueError(f"La tolleranza non può essere {n}. Usa un numero non negativo!")
        if self._last_read_mode is None:
            raise ValueError("Nessuna lettura precedente con cui confrontare!")
        precedente = self._last_read
        if self._last_read_mode == 1:
            attuale = self.read()
        elif self._last_read_mode == 2:
            attuale = self.value()
        else:
            attuale = self.value_between(self._last_read_min, self._last_read_max)
        self._last_read = precedente
        return abs(attuale - precedente) <= n