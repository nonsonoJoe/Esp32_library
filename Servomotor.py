from PuWM import PuWM
from Sequenziatore import Sequenziatore

class Servomotor:
    """!
    @brief Questa classe modella un servomotore collegato a un pin dell'ESP32.
    @details Espone il costruttore Servomotor(n) e i metodi set_duty(d), set_angle(a),
    rilascia(), move_towards(duty, steps), load(lista, ripeti), load_angles(lista, ripeti),
    stop() e async_execute().
    Il servo può essere comandato in tre modi: con una posizione diretta (set_duty() e
    set_angle()), con un movimento graduale non bloccante (move_towards()) oppure caricando
    una sequenza di posizioni (load() o load_angles()) ed eseguendola con async_execute().
    Collegamenti: marrone = massa (GND), rosso = 5V (pin 5V della scheda), giallo = pin n.
    La massa del servo deve essere in comune con quella dell'ESP32.
    La classe è composta da un PuWM a 50 Hz e da un Sequenziatore.
    @note move_towards() e async_execute() sono indipendenti: non si conoscono e non si
    scambiano informazioni. Se vengono usati insieme sullo stesso servo vince l'ultima
    scrittura e, se una sequenza è in corso, alla prima chiamata di async_execute() il servo
    torna al passo corrente. Per dare la precedenza a uno dei due bisogna chiamare stop()
    o evitare di chiamare l'altro.
    @note Il pin 5V della scheda è alimentato dalla USB: sotto carico un servo può avere picchi
    di corrente che fanno riavviare la scheda. In quel caso conviene un'alimentazione separata.
    """
    ## Duty cycle corrispondente a 0 gradi
    DUTY_MIN = 26
    ## Duty cycle corrispondente a 180 gradi
    DUTY_MAX = 128
    ## Angolo massimo in gradi
    ANGOLO_MAX = 180

    def __init__(self, n):
        """!
        @brief Inizializza una nuova istanza senza forzare alcun angolo.
        @details Il servo parte rilasciato (duty 0) e la sua posizione è ignota.
        I controlli sul pin sono eseguiti dal PuWM interno.
        @param n Il numero del pin che va connesso al filo di segnale del servo.
        @exception ValueError se il pin non è utilizzabile per la PWM.
        """
        ## Canale PWM a 50 Hz che pilota il servo
        self._pwm = PuWM(n, 50)
        ## Sequenziatore che gestisce le sequenze caricate
        self._sequenziatore = Sequenziatore()
        ## Ultimo duty scritto sul servo, None se la posizione è ignota
        self._stato = None

    def set_duty(self, d):
        """!
        @brief Forza una posizione del servo in base al duty cycle.
        @param d Il duty cycle, un intero nell'intervallo [DUTY_MIN, DUTY_MAX].
        @exception TypeError se d non è un intero.
        @exception ValueError se d è fuori dall'intervallo.
        """
        self._controlla_duty(d)
        self._scrivi(d)

    def set_angle(self, a):
        """!
        @brief Forza un preciso angolo del servo.
        @details La conversione è l'approssimazione lineare tra DUTY_MIN (0°) e DUTY_MAX (180°).
        Sono ammessi anche valori con la virgola: il duty risultante viene troncato a intero.
        @param a L'angolo in gradi, nell'intervallo [0, ANGOLO_MAX].
        @exception ValueError se a è fuori dall'intervallo.
        """
        self._scrivi(self._angolo_a_duty(a))

    def rilascia(self):
        """!
        @brief Costringe il servo a non forzare più un angolo.
        @details Porta il duty a 0 e segna la posizione come ignota. Un servo rilasciato può
        cedere sotto carico.
        """
        self._pwm.set_duty(0)
        self._stato = None

    def move_towards(self, duty, steps=1):
        """!
        @brief Sposta il servo verso un duty di un passo alla volta, senza bloccare.
        @details Va chiamato ripetutamente a breve distanza: a ogni chiamata il duty cambia
        di al più steps unità verso il bersaglio, senza mai superarlo. Più steps è grande, più
        il movimento è veloce. Se la posizione è ignota (all'avvio o dopo rilascia()) il servo
        salta direttamente al bersaglio. Non interagisce con le sequenze (vedi la nota della classe).
        @param duty Il duty da raggiungere, un intero nell'intervallo [DUTY_MIN, DUTY_MAX].
        @param steps L'ampiezza massima del passo, un intero positivo.
        @return True se il servo ha raggiunto il bersaglio, False se ha ancora strada da fare.
        @exception TypeError se duty o steps non sono interi.
        @exception ValueError se duty è fuori dall'intervallo o se steps non è positivo.
        """
        self._controlla_duty(duty)
        if not isinstance(steps, int):
            raise TypeError("steps deve essere un intero!")
        if steps < 1:
            raise ValueError(f"steps non può essere {steps}. Usa un intero positivo!")
        stato = self._stato
        if stato is None or abs(duty - stato) <= steps:
            if duty != stato:
                self._scrivi(duty)
            return True
        self._scrivi(stato + (steps if duty > stato else -steps))
        return False

    def load(self, lista, ripeti=1):
        """!
        @brief Carica una sequenza di duty da eseguire in modo non bloccante.
        @details La sequenza deve essere una tupla nella forma ((duty1, tempo1), (duty2, tempo2), ...)
        con i tempi in ms. I passi sono salti di posizione, non rampe: per un movimento graduale
        servono più passi intermedi. Se era già presente una sequenza, viene sostituita senza preavviso.
        I controlli sono eseguiti prima di modificare lo stato: in caso di errore la sequenza
        precedente resta invariata.
        @param lista La tupla dei passi.
        @param ripeti Il numero di volte che la sequenza deve essere eseguita, dove 0 indica che deve ripetersi sempre.
        @exception TypeError se un duty non è un intero.
        @exception ValueError se un duty è fuori dall'intervallo, se la sequenza è vuota,
        se un tempo non è positivo o se ripeti non è valido.
        """
        for passo in lista:
            self._controlla_duty(passo[0])
        self._sequenziatore.load_sequence(lista, ripeti)

    def load_angles(self, lista, ripeti=1):
        """!
        @brief Carica una sequenza di angoli da eseguire in modo non bloccante.
        @details Come load(), ma la sequenza ha la forma ((angolo1, tempo1), (angolo2, tempo2), ...)
        con gli angoli in gradi. Gli angoli vengono convertiti in duty al momento del caricamento.
        @param lista La tupla dei passi.
        @param ripeti Il numero di volte che la sequenza deve essere eseguita, dove 0 indica che deve ripetersi sempre.
        @exception ValueError se un angolo è fuori dall'intervallo, se la sequenza è vuota,
        se un tempo non è positivo o se ripeti non è valido.
        """
        convertita = tuple((self._angolo_a_duty(passo[0]), passo[1]) for passo in lista)
        self._sequenziatore.load_sequence(convertita, ripeti)

    def stop(self):
        """!
        @brief Fa dimenticare al servo la sequenza caricata.
        @details Il servo resta nella posizione in cui si trova: a differenza del Led non viene
        rilasciato, perché un servo rilasciato può cedere sotto carico. Per rilasciarlo
        serve chiamare anche rilascia().
        """
        self._sequenziatore.unload_sequence()

    def async_execute(self):
        """!
        @brief Esegue la sequenza caricata in maniera non bloccante.
        @details Va chiamato ripetutamente a breve distanza dal loop principale.
        Scrive sul servo solo quando il passo corrente è diverso dall'ultima posizione scritta.
        Quando la sequenza termina il servo resta nell'ultima posizione.
        @return True se non c'è nulla in corso o se la sequenza è appena terminata,
        False se la sequenza è ancora in corso.
        """
        if not self._sequenziatore.ongoing():
            return True
        prossimo_stato = self._sequenziatore.current_step()
        if prossimo_stato is None:
            return True
        if prossimo_stato != self._stato:
            self._scrivi(prossimo_stato)
        return False

    def _scrivi(self, d):
        """!
        @brief Scrive il duty sul PWM e aggiorna la posizione memorizzata, senza controlli.
        @param d Un duty già validato.
        """
        self._pwm.set_duty(d)
        self._stato = d

    def _controlla_duty(self, d):
        """!
        @brief Verifica che il duty sia un intero accettabile per un servo.
        @param d Il duty da controllare.
        @exception TypeError se d non è un intero.
        @exception ValueError se d è fuori dall'intervallo [DUTY_MIN, DUTY_MAX].
        """
        if not isinstance(d, int):
            raise TypeError(f"Il duty {d} deve essere un intero!")
        if d < self.DUTY_MIN or d > self.DUTY_MAX:
            raise ValueError(f"Non puoi settare il duty a {d}. Usa un intero tra {self.DUTY_MIN} e {self.DUTY_MAX}!")

    def _angolo_a_duty(self, a):
        """!
        @brief Verifica l'angolo e lo converte in duty.
        @param a L'angolo in gradi.
        @return Il duty corrispondente, intero.
        @exception ValueError se a è fuori dall'intervallo [0, ANGOLO_MAX].
        """
        if a < 0 or a > self.ANGOLO_MAX:
            raise ValueError(f"Non puoi settare l'angolo a {a}. Usa un valore tra 0 e {self.ANGOLO_MAX}!")
        return int(self.DUTY_MIN + a * (self.DUTY_MAX - self.DUTY_MIN) / self.ANGOLO_MAX)