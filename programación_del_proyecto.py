import serial, time, random
from tkinter import *
from tkinter import messagebox

# Mapeo de caracteres Morse a texto normal
# Incluye letras, números y operadores básicos para el juego
MORSE_DICT = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
    '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
    '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
    '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
    '-.--': 'Y', '--..': 'Z',
    '.----': '1', '..---': '2', '...--': '3', '....-': '4', '.....': '5',
    '-....': '6', '--...': '7', '---..': '8', '----.': '9', '-----': '0',
    '.-.-.': '+', '-....-': '-'
}

# Configuración del puerto serie 
PUERTO = 'COM3' 

try:
    # Intentamos abrir la comunicación con el Arduino
    arduino = serial.Serial(PUERTO, 9600, timeout=0.1)
    conectado = True
except:
    # Si falla, el programa sigue pero sin comunicación física
    arduino = None
    conectado = False

class JuegoMorse:
    def __init__(self, root):
        self.root = root
        self.root.title("DUELO MORSE: PC vs MAQUETA")
        self.root.geometry("800x750")

        # Configuración inicial de variables del juego
        self.lista_palabras = ["HOLA", "SOS", "1+1", "9-2", "CASA", "SI-NO", "PAZ", "3-1"]
        self.ronda_actual = 0
        self.puntos_pc = 0
        self.puntos_ard = 0
        self.objetivo = ""
        self.turno = "ESPERANDO"
        self.prog_pc = ""
        self.prog_ard = ""
        self.t_presion = 0
        self.t_suelto = time.time()
        self.morse_actual = ""
        self.activo = False
        
        self.modo_dictado = StringVar(value="A")
        
        # --- DISEÑO DE LA INTERFAZ ---
        
        # Selector de modo (Solo sonido, solo luz o ambos)
        config_frame = LabelFrame(root, text=" Modo de Dictado ", padx=10, pady=10)
        config_frame.pack(pady=10)
        Radiobutton(config_frame, text="Sonido", variable=self.modo_dictado, value="B").pack(side=LEFT, padx=10)
        Radiobutton(config_frame, text="LED", variable=self.modo_dictado, value="L").pack(side=LEFT, padx=10)
        Radiobutton(config_frame, text="Ambos", variable=self.modo_dictado, value="A").pack(side=LEFT, padx=10)
        
        # Marcador principal de puntos
        self.info_frame = Frame(root, bg="#2c3e50", pady=10)
        self.info_frame.pack(fill=X)
        self.lbl_score = Label(self.info_frame, text="MARCADOR -> PC: 0 | MAQUETA: 0", font=("Arial", 16, "bold"), fg="#f1c40f", bg="#2c3e50")
        self.lbl_score.pack()

        self.btn = Button(root, text="INICIAR RONDA", font=("Arial", 14, "bold"), bg="#27ae60", fg="white", command=self.nueva_ronda)
        self.btn.pack(pady=20)
        
        self.lbl_turno = Label(root, text="Pulsa para empezar", font=("Arial", 12, "italic"))
        self.lbl_turno.pack()

        # Visualización de la palabra a adivinar (se muestra oculta inicialmente)
        self.lbl_palabra = Label(root, text="----", font=("Courier", 50, "bold"), fg="#34495e")
        self.lbl_palabra.pack(pady=20)

        # Paneles divididos para Jugador 1 y Jugador 2
        f_principal = Frame(root)
        f_principal.pack(pady=10)

        # Sección del PC
        self.p1 = LabelFrame(f_principal, text=" JUGADOR 1 (PC) ", font=("Arial", 12, "bold"), padx=20, pady=20, fg="blue")
        self.p1.grid(row=0, column=0, padx=20)
        Label(self.p1, text="Usa la tecla CTRL IZQ").pack()
        self.res_pc = Label(self.p1, text="", font=("Arial", 40, "bold"), fg="blue", width=8)
        self.res_pc.pack()
        
        # Sección de la Maqueta
        self.p2 = LabelFrame(f_principal, text=" JUGADOR 2 (MAQUETA) ", font=("Arial", 12, "bold"), padx=20, pady=20, fg="green")
        self.p2.grid(row=0, column=1, padx=20)
        Label(self.p2, text="Usa el botón físico").pack()
        self.res_ard = Label(self.p2, text="", font=("Arial", 40, "bold"), fg="green", width=8)
        self.res_ard.pack()

        # Eventos del teclado para controlar la entrada del PC
        root.bind("<Control_L>", self.press)
        root.bind("<KeyRelease-Control_L>", self.release)
        
        # Lanzamiento del bucle de actualización
        self.loop()

    def nueva_ronda(self):
        # Reinicio de valores para la nueva partida
        self.ronda_actual += 1
        self.objetivo = random.choice(self.lista_palabras).upper()
        
        if conectado:
            arduino.write("CLEAR\n".encode())
            # Comando D_ modo:palabra
            arduino.write(f"D_{self.modo_dictado.get()}:{self.objetivo}\n".encode())
            
        self.prog_pc = ""
        self.prog_ard = ""
        self.morse_actual = ""
        self.res_pc.config(text="")
        self.res_ard.config(text="")
        self.turno = "DICTADO"
        self.lbl_palabra.config(text="*" * len(self.objetivo))
        self.btn.config(state="disabled")
        self.lbl_turno.config(text="ESCUCHANDO DICTADO LENTO...")

    def press(self, e):
        # Registra el momento en que se presiona CTRL
        if self.turno == "PC" and self.t_presion == 0:
            self.t_presion = time.time()
            self.activo = True
            if conectado: arduino.write("B_ON\n".encode())

    def release(self, e):
        # Calcula la duración de la pulsación para diferenciar . de -
        if self.turno == "PC" and self.t_presion != 0:
            if conectado: arduino.write("B_OFF\n".encode())
            dur = time.time() - self.t_presion
            
            # Lógica de tiempos: menos de 1.5s es punto, más es raya
            if dur > 0.1: 
                self.morse_actual += "-" if dur > 1.5 else "."
            
            self.t_presion = 0
            self.t_suelto = time.time()

    def loop(self):
        # Lectura de datos provenientes del Arduino
        if conectado and arduino.in_waiting > 0:
            linea = arduino.readline().decode('utf-8', errors='ignore').strip()
            
            # READY indica que el Arduino terminó de dictar la palabra
            if linea == "READY" and self.turno == "DICTADO":
                self.turno = "PC"
                self.lbl_turno.config(text="TU TURNO (PC) - CTRL IZQ")
            
            # Si es el turno de la maqueta, procesamos las letras recibidas
            elif self.turno == "ARDUINO" and len(linea) >= 1:
                self.prog_ard += linea
                self.res_ard.config(text=self.prog_ard)
                # Validar si la letra es correcta respecto al objetivo
                if linea == self.objetivo[len(self.prog_ard)-1]: self.puntos_ard += 1
                self.lbl_score.config(text=f"MARCADOR -> PC: {self.puntos_pc} | MAQUETA: {self.puntos_ard}")
                
                if len(self.prog_ard) == len(self.objetivo): 
                    self.root.after(1000, self.finalizar_ronda)

        # Procesamiento de la letra escrita por el PC tras un tiempo de silencio 
        if self.turno == "PC" and self.activo and self.morse_actual != "" and (time.time() - self.t_suelto > 2.5):
            letra_p = MORSE_DICT.get(self.morse_actual, "?")
            
            if len(self.prog_pc) < len(self.objetivo):
                self.prog_pc += letra_p
                self.res_pc.config(text=self.prog_pc)
                if letra_p == self.objetivo[len(self.prog_pc)-1]:
                    self.puntos_pc += 1
                    # Enviamos la letra al Arduino para que se vea en su matriz
                    if conectado: arduino.write((letra_p + "\n").encode())
            
            self.morse_actual = ""
            self.activo = False
            self.lbl_score.config(text=f"MARCADOR -> PC: {self.puntos_pc} | MAQUETA: {self.puntos_ard}")
            
            # Cambio de turno automático cuando el PC termina su palabra
            if len(self.prog_pc) == len(self.objetivo):
                self.turno = "ARDUINO"
                self.lbl_turno.config(text="TURNO JUGADOR 2 (BOTÓN FÍSICO)")
                if conectado: self.root.after(500, lambda: arduino.write("CLEAR\n".encode()))

        # El bucle se repite cada 50ms para no saturar el procesador
        self.root.after(50, self.loop)

    def finalizar_ronda(self):
        # Muestra resultados al terminar todos los turnos
        messagebox.showinfo("Ronda Terminada", f"Resultados actuales:\nPC: {self.puntos_pc}\nMaqueta: {self.puntos_ard}")
        self.btn.config(state="normal", text="SIGUIENTE RONDA")
        self.turno = "ESPERANDO"
        self.lbl_turno.config(text="Pulsa para iniciar la siguiente")

# Ejecución de la aplicación
root = Tk()
app = JuegoMorse(root)
root.mainloop()
