from machine import Pin
from Cronometro import Cronometro

class Button:
    """!
    @brief Questa classe modella un bottone collegato a un pin dell'ESP32.
    @details Espone il costruttore Button(n, mode, bounce_time) e i metodi true_press()
    e set_handler(func, event). Con mode=PULL_UP il bottone va collegato tra il pin e GND
    (premuto = livello basso); con mode=PULL_DOWN tra il pin e 3V3 (premuto = livello alto).
    Dopo aver inizializzato un bottone, ricordati di impostare l'handler con set_handler().
    L'handler viene eseguito in contesto di interrupt: deve essere breve e non deve
    allocare memoria (niente f-string, creazione di liste o stampe lunghe). Se deve fare
    di più, conviene che imposti un flag da leggere nel loop principale.
    @warning Il debounce di true_press() copre solo i fronti per cui è registrato l'handler:
    il rimbalzo al rilascio può generare pressioni spurie se si ascolta solo la pressione.
    """
    ## Configurazione con resistenza di pull up (bottone verso GND)
    PULL_UP = 1
    ## Configurazione con resistenza di pull down (bottone verso 3V3)
    PULL_DOWN = -1
    ## Evento: pressione del bottone
    PRESSIONE = 10
    ## Evento: rilascio del bottone
    RILASCIO = 1
    ## Evento: pressione e rilascio
    ENTRAMBI = 11

    ## Pin dell'ESP32 sempre utilizzabili per un bottone.
    _PIN_SICURI = (4, 13, 14, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33)
    ## Pin di strapping: funzionano, ma possono interferire con l'avvio (0 è il tasto BOOT).
    _PIN_CON_CAUTELA = (0, 2, 5, 15)
    ## Pin solo ingresso, senza resistenze di pull up o pull down interne.
    _PIN_SENZA_PULL = (34, 35, 36, 39)

    def __init__(self, n, mode, bounce_time):
        """!
        @brief Inizializza una nuova istanza.
        @details Tutti i controlli vengono eseguiti prima di configurare il pin.
        Sui pin 34, 35, 36 e 39 non esistono resistenze interne: il pin viene configurato
        senza pull e serve una resistenza esterna. Sui pin con cautela stampa un avviso.
        @param n Il numero del pin di ingresso.
        @param mode PULL_UP (+1) o PULL_DOWN (-1).
        @param bounce_time Tempo in ms durante il quale true_press() ignora le pressioni successive a un fronte.
        @exception ValueError se il pin non è utilizzabile, se mode non è valido o se bounce_time è negativo.
        """
        senza_pull = n in self._PIN_SENZA_PULL
        if not (n in self._PIN_SICURI or n in self._PIN_CON_CAUTELA or senza_pull):
            raise ValueError(f"Il pin {n} non può essere collegato a un bottone! Cambia pin!")
        if mode not in (self.PULL_UP, self.PULL_DOWN):
            raise ValueError(f"Il mode {mode} non è valido. Usa +1 (pull up) o -1 (pull down)!")
        if bounce_time < 0:
            raise ValueError(f"Il tempo {bounce_time} è negativo. Usa 0 o un valore positivo in ms!")

        if n in self._PIN_CON_CAUTELA:
            print(f"Il pin {n} può essere usato per i bottoni, ma interferisce con l'avvio.")
        if senza_pull:
            print(f"Il pin {n} non ha resistenze interne: aggiungi una resistenza esterna.")
            pull = None
        else:
            pull = Pin.PULL_UP if mode == self.PULL_UP else Pin.PULL_DOWN

        ## Pin hardware del bottone
        self._pin = Pin(n, Pin.IN, pull)
        ## Fronte che corrisponde alla pressione
        self._fronte_pressione = Pin.IRQ_FALLING if mode == self.PULL_UP else Pin.IRQ_RISING
        ## Fronte che corrisponde al rilascio
        self._fronte_rilascio = Pin.IRQ_RISING if mode == self.PULL_UP else Pin.IRQ_FALLING
        ## Tempo di quiete in ms richiesto tra due fronti validi
        self._bounce_time = bounce_time
        ## Cronometro che misura il tempo dall'ultima chiamata di true_press()
        self._cronometro = Cronometro()

    def true_press(self):
        """!
        @brief Da chiamare nell'handler a ogni fronte, per scartare i rimbalzi.
        @details Il tempo di quiete riparte a ogni chiamata, anche se rifiutata: una sequenza
        di fronti ravvicinati viene considerata un solo evento. La prima chiamata è sempre valida.
        @return True se è passato almeno bounce_time ms dalla chiamata precedente, False se è un rimbalzo.
        """
        valida = (not self._cronometro.attivo()) or self._cronometro.scaduto(self._bounce_time)
        self._cronometro.start()
        return valida

    def set_handler(self, func, event):
        """!
        @brief Associa una funzione handler a un evento del bottone.
        @details L'handler riceve come argomento il Pin che ha generato l'interrupt
        e viene eseguito in contesto di interrupt (vedi la nota della classe).
        @param func La funzione che opera da handler.
        @param event PRESSIONE (10), RILASCIO (1) o ENTRAMBI (11).
        @exception ValueError se event non è valido.
        """
        if event == self.ENTRAMBI:
            trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING
        elif event == self.PRESSIONE:
            trigger = self._fronte_pressione
        elif event == self.RILASCIO:
            trigger = self._fronte_rilascio
        else:
            raise ValueError(f"L'evento {event} non è valido. Usa 10, 1 o 11!")
        self._pin.irq(trigger=trigger, handler=func)