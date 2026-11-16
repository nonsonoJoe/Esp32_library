from Cronometro import Cronometro
#documentazione estesa con claude
class Sequenziatore:
    """!
    @brief Questa classe modella un sequenziatore, ovvero un oggetto in grado di memorizzare una sequenza di azioni
    che un componente deve svolgere in un certo lasso di tempo.
    @details Gli oggetti di questa classe sono pensati per comporre
    gli oggetti delle classi di componenti. I sequenziatori usano gli oggetti Cronometro.
    Il sequenziatore non conosce l'hardware e tratta i passi come dati opachi: non confronta
    i passi tra loro, quindi il componente deve ricordare l'ultimo passo applicato per evitare
    scritture ridondanti. I passi non possono valere None, perché None è usato come segnale
    di "nessun passo".
    """
    def __init__(self):
        """!
        @brief Inizializza una nuova istanza e un suo cronometro
        """
        ## @brief Tupla di passi nella forma ((passo, tempo_ms), ...), None se non c'è una sequenza
        self._sequenza=None
        ## @brief Ripetizioni rimanenti (0 = infinito), None se non c'è una sequenza
        self._ripeti=None
        ## @brief Cronometro che misura il tempo trascorso nel passo corrente
        self._cronometro=Cronometro()
        ## @brief Indice del passo corrente dentro la sequenza, None se non c'è una sequenza
        self._indice=None


    def load_sequence(self,sequenza, ripeti=1):
        """!
        @brief Permette di caricare una sequenza, specificando quante volte deve essere ripetuta.
        @details La sequenza deve essere una tupla nella struttura ((passo1, tempo1), (passo2,tempo2), ...)
        dove tempo è espresso in ms. Quando questo metodo viene chiamato, il cronometro si avvia.
        Se era già presente una sequenza, viene sostituita senza preavviso e il conteggio riparte dal primo passo.
        Tutti i controlli vengono eseguiti prima di modificare lo stato: in caso di errore
        l'oggetto resta com'era.
        @param  sequenza La tupla in ingresso
        @param  ripeti Il numero di volte che si deve ripetere la sequenza, dove 0 indica che la sequenza si deve ripetere sempre
        @exception ValueError se ripeti è negativo, se la sequenza è vuota o se un passo ha una durata non positiva.
        """
        if ripeti<0:
            raise ValueError("Non puoi caricare un comportamento da ripetere un numero negativo di volte. Usa un numero non negativo!")
        if len(sequenza)==0:
            raise ValueError("La tupla passata è vuota. Mettine una con degli elementi del tipo (istruzione,tempo_ms)!")
        for passo in sequenza:
            if passo[1]<=0:
                raise ValueError("Le istruzioni passate possono avere solo un tempo di esecuzione positivo passato in millisecondi!")
        self._sequenza=sequenza
        self._ripeti=ripeti
        self._indice=0
        self._cronometro.start()

    def unload_sequence(self):
        """!
        @brief Permette di dimenticare le informazioni sulla sequenza.
        @details Questo metodo ferma il cronometro. Dopo, la chiamata ongoing() restituisce False.
        """
        self._sequenza=None
        self._ripeti=None
        self._indice=None
        self._cronometro.stop()

    def ongoing(self):
        """!
        @brief Notifica se il sequenziatore è attivo.
        @details Vale True da load_sequence() fino al momento in cui current_step() segnala la fine
        della sequenza (o fino a unload_sequence()).
        @return True se c'è una sequenza in corso, False altrimenti.
        """
        return self._cronometro.attivo()

    def current_step(self):
        """!
        @brief Trova il passo corrente da eseguire.
        @details Se il passo attuale è scaduto, avanza anche di più passi consecutivi (utile se
        il loop principale è in ritardo), gestendo le ripetizioni. Quando la sequenza termina
        chiama unload_sequence().
        Il metodo restituisce il passo corrente a ogni chiamata, anche se non è cambiato:
        spetta al componente confrontarlo con l'ultimo applicato.
        Il chiamante può distinguere "inattivo" da "appena finita" controllando ongoing()
        prima della chiamata: se era True e il risultato è None, la sequenza è appena terminata.
        @return Il valore del passo corrente (il primo elemento della coppia (passo, tempo)),
        oppure None se non c'è una sequenza o se è appena terminata.
        """
        if self._sequenza is None:
            return None
        durata=self._sequenza[self._indice][1]
        while self._cronometro.scaduto(durata):
            self._cronometro.avanza(durata)
            self._indice+=1
            if self._indice>=len(self._sequenza):
                if self._ripeti==1:
                    self.unload_sequence()
                    return None
                else:
                    self._indice=0
                    if self._ripeti>1:
                        self._ripeti-=1
            durata=self._sequenza[self._indice][1]
        return self._sequenza[self._indice][0]