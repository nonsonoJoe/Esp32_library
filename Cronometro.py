from time import ticks_ms, ticks_diff, ticks_add
#generata e documentata con l'ia, il codice mi sembra corretto, la documentazione non l'ho letta
class Cronometro:
    """!
    @brief Cronometro non bloccante basato sui tick di MicroPython.

    @details Usa ticks_ms(), ticks_diff() e ticks_add() del modulo time,
    quindi gestisce correttamente il ritorno a zero del contatore dei
    millisecondi. Il tempo è sempre calcolato come differenza rispetto
    all'istante di avvio, senza usare timer hardware né sleep.

    @note Gli intervalli misurabili devono essere inferiori a metà del
    periodo di ticks_ms() (su molte porte circa 6 giorni). Oltre questo
    limite ticks_diff() restituisce valori errati.

    @warning Tutti i metodi di lettura (trascorso(), scaduto(), fase()) e
    avanza() richiedono che il cronometro sia attivo, altrimenti
    sollevano TypeError.

    @code
    cron = Cronometro(avvia=True)
    while True:
        if cron.scaduto(500):
            cron.avanza(500)   # niente deriva
            led.toggle()
    @endcode
    """

    def __init__(self, avvia=False):
        """!
        @brief Costruisce il cronometro.

        @param avvia  Se True il cronometro parte subito dalla creazione,
                      altrimenti resta fermo fino a start().
        """
        self._t0 = ticks_ms() if avvia else None

    def start(self):
        """!
        @brief Avvia o riavvia il cronometro dall'istante corrente.

        @details Se era già attivo, il conteggio riparte da zero.
        """
        self._t0 = ticks_ms()

    def stop(self):
        """!
        @brief Ferma il cronometro e azzera lo stato.

        @details Il tempo trascorso non viene conservato: per ripartire
        serve chiamare start().
        """
        self._t0 = None

    def attivo(self):
        """!
        @brief Indica se il cronometro è in funzione.

        @return True se è stato avviato e non fermato, False altrimenti.
        """
        return self._t0 is not None

    def trascorso(self):
        """!
        @brief Restituisce il tempo trascorso dall'avvio.

        @return Millisecondi trascorsi (int). Può essere negativo se
                l'inizio è stato spostato nel futuro con avanza().
        @exception TypeError se il cronometro non è attivo.
        """
        return ticks_diff(ticks_ms(), self._t0)

    def scaduto(self, ms):
        """!
        @brief Verifica se è trascorso almeno un dato intervallo.

        @param ms  Durata da confrontare, in millisecondi.
        @return True se il tempo trascorso è maggiore o uguale a ms.
        @exception TypeError se il cronometro non è attivo.
        """
        return ticks_diff(ticks_ms(), self._t0) >= ms

    def fase(self, periodo):
        """!
        @brief Posizione dentro un ciclo periodico.

        @details Equivale a (tempo trascorso) % periodo. Utile per
        pattern ciclici, ad esempio lampeggi con fase() < 250 su un
        periodo di 500 ms.

        @param periodo  Durata del ciclo in millisecondi (deve essere > 0).
        @return Valore nell'intervallo [0, periodo).
        @exception TypeError se il cronometro non è attivo.
        @exception ZeroDivisionError se periodo è 0.
        """
        return ticks_diff(ticks_ms(), self._t0) % periodo

    def avanza(self, ms):
        """!
        @brief Sposta l'istante di inizio in avanti di ms millisecondi.

        @details Da usare dopo che scaduto(ms) è risultato vero per
        rinnovare il ciclo senza accumulare l'errore di ritardo del
        loop, che invece introdurrebbe deriva con start().

        @param ms  Millisecondi di cui spostare l'inizio.
        @exception TypeError se il cronometro non è attivo.
        """
        self._t0 = ticks_add(self._t0, ms)