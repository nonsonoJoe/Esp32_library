import time
from machine import Pin # type: ignore
from Cronometro import Cronometro

class StepMotor:
    """!
    @brief Questa classe modella un motore passo passo collegato a un driver a 4 ingressi.
    
    @details Espone il costruttore StepMotor(pin1, pin2, pin3, pin4) e due famiglie di metodi:
    - NON bloccanti: move(), move_rpm(), async_execute(), stop() e rilascia(). Il movimento
      viene fatto a piccoli passi chiamando async_execute() a intervalli brevi e regolari
      nel loop principale.
    - bloccanti: step() e step_rpm(), che aspettano la fine del movimento.
    
    Il ritmo dei passi è misurato con un Cronometro. Il Sequenziatore non è usato di proposito:
    se il loop è in ritardo, il Sequenziatore salta i passi scaduti, mentre un motore passo passo
    deve eseguire ogni singolo passo per non perdere la posizione.
    
    Se il loop è in ritardo il motore rallenta (tra due passi passa sempre almeno delay ms)
    invece di eseguire passi in raffica, che il rotore non riuscirebbe a seguire.
    In modalità FULL servono 2048 passi per un giro, in modalità HALF ne servono 4096.
    
    @warning NON attaccare i pin dell'ESP32 direttamente al motore: vanno attaccati al driver.
    La massa dell'alimentatore va collegata alla massa dell'ESP32. Il motore va alimentato a 5V.
    """
    # full-step con 2 bobine attive per ogni step
    # due bobine accese per ogni step -> più coppia
    # il valore (0=spento, 1=acceso) da dare a quel pin nel passo corrente.
    step_sequence = [
        [1, 0, 0, 1],  
        [1, 1, 0, 0],  
        [0, 1, 1, 0],  
        [0, 0, 1, 1],  
    ]#4 step
    # la half-step corrispondente (8 stati) è questa:
    # Half-step (mezzo passo): alterna 1 bobina e 2 bobine
    step_sequence_half= [
        [1,1,0,0],  # IN1+IN2
        [0,1,0,0],  # solo IN2
        [0,1,1,0],  # IN2+IN3
        [0,0,1,0],  # solo IN3
        [0,0,1,1],  # IN3+IN4
        [0,0,0,1],  # solo IN4
        [1,0,0,1],  # IN1+IN4
        [1,0,0,0],  # solo IN1
    ]#8 step
    
    def __init__(self, pin1,pin2,pin3,pin4):
        """!
        @brief Inizializza una nuova istanza di un motore passo passo.
        
        @param pin1 Il primo pin di ingresso del driver.
        @param pin2 Il secondo pin di ingresso del driver.
        @param pin3 Il terzo pin di ingresso del driver.
        @param pin4 Il quarto pin di ingresso del driver.
        
        @exception Exception se un pin non è valido o non è utilizzabile.
        """
        pins=[pin1,pin2,pin3,pin4]
        ## Lista dei 4 pin di uscita che pilotano il driver
        self.stepper_pins=[]
        for i in pins:
            self.stepper_pins.append(Pin(self.__check_pin(i),Pin.OUT))
        ## Cronometro che misura il tempo dall'ultimo passo
        self._cronometro=Cronometro()
        ## Sequenza di bobine in uso (full o half step), None se nessun movimento è stato avviato
        self._lista=None
        ## Verso di rotazione (+1 o -1)
        self._direzione=1
        ## Passi ancora da eseguire
        self._rimanenti=0
        ## Tempo minimo in ms tra due passi
        self._delay=0
        ## Riga corrente della sequenza di bobine
        self._indice=0
        
    def __check_pin(self,p):
        """!
        @brief PRIVATO. Controlla se il pin è accettabile per controllare le bobine di un motore passo passo.
        
        @param p Il numero del pin.
        
        @return Il numero del pin.
        
        @exception Exception se il pin non è tra 0 e 39 o se è tra quelli non utilizzabili (6-11 e 34-39).
        """
        if(p<0 or p>39):
            raise Exception(f"Il pin {p} non è un pin valido. Usa un pin tra 0 e 39!")
        if(6<=p<=11 or 34<=p<=39):
            raise Exception(f"Il pin {p} non è utilizzabile per un motore passo passo!")
        return p

#---------------------------- BLOCCANTI
    def step(self, direction, steps, delay, mode):
        """!
        @brief Effettua un numero preciso di passi nel verso e nel delay selezionato (BLOCCANTE).
        @details Il metodo ritorna solo a movimento finito. Usa move() e async_execute().
        Ricorda che in modalità HALF servono 4096 passi per un giro, in modalità FULL ne servono 2048.
        @param direction La direzione di rotazione. Valori ammessi: +1 (antiorario), -1 (orario).
        @param steps Il numero di passi da effettuare. Sono ammessi solo valori non negativi.
        @param delay Il ritardo in ms tra un passo e l'altro. Sono ammessi valori di almeno 5.
        @param mode La modalità. Valori ammessi: "HALF", "FULL".
        @exception ValueError se direction, steps o delay non sono validi.
        @exception Exception se mode non è valido.
        """
        lista=[]
        if(self.__is_mode_full_step(mode)):
            lista=self.step_sequence
        else:
            lista=self.step_sequence_half            
        if(direction not in [-1,1]):
            raise Exception(f"La direzione {direction} non è valida. Usa +1 o -1!")
        if(steps<0):
            raise Exception(f"Non puoi eseguire {steps} passi. Usa un numero positivo!")
        if(delay<5):
            raise Exception(f"Non puoi avere un delay minore di {delay}ms!")
        
        step_index=0
        for i in range(steps):
            # l'operatore % garantisce che step_index rimanga all'interno dell'intervallo valido,
            # assicurando che la sequenza dei passi venga ripetuta ciclicamente.
            # indica la riga quindi quale passo
            step_index = (step_index + direction) % len(lista)
            #pin_index determina la colonna (quindi la bobbina)
            for pin_index in range(len(self.stepper_pins)):
                #Esempio: se step_index = 2, la sequenza è [0, 1, 1, 0]
                # Se pin_index = 0 → pin_value = 0
                # Se pin_index = 1 → pin_value = 1
                # Se pin_index = 2 → pin_value = 1
                # Se pin_index = 3 → pin_value = 0
                pin_value = lista[step_index][pin_index]
                #Scrive il valore sul pin fisico, accendendo o spegnendo la bobina
                self.stepper_pins[pin_index].value(pin_value)
            
            #Aspetta il tempo delay prima di passare al prossimo passo.
            #Pausa più corta → motore più veloce. Pausa più lunga → motore più lento.
            time.sleep_ms(delay)
    
    def step_rpm(self, direction, steps, rpm, mode):
        """!
        @brief Effettua un numero preciso di passi nel verso alle RPM selezionate (BLOCCANTE).
        @details Il metodo ritorna solo a movimento finito. Usa move_rpm() e async_execute().
        Ricorda che in modalità HALF servono 4096 passi per un giro, in modalità FULL ne servono 2048.
        @param direction La direzione di rotazione. Valori ammessi: +1 (antiorario), -1 (orario).
        @param steps Il numero di passi da effettuare. Sono ammessi solo valori non negativi.
        @param rpm Il numero di RPM. Vedi move_rpm() per il massimo.
        @param mode La modalità. Valori ammessi: "HALF", "FULL".
        @exception ValueError per gli stessi motivi di move_rpm().
        @exception Exception se mode non è valido.
        """
        if(rpm>6 or rpm<=0):
            raise Exception(f"Il motore non può ruotare a {rpm} RPM. Usa un numero positivo minore di 6!")
        steps_per_round= 2048 if self.__is_mode_full_step(mode) else 4096
        self.step(direction, steps, 60_000/rpm/steps_per_round, mode)

    def __is_mode_full_step(self,mode):
            """!
            @brief PRIVATO. Controlla che la modalità sia una stringa accettabile.
            
            @param mode La stringa, che può essere "FULL" o "HALF".
            
            @return True se mode è "FULL", False se mode è "HALF".
            
            @exception Exception se mode non è "FULL" né "HALF".
            """
            if (mode=="FULL"):
                return True
            elif(mode=="HALF"):
                return False
            else:
                raise Exception(f"La modalità {mode} non è valida. Usa le stringhe 'HALF' o 'FULL'!")
    
#---------------------------- NON BLOCCANTI
    def move(self, direction, steps, delay, mode):
        """!
        @brief Avvia un movimento in modo NON bloccante.
        @details Il primo passo è eseguito subito, gli altri da async_execute().
        Se un movimento era già in corso, viene sostituito senza preavviso.
        Ricorda che in modalità HALF servono 4096 passi per un giro, in modalità FULL ne servono 2048.
        @param direction La direzione di rotazione. Valori ammessi: +1 (antiorario), -1 (orario).
        @param steps Il numero di passi da effettuare. Sono ammessi solo valori non negativi.
        @param delay Il tempo minimo in ms tra un passo e l'altro. Sono ammessi valori di almeno 5.
        @param mode La modalità. Valori ammessi: "HALF", "FULL".
        @exception ValueError se direction, steps o delay non sono validi.
        @exception Exception se mode non è valido.
        """
        if(self.__is_mode_full_step(mode)):
            lista=self.step_sequence
        else:
            lista=self.step_sequence_half
        if(direction not in (-1,1)):
            raise ValueError(f"La direzione {direction} non è valida. Usa +1 o -1!")
        if(steps<0):
            raise ValueError(f"Non puoi eseguire {steps} passi. Usa un numero non negativo!")
        if(delay<5):
            raise ValueError(f"Il delay di {delay}ms è troppo basso. Usa almeno 5ms!")

        self._lista=lista
        self._direzione=direction
        self._rimanenti=steps
        self._delay=delay
        self._indice=0
        if steps>0:
            self._fai_passo()
            self._cronometro.start()
        else:
            self._cronometro.stop()

    def move_rpm(self, direction, steps, rpm, mode):
        """!
        @brief Avvia un movimento in modo NON bloccante alle RPM selezionate.
        @details Il delay tra i passi è calcolato dalle RPM (vedi move()).
        Con il delay minimo di 5ms le RPM massime sono circa 5.86 in FULL e 2.93 in HALF.
        @param direction La direzione di rotazione. Valori ammessi: +1 (antiorario), -1 (orario).
        @param steps Il numero di passi da effettuare. Sono ammessi solo valori non negativi.
        @param rpm Il numero di RPM. Sono ammessi valori positivi, entro il massimo della modalità.
        @param mode La modalità. Valori ammessi: "HALF", "FULL".
        @exception ValueError se rpm non è positivo o supera il massimo della modalità,
        oppure per gli stessi motivi di move().
        @exception Exception se mode non è valido.
        """
        if(rpm<=0):
            raise ValueError(f"Il motore non può ruotare a {rpm} RPM. Usa un numero positivo!")
        steps_per_round= 2048 if self.__is_mode_full_step(mode) else 4096
        delay=60_000/rpm/steps_per_round
        if(delay<5):
            massimo=60_000/5/steps_per_round
            raise ValueError(f"{rpm} RPM sono troppi in modalità {mode}: il massimo è {massimo:.2f} RPM!")
        self.move(direction, steps, delay, mode)

    
    def async_execute(self):
        """!
        @brief Esegue il movimento avviato con move() in maniera non bloccante.
        @details Va chiamato ripetutamente a breve distanza dal loop principale.
        Esegue un solo passo per chiamata e solo se è passato almeno delay ms dal precedente.
        Al termine le bobine restano alimentate (il rotore è bloccato): per liberarlo usare rilascia().
        @return True se non c'è nulla in corso o se il movimento è appena terminato,
        False se il movimento è ancora in corso.
        """
        if not self._cronometro.attivo():
            return True
        if self._cronometro.scaduto(self._delay):
            if self._rimanenti==0:
                self._cronometro.stop()
                return True
            self._fai_passo()
            self._cronometro.start()
        return False

    def stop(self):
        """!
        @brief Interrompe il movimento in corso.
        @details Le bobine restano alimentate, quindi il rotore resta bloccato.
        """
        self._cronometro.stop()
        self._rimanenti=0

    def rilascia(self):
        """!
        @brief Interrompe il movimento in corso e spegne tutte le bobine.
        @details Il rotore è libero e il motore non scalda.
        """
        self.stop()
        for pin in self.stepper_pins:
            pin.value(0)
            
    def _fai_passo(self):
        """!
        @brief PRIVATO. Passa alla riga successiva della sequenza e la scrive sui pin.
        @details L'operatore % mantiene l'indice nell'intervallo valido, così la sequenza
        dei passi viene ripetuta ciclicamente. Decrementa i passi rimanenti.
        """
        self._indice=(self._indice+self._direzione)%len(self._lista)
        riga=self._lista[self._indice]
        for i in range(len(self.stepper_pins)):
            self.stepper_pins[i].value(riga[i])
        self._rimanenti-=1

    def __is_mode_full_step(self,mode):
        """!
        @brief PRIVATO. Controlla che la modalità sia una stringa accettabile.
        @param mode La stringa, che può essere "FULL" o "HALF".
        @return True se mode è "FULL", False se mode è "HALF".
        @exception Exception se mode non è "FULL" né "HALF".
        """
        if (mode=="FULL"):
            return True
        elif(mode=="HALF"):
            return False
        else:
            raise Exception(f"La modalità {mode} non è valida. Usa le stringhe 'HALF' o 'FULL'!")
