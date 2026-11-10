from machine import ADC, Pin
import time

class AtDC:
    """
    Questa classe modella un Analog to Digital Converter.
    Espone i metodi costruttore(n,min,max), read(), value(), value_between(min,max)
    Ricordati che l'ADC legge la tensione di segnali analogici continui.
    """

    def __init__(self, n, min_value=0, max_value=100):
        """
        Inizializza una nuove istanza.
        :parameter n Il pin che opera come ADC.
        :parameter min_value Il valore minimo della lettura normalizzata
        :parameter max_value Il valore massimo della lettura normalizzata
        """
        if(n < 0 or n > 39):
            self.__fatalError(1, n)
        elif(n in (0, 2, 4, 12, 13, 14, 15, 25, 26, 27)):
            print("--- WARNING: stai usando i pin del gruppo ADC2! Se stai usando il wifi allora l'ADC non funziona!")
        elif(not 32 <= n <= 39):
            self.__fatalError(2, n)
        if min_value >= max_value:
            self.__fatalError(3, min_value, max_value)
        self.adc = ADC(Pin(n))
        self.adc.atten(ADC.ATTN_11DB)
        self.min_value = min_value
        self.max_value = max_value

        
    def __fatalError(self, err, arg, arg2=0):
        """PRIVATO. Arresta il sistema se succede qualcosa di inaspettato"""
        print("--- ERRORE ---")
        if (err == 1):
            raise Exception(f"Il pin {arg} non è un pin valido!")
        elif (err == 2):
            raise Exception(f"Il pin {arg} non è utilizzabile per un ADC!")
        elif (err == 3):
            raise Exception(f"L'argomento {arg} è maggiore di {arg2}. Inverti i valori o cambiali!")

    def read(self):
        """
        Legge direttamente il valore della tensione.
        :return un valore tra 0 e 4095.
        """
        return self.adc.read()

    def value(self):
        """
        Legge il valore della tensione normalizzato.
        :return un valore tra min e max.
        """
        return self.min_value + (self.max_value - self.min_value) * self.read() / 4095
        
    def value_between(self, min_v, max_v):
        """
        Legge direttamente il valore della tensione normalizzato tra min e max passati
        :return un valore tra min e max specificati.
        """
        if min_v >= max_v:
            self.__fatalError(3, min_v, max_v)
        return min_v + (max_v - min_v) * self.read() / 4095