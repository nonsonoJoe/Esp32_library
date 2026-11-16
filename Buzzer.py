from machine import Pin, PWM # type: ignore
from time import sleep_ms
#Codice mio
from PuWM import PuWM
from Sequenziatore import Sequenziatore
class Buzzer:
    """!
    @brief Questa classe modella un buzzer pilotato in PWM.

    @details Espone il costruttore Buzzer(n, f) e i metodi set_duty(), set_freq(), stop(),
    load(), async_execute() e play().
    
    Una melodia si può eseguire in due modi: in modo bloccante con play(), oppure in modo
    non bloccante caricandola con load() e chiamando async_execute() a intervalli brevi e
    regolari nel loop principale.
    
    Il buzzer usa un Sequenziatore interno: ogni nota è un passo nella forma (frequenza, tempo_ms),
    dove la frequenza 0 indica una pausa.
    
    Se due note uguali sono consecutive vengono suonate come un'unica nota lunga: per
    separarle bisogna inserire una pausa (0) in mezzo.
    
    Se set_duty() o set_freq() vengono chiamati mentre una melodia è in corso, alla prima
    chiamata di async_execute() il buzzer torna alla nota corrente. Per dare la precedenza
    al comando manuale bisogna chiamare prima stop().
    """
    ## Dizionario che associa il nome di una nota alla sua frequenza in Hz (S = diesis, ad esempio CS4 = Do diesis 4).
    DIZIONARIO_NOTE = {
        "B0": 31,
        "C1": 33, "CS1": 35, "D1": 37, "DS1": 39, "E1": 41, "F1": 44, "FS1": 46, "G1": 49, "GS1": 52, "A1": 55, "AS1": 58, "B1": 62,
        "C2": 65, "CS2": 78, "E2": 82, "F2": 87, "FS2": 93, "G2": 98, "GS2": 104, "A2": 110, "AS2": 117, "B2": 123,
        "C3": 131, "CS3": 139, "D3": 147, "DS3": 156, "E3": 165, "F3": 175, "FS3": 185, "G3": 196, "GS3": 208, "A3": 220, "AS3": 233, "B3": 247,
        "C4": 262, "CS4": 277, "D4": 294, "DS4": 311, "E4": 330, "F4": 349, "FS4": 370, "G4": 392, "GS4": 415, "A4": 440, "AS4": 466, "B4": 494,
        "C5": 523, "CS5": 554, "D5": 587, "DS5": 622, "E5": 659, "F5": 698, "FS5": 740, "G5": 784, "GS5": 831, "A5": 880, "AS5": 932, "B5": 988,
        "C6": 1047, "CS6": 1109, "D6": 1175, "DS6": 1245, "E6": 1319, "F6": 1397, "FS6": 1480, "G6": 1568, "GS6": 1661, "A6": 1760, "AS6": 1865, "B6": 1976,
        "C7": 2093, "CS7": 2217, "D7": 2349, "DS7": 2489, "E7": 2637, "F7": 2794, "FS7": 2960, "G7": 3136, "GS7": 3322, "A7": 3520, "AS7": 3729, "B7": 3951,
        "C8": 4186, "CS8": 4435, "D8": 4699, "DS8": 4978
    }

    def __init__(self, n, f=5000):
        """!
        @brief Inizializza una nuova istanza, con il buzzer in silenzio.
        
        @param n Il numero del pin da connettere al buzzer.
        @param f La frequenza iniziale in Hz, un intero tra 1 e 5000.
        
        @exception ValueError se il pin o la frequenza non sono validi (controlli di PuWM).
        """
        ## Canale PWM che pilota il buzzer
        self.pwm = PuWM(n, f)
        self.pwm.set_duty(0)
        ## Sequenziatore che gestisce la melodia caricata
        self._sequenziatore = Sequenziatore()
        ## Duty usato per le note della melodia caricata
        self._duty = 512
        ## Ultima frequenza applicata dalla melodia: 0 = silenzio, None = sconosciuta
        self._ultima_freq = 0

    def set_duty(self,d):
        """!
        @brief Imposta il duty cycle, cioè l'intensità del suono.
        
        @details I suoni più intensi si ottengono con d circa uguale a 512.
        
        @param d Un intero tra 0 e 1023.
        
        @exception ValueError se d è fuori range (controllo di PuWM).
        @exception TypeError se d non è un intero (controllo di PuWM).
        """
        self.pwm.set_duty(d)
        self._ultima_freq = None

    def set_freq(self, f):
        """!
        @brief Imposta la frequenza del suono.
        
        @param f La frequenza in Hz, un intero tra 1 e 5000.
        
        @exception ValueError se f è fuori range (controllo di PuWM).
        @exception TypeError se f non è un intero (controllo di PuWM).
        """
        self.pwm.set_freq(f)
        self._ultima_freq = None

    def stop(self):
        """!
        @brief Fa dimenticare al componente la melodia caricata (se c'è) e porta il duty a 0.
        """
        self._sequenziatore.unload_sequence()
        self._silenzia()
            
    def play(self, melodies, wait, duty=512):
        """!
        @brief Suona una melodia in modo BLOCCANTE.
        
        @param melodies La tupla (o lista) di note.
        @param wait La durata di ogni nota e di ogni pausa in ms.
        @param duty L'intensità del suono, un intero tra 0 e 1023.
        """
        for note in melodies:
            if note == 0:
                self.pwm.set_duty(0) # Pausa
            else:
                self.pwm.set_freq(self.DIZIONARIO_NOTE.get(note))
                self.pwm.set_duty(duty) 
            sleep_ms(wait) # Durata della nota
        self.stop()

    def async_execute(self):
        """!
        @brief Esegue la melodia caricata in maniera non bloccante.
        
        @details Va chiamato ripetutamente a breve distanza dal loop principale.
        Scrive sul PWM solo quando la nota cambia. Quando la melodia termina il buzzer tace.
        
        @return True se non c'è nulla in corso o se la melodia è appena terminata,
        False se la melodia è ancora in corso.
        """
        if not self._sequenziatore.ongoing():
            return True

        freq = self._sequenziatore.current_step()
        if freq is None:
            self._silenzia()
            return True
        if freq != self._ultima_freq:
            self._applica(freq)
        return False

    def load(self, melodies, wait, duty=512, ripeti=1):
            """!
            @brief Carica una melodia da eseguire in modo non bloccante con async_execute().
            
            @details La melodia è una tupla (o lista) di note, ad esempio ("C4", "E4", 0, "G4"),
            dove 0 indica una pausa. I nomi validi sono le chiavi di DIZIONARIO_NOTE.
            
            Se era già presente una melodia, viene sostituita senza preavviso.
            
            I controlli sono eseguiti prima di modificare lo stato: in caso di errore
            la melodia precedente resta invariata.
            
            @param melodies La tupla (o lista) di note.
            @param wait La durata di ogni nota e di ogni pausa in ms, un intero positivo.
            @param duty L'intensità del suono, un intero tra 0 e 1023.
            @param ripeti Il numero di volte che la melodia deve essere eseguita, dove 0 indica che deve ripetersi sempre.
            
            @exception ValueError se una nota non esiste, se wait o duty non sono validi,
            se la melodia è vuota o se ripeti non è valido.
            """
            if not isinstance(wait, int) or wait <= 0:
                raise ValueError(f"wait deve essere un intero positivo in ms, non {wait}!")
            if not isinstance(duty, int) or duty < 0 or duty > 1023:
                raise ValueError(f"Il duty deve essere un intero tra 0 e 1023, non {duty}!")
            passi = []
            for nota in melodies:
                if nota == 0:
                    passi.append((0, wait))
                elif nota in self.DIZIONARIO_NOTE:
                    passi.append((self.DIZIONARIO_NOTE[nota], wait))
                else:
                    raise ValueError(f"La nota {nota} non esiste. Usa un nome come 'A4' oppure 0 per una pausa!")
            self._sequenziatore.load_sequence(tuple(passi), ripeti)
            self._duty = duty
            # Forza la riscrittura della prima nota, anche se coincide con l'ultima applicata
            self._ultima_freq = None

    def _applica(self, freq):
        """!
        @brief Scrive sul PWM la frequenza di una nota (o il silenzio) e la memorizza.
        
        @param freq La frequenza in Hz, oppure 0 per una pausa.
        """
        if freq == 0:
            self.pwm.set_duty(0)
        else:
            self.pwm.set_freq(freq)
            self.pwm.set_duty(self._duty)
        self._ultima_freq = freq

    def _silenzia(self):
        """!
        @brief Porta il duty a 0 e memorizza che il buzzer è in silenzio.
        """
        self.pwm.set_duty(0)
        self._ultima_freq = 0

    