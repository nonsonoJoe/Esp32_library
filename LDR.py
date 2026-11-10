from AtDC import AtDC
class LDR:
    """
    Questa classe modella un Fotoresistore (light dependent resistor). Un oggetto LDR è composto da un AtDC.
    Espone i metodi costruttore(n,min,max), read(), value(), value_between(min,max)
    Ricordati di importare anche la classe AtDC.
    """

    def __init__(self, n, min_value=0, max_value=100):
        """
        Inizializza una nuova istanza.
        :parameter n Il pin che va connesso al terminale di mezzo dell'LDR.
        :parameter min_value Il valore minimo della lettura normalizzata
        :parameter max_value Il valore massimo della lettura normalizzata
        """
        self.atdc=AtDC(n,min_value,max_value)
        

    def read(self):
        """
        Legge direttamente il valore della tensione.
        :return un valore tra 0 e 4095.
        """
        return self.atdc.read()

    def value(self):
        """
        Legge il valore della tensione normalizzato.
        :return un valore tra min e max.
        """
        return self.atdc.value()
        
    def value_between(self, min_v, max_v):
        """
        Legge direttamente il valore della tensione normalizzato tra min e max passati
        :return un valore tra min e max specificati.
        """
        return self.atdc.value_between(min_v,max_v)



