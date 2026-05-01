// ======================================================
// PROYECTO: SISTEMA DE COMUNICACIÓN MORSE PC-MAQUETA
// ======================================================

// Pines de control para periféricos básicos
const int boton = 17;   
const int buzzer = 19;  
const int ledDictado = 9; 

// Definición de pines para la matriz de LEDs (Filas y Columnas)
int filaLEDs[13] = {4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16};
int colLEDs[3] = {3, 2, 18}; 

// Tiempos estándar para la lógica de dictado y reconocimiento
const int tiempoPunto = 1000;       // Duración punto: 1 seg
const int tiempoRaya = 3000;        // Duración raya: 3 seg
const int espacioEntreSimbolos = 1000; // Pausa entre componentes de una misma letra
const int umbralCorte = 1500;       // Límite para diferenciar punto de raya al pulsar
const int esperaFinLetra = 3000;    // Tiempo muerto necesario para procesar el envío

// Variables de estado para el análisis de señales
String morseActual = "";
unsigned long tPresion = 0;
unsigned long tSuelto = 0;
bool procesando = false;

void setup() {
  // Inicialización de entradas y salidas
  pinMode(boton, INPUT); 
  pinMode(buzzer, OUTPUT);
  pinMode(ledDictado, OUTPUT);
  
  // Configuración masiva de pines de la matriz
  for (int i = 0; i < 13; i++) pinMode(filaLEDs[i], OUTPUT);
  for (int i = 0; i < 3; i++) pinMode(colLEDs[i], OUTPUT);
  
  // Comunicación con el script de Python
  Serial.begin(9600);
  apagarTodo(); // Estado inicial limpio
}

void loop() {
  // --- GESTIÓN DE COMANDOS DESDE LA PC ---
  if (Serial.available() > 0) {
    String entrada = Serial.readStringUntil('\n');
    entrada.trim();

    // Comandos directos de sonido/luz
    if (entrada == "B_ON") { digitalWrite(buzzer, HIGH); digitalWrite(ledDictado, HIGH); }
    else if (entrada == "B_OFF") { digitalWrite(buzzer, LOW); digitalWrite(ledDictado, LOW); }
    else if (entrada == "CLEAR") { apagarTodo(); }
    
    // Si llega un solo caracter, se muestra en la matriz
    else if (entrada.length() == 1) { encenderMatriz(toupper(entrada[0])); }
    
    // Lógica de dictado automático al iniciar ronda
    else if (entrada.startsWith("D_")) { 
      char modo = entrada[2]; // B=Buzzer, L=LED, A=Ambos
      String palabra = entrada.substring(4);
      for (int i = 0; i < palabra.length(); i++) {
        dictarLetra(toupper(palabra[i]), modo);
        delay(2000); // Separación entre letras de la palabra dictada
      }
      Serial.println("READY"); // Notifica a Python que terminó de dictar
    }
  }

  // --- LÓGICA DE ENTRADA MANUAL (BOTÓN FÍSICO) ---
  int lectura = digitalRead(boton);
  
  if (lectura == HIGH) { 
    // Feedback inmediato al presionar
    digitalWrite(buzzer, HIGH);
    digitalWrite(ledDictado, HIGH); 
    if (tPresion == 0) tPresion = millis(); // Marca de tiempo inicial
    procesando = true;
  } 
  else if (lectura == LOW && tPresion > 0) {
    // Al soltar, calculamos cuánto tiempo estuvo presionado
    digitalWrite(buzzer, LOW);
    digitalWrite(ledDictado, LOW);
    unsigned long duracion = millis() - tPresion;
    
    if (duracion > 100) { // Filtro anti-rebote básico
      morseActual += (duracion < umbralCorte) ? "." : "-";
    }
    tPresion = 0;
    tSuelto = millis();
  }

  // Si pasa suficiente tiempo sin pulsar, se traduce la cadena acumulada
  if (procesando && lectura == LOW && morseActual.length() > 0 && (millis() - tSuelto > esperaFinLetra)) {
    char letra = traducirMorse(morseActual);
    encenderMatriz(letra); 
    Serial.println(letra); // Envía la letra detectada a la PC
    morseActual = "";
    procesando = false;
  }
}

// Función para emitir señales visuales/auditivas según el modo
void dictarLetra(char c, char modo) {
  String caracteres = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890+-";
  String patrones[] = {
    ".-", "-...", "-.-.", "-..", ".", "..-.", "--.", "....", "..", ".---", "-.-", ".-..", "--", "-.", "---", ".--.", "--.-", ".-.", "...", "-", "..-", "...-", ".--", "-..-", "-.--", "--..",
    ".----", "..---", "...--", "....-", ".....", "-....", "--...", "---..", "----.", "-----", ".-.-.", "-....-"
  };
  
  int idx = caracteres.indexOf(c);
  if (idx != -1) {
    String codigo = patrones[idx];
    for (int j = 0; j < codigo.length(); j++) {
      int dur = (codigo[j] == '.' ? tiempoPunto : tiempoRaya);
      
      // Activa buzzer y/o LED según la configuración elegida en la interfaz
      if (modo == 'B' || modo == 'A') digitalWrite(buzzer, HIGH);
      if (modo == 'L' || modo == 'A') { digitalWrite(colLEDs[0], HIGH); digitalWrite(ledDictado, HIGH); }
      
      delay(dur); 
      
      digitalWrite(buzzer, LOW);
      digitalWrite(ledDictado, LOW);
      digitalWrite(colLEDs[0], LOW);
      
      delay(espacioEntreSimbolos); 
    }
  }
}

// Limpieza de todos los pines de salida
void apagarTodo() {
  for (int i = 0; i < 13; i++) digitalWrite(filaLEDs[i], LOW);
  for (int i = 0; i < 3; i++) digitalWrite(colLEDs[i], LOW);
  digitalWrite(ledDictado, LOW);
  digitalWrite(buzzer, LOW);
}

// Diccionario de traducción de cadenas Morse a caracteres
char traducirMorse(String c) {
  if (c == ".-") return 'A'; if (c == "-...") return 'B'; if (c == "-.-.") return 'C';
  if (c == "-..") return 'D'; if (c == ".") return 'E'; if (c == "..-.") return 'F';
  if (c == "--.") return 'G'; if (c == "....") return 'H'; if (c == "..") return 'I';
  if (c == ".---") return 'J'; if (c == "-.-") return 'K'; if (c == ".-..") return 'L';
  if (c == "--") return 'M'; if (c == "-.") return 'N'; if (c == "---") return 'O';
  if (c == ".--.") return 'P'; if (c == "--.-") return 'Q'; if (c == ".-.") return 'R';
  if (c == "...") return 'S'; if (c == "-") return 'T'; if (c == "..-") return 'U';
  if (c == "...-") return 'V'; if (c == ".--") return 'W'; if (c == "-..-") return 'X';
  if (c == "-.--") return 'Y'; if (c == "--..") return 'Z';
  if (c == ".----") return '1'; if (c == "..---") return '2'; if (c == "...--") return '3';
  if (c == "....-") return '4'; if (c == ".....") return '5'; if (c == "-....") return '6';
  if (c == "--...") return '7'; if (c == "---..") return '8'; if (c == "----.") return '9';
  if (c == "-----") return '0'; if (c == ".-.-.") return '+'; if (c == "-....-") return '-';
  return '?';
}

// Control de la matriz de LEDs para representar visualmente la letra
void encenderMatriz(char c) {
  apagarTodo();
  int f = -1, col = -1;
  // Organización por grupos para facilitar el mapeo en la matriz física
  String f1 = "ACEGIKMOSQUWY", f2 = "BDFHJLNPTRVXZ";
  
  if (f1.indexOf(c) != -1) { col = 0; f = f1.indexOf(c); }
  else if (f2.indexOf(c) != -1) { col = 1; f = f2.indexOf(c); }
  
  // Si es letra conocida, activa fila y columna correspondiente
  if (f >= 0 && col >= 0) { 
    digitalWrite(filaLEDs[f], HIGH); 
    digitalWrite(colLEDs[col], HIGH); 
  }
  // Para caracteres especiales o números, solo usamos el LED de dictado como indicador
  else if (c != '?') { 
    digitalWrite(ledDictado, HIGH); 
  }
}