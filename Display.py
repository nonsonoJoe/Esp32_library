from machine import Pin, I2C
import ssd1306
import framebuf

class Display:
   """!
    @brief Incapsula un display OLED SSD1306 collegato tramite bus I2C.

    @details La classe crea il bus I2C e il driver ssd1306.SSD1306_I2C e ne espone
    le operazioni di disegno utilizzate dal progetto: testo, rettangoli, riempimenti,
    immagini monocromatiche, intestazione con linea separatrice e area contenuto.

    I metodi di disegno modificano soltanto il buffer in memoria: il risultato compare
    sul display solo dopo la chiamata a show() (o a clear(), che aggiorna subito lo
    schermo). Colori: 1 = pixel acceso, 0 = pixel spento.

    I valori predefiniti (128x64 pixel, SCL = 22, SDA = 21, bus I2C 0) sono quelli del
    file sorgente.
    """

    ## @brief Larghezza predefinita del display (int, pixel). Usata se il costruttore
    #  non riceve un valore esplicito.
    DEFAULT_WIDTH = 128

    ## @brief Altezza predefinita del display (int, pixel). Usata se il costruttore
    #  non riceve un valore esplicito.
    DEFAULT_HEIGHT = 64

    ## @brief Pin GPIO predefinito della linea SCL (int). Usato per creare il bus I2C.
    DEFAULT_SCL_PIN = 22

    ## @brief Pin GPIO predefinito della linea SDA (int). Usato per creare il bus I2C.
    DEFAULT_SDA_PIN = 21

    ## @brief Identificativo predefinito del bus I2C (int, 0 o 1). Usato per creare il bus.
    DEFAULT_I2C_ID = 0

    ## @brief Coordinata y (int, pixel) della linea che separa l'intestazione
    #  dal contenuto. Usata da draw_header().
    SEPARATOR_Y = 10

    ## @brief Coordinata y (int, pixel) da cui inizia l'area contenuto, sotto
    #  l'intestazione. Usata da clear_content().
    CONTENT_TOP = 12

    ## @brief Numero massimo di GPIO dell'ESP32 (int). Limite superiore dei pin validi.
    MAX_GPIO = 39

    ## @brief Pin collegati alla flash SPI interna (tuple di int). Non utilizzabili
    #  per SCL e SDA. Usata da _check_pins().
    FLASH_PINS = (6, 7, 8, 9, 10, 11)

    ## @brief Numeri tra 0 e 39 che non corrispondono a un GPIO dell'ESP32
    #  (tuple di int). Non utilizzabili per SCL e SDA. Usata da _check_pins().
    MISSING_PINS = (24, 28, 29, 30, 31)

    ## @brief Pin solo ingresso (tuple di int). Non utilizzabili per SCL e SDA,
    #  che devono poter comandare anche l'uscita. Usata da _check_pins().
    INPUT_ONLY_PINS = (34, 35, 36, 37, 38, 39)

    def __init__(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, scl_pin=DEFAULT_SCL_PIN, sda_pin=DEFAULT_SDA_PIN, i2c_id=DEFAULT_I2C_ID):
        """!
        @brief Inizializza il bus I2C e il driver del display.

        @param width Larghezza del display in pixel.
        @param height Altezza del display in pixel.
        @param scl_pin Numero del pin GPIO collegato a SCL.
        @param sda_pin Numero del pin GPIO collegato a SDA.
        @param i2c_id Identificativo del bus I2C (0 o 1).

        @exception TypeError se scl_pin o sda_pin non sono numeri interi.
        @exception ValueError se scl_pin o sda_pin non sono utilizzabili per
        l'I2C su un ESP32 oppure sono uguali (vedi _check_pins()).
        @exception OSError Sollevata dal bus I2C se il display non risponde
        (ad esempio cablaggio errato o indirizzo non raggiungibile).
        """
        self._check_pins(scl_pin, sda_pin)

        ## @brief Larghezza del display (int, pixel). Usata per i calcoli di
        #  layout e come larghezza predefinita delle immagini.
        self.width = width

        ## @brief Altezza del display (int, pixel). Usata per i calcoli di
        #  layout e come altezza predefinita delle immagini.
        self.height = height

        self._i2c = I2C(i2c_id, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self._display = ssd1306.SSD1306_I2C(width, height, self._i2c)

    def _check_pins(self, scl_pin, sda_pin):
        """!
        @brief PRIVATO. Controlla se i pin scelti vanno bene per il bus I2C del display.

        @details SCL e SDA devono essere GPIO esistenti dell'ESP32, non collegati alla
        flash interna e capaci di comandare un'uscita (i pin 34-39 sono solo ingresso).
        I due pin devono inoltre essere diversi tra loro.

        @param scl_pin Numero del pin collegato a SCL.
        @param sda_pin Numero del pin collegato a SDA.
        @exception TypeError se un pin non e' un numero intero.
        @exception ValueError se un pin e' fuori dall'intervallo 0-39, non esiste,
        e' collegato alla flash, e' solo ingresso, oppure SCL e SDA coincidono.
        """
        for name, p in (("SCL", scl_pin), ("SDA", sda_pin)):
            if not isinstance(p, int):
                raise TypeError(f"Il pin {name} deve essere un numero intero, ricevuto: {p!r}")
            if p < 0 or p > self.MAX_GPIO:
                raise ValueError(f"Il pin {p} ({name}) non e' valido. Usa un pin tra 0 e {self.MAX_GPIO}!")
            if p in self.MISSING_PINS:
                raise ValueError(f"Il pin {p} ({name}) non esiste sull'ESP32!")
            if p in self.FLASH_PINS:
                raise ValueError(f"Il pin {p} ({name}) e' collegato alla flash interna e non e' utilizzabile!")
            if p in self.INPUT_ONLY_PINS:
                raise ValueError(f"Il pin {p} ({name}) e' solo ingresso: per l'I2C serve un pin che possa anche comandare l'uscita!")
        if scl_pin == sda_pin:
            raise ValueError(f"SCL e SDA non possono usare lo stesso pin ({scl_pin})!")

    def fill(self, colour=0):
        """!
        @brief Riempie l'intero buffer con un colore, senza aggiornare il display.

        @param colour 0 per spegnere tutti i pixel, 1 per accenderli.
        """
        self._display.fill(colour)

    def clear(self):
        """!
        @brief Spegne tutti i pixel e aggiorna subito il display.
        """
        self._display.fill(0)
        self._display.show()

    def clear_content(self):
        """!
        @brief Cancella l'area sotto l'intestazione, lasciando intatta l'intestazione.

        @details L'area parte dalla riga CONTENT_TOP e arriva al bordo inferiore.
        """
        self._display.fill_rect(0, self.CONTENT_TOP, self.width, self.height - self.CONTENT_TOP, 0)

    def draw_header(self, title):
        """!
        @brief Disegna un titolo in alto a sinistra e una linea separatrice sotto di esso.

        @param title Testo del titolo (font integrato del driver, 8x8 pixel per carattere).
        """
        self._display.text(title, 0, 0, 1)
        self._display.rect(0, self.SEPARATOR_Y, self.width, 1, 1)

    def text(self, string, x, y, colour=1):
        """!
        @brief Scrive una riga di testo nel buffer.

        @param string Testo da scrivere.
        @param x Coordinata orizzontale del primo carattere, in pixel.
        @param y Coordinata verticale del bordo superiore del testo, in pixel.
        @param colour 1 per testo acceso, 0 per testo spento (utile su sfondo acceso).
        """
        self._display.text(string, x, y, colour)

    def rect(self, x, y, width, height, colour=1):
        """!
        @brief Disegna il contorno di un rettangolo nel buffer.

        @param x Coordinata orizzontale dell'angolo in alto a sinistra.
        @param y Coordinata verticale dell'angolo in alto a sinistra.
        @param width Larghezza del rettangolo in pixel.
        @param height Altezza del rettangolo in pixel.
        @param colour 1 per pixel accesi, 0 per pixel spenti.
        """
        self._display.rect(x, y, width, height, colour)

    def fill_rect(self, x, y, width, height, colour=1):
        """!
        @brief Disegna un rettangolo pieno nel buffer.

        @details Utile anche per cancellare una zona precisa (colour = 0) prima di
        riscrivere un testo che cambia.

        @param x Coordinata orizzontale dell'angolo in alto a sinistra.
        @param y Coordinata verticale dell'angolo in alto a sinistra.
        @param width Larghezza del rettangolo in pixel.
        @param height Altezza del rettangolo in pixel.
        @param colour 1 per pixel accesi, 0 per pixel spenti.
        """
        self._display.fill_rect(x, y, width, height, colour)

    def draw_image(self, buffer, x=0, y=0, width=None, height=None):
        """!
        @brief Cancella il buffer e vi disegna un'immagine monocromatica.

        @details Il buffer deve essere in formato MONO_HLSB (un bit per pixel, righe
        orizzontali, bit piu' significativo a sinistra) e deve contenere
        width * height / 8 byte. Il costruttore di framebuf richiede un buffer
        scrivibile (bytearray): se le immagini sono di tipo bytes, convertirle con
        bytearray() prima di chiamare il metodo. Il buffer del display viene svuotato
        prima del disegno, come nel sorgente originale.

        @param buffer Dati dell'immagine (bytearray).
        @param x Coordinata orizzontale in cui disegnare l'immagine.
        @param y Coordinata verticale in cui disegnare l'immagine.
        @param width Larghezza dell'immagine in pixel; se None usa la larghezza del display.
        @param height Altezza dell'immagine in pixel; se None usa l'altezza del display.
        @exception Exception Eventuali errori di framebuf per buffer non compatibili
        con le dimensioni indicate (il tipo esatto dipende dal firmware).
        """
        if width is None:
            width = self.width
        if height is None:
            height = self.height
        frame = framebuf.FrameBuffer(buffer, width, height, framebuf.MONO_HLSB)
        self._display.fill(0)
        self._display.blit(frame, x, y)

    def show(self):
        """!
        @brief Trasferisce il buffer al display, rendendo visibili le modifiche.
        """
        self._display.show()