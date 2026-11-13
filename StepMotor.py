import time
from machine import Pin 

class StepMotor:
    """
    Questa classe modella un motore passo passo.
    Espone i metodi costruttore(pin1,pin2,pin3,pin4), step(direction, steps, delay, mode).
    NON attaccare i pin dell'esp al motore passo passo, attaccali al driver.
    Ricordati di collegare la massa del power supply alla massa dell'esp.
    Attaccami alla 5V
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
        """
        Inizializza una nuova istanza di un motore passo passo.
        :parameter pin1        Il primo pin di ingresso.
        :parameter pin2        Il secondo pin di ingresso.
        :parameter pin3        Il terzo pin di ingresso.
        :parameter pin4        Il quarto pin di ingresso.
        """
        pins=[pin1,pin2,pin3,pin4]
        self.stepper_pins=[]
        for i in pins:
            self.stepper_pins.append(Pin(self.__check_pin(i),Pin.OUT))
        
    def __check_pin(self,p):
        """
        PRIVATO. Controlla se il pin è accettabile per controllare le bobine di uno step motor.
        :parameter p Il numero del pin.
        :return il numero del pin. Può sollevare eccezioni.
        """
        if(p<0 or p>39):
            raise Exception(f"Il pin {p} non è un pin valido. Usa un pin tra 0 e 39!")
        if(6<=p<=11 or 34<=p<=39):
            raise Exception(f"Il pin {p} non è utilizzabile per un motore passo passo!")
        return p
        
    def step(self, direction, steps, delay, mode):
        """
        Effettua un numero preciso di step nel verso e nel delay selezionato.
        Ricordati che in modalità HALF servono 4096 passi, in modalità FULL ne servono 2048
        :parameter direction La direzione di rotazione. Valori ammessi: +1 (antiorario), -1 (orario).
        :parameter steps Il numero di passi da effettuare. Sono ammessi solo valori positivi
        :parameter delay Il ritardo in ms tra un passo e l'altro. Sono ammessi valori maggiori di 5.
        :parameter mode Il numero di passi da effettuare. Valori ammessi: "HALF", "FULL".
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
    
    def __is_mode_full_step(self,mode):
        """
        PRIVATO. Controlla che la modalità sia una stringa accettabile.
        :parameter mode la stringa, che può essere "FULL" o "HALF".
        :return true se mode=="FULL", false se mode=="HALF". Può lanciare eccezioni.
        """
        if (mode=="FULL"):
            return True
        elif(mode=="HALF"):
            return False
        else:
            raise Exception(f"La modalità {mode} non è valida. Usa le stringhe 'HALF' o 'FULL'!")
#------------------------------
    def step_rpm(self, direction, steps, rpm, mode):
        """
        Effettua un numero preciso di step nel verso alle RPM selezionate.
        Ricordati che in modalità HALF servono 4096 passi, in modalità FULL ne servono 2048
        :parameter direction La direzione di rotazione. Valori ammessi: +1 (antiorario), -1 (orario).
        :parameter steps Il numero di passi da effettuare. Sono ammessi solo valori positivi
        :parameter rpm Il numero di RPM. Sono ammessi valori positivi minori di 6.
        :parameter mode Il numero di passi da effettuare. Valori ammessi: "HALF", "FULL".
        """
        if(rpm>6 or rpm<=0):
            raise Exception(f"Il motore non può ruotare a {rpm} RPM. Usa un numero positivo minore di 6!")
        steps_per_round= 2048 if self.__is_mode_full_step(mode) else 4096
        self.step(direction, steps, 60_000/rpm/steps_per_round, mode)