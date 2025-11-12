import cv2
import time
import serial
from LPR import LPR
import pytesseract

# ================= CONFIGURACIÓN =================
# Ruta a Tesseract (ajusta si es distinta)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Lista de matrículas permitidas (en mayúsculas)
AUTHORIZED_PLATES = {"AAAAAA", "BOA", "HOLA", "LAO57O", "804A57", "ABCDEX"}

# Puerto del Arduino
SERIAL_PORT = "COM6"    # ⚠️ CAMBIA según tu puerto (ej: COM4, COM6...)
BAUD_RATE = 9600

# Cámara
CAMERA_INDEX = 0        # 0 = cámara integrada, 1 = cámara USB
COOLDOWN = 8            # segundos entre señales del mismo auto
# =================================================

# Inicializa clase LPR
lpr = LPR()

# Conexión serial con Arduino
try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print(f"[SERIAL] ✅ Conectado a {SERIAL_PORT}")
except Exception as e:
    print(f"[SERIAL] ⚠️ No se pudo conectar al Arduino: {e}")
    arduino = None

# Abrir cámara
cap = cv2.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    print("❌ No se pudo abrir la cámara.")
    exit()

print("🎥 Cámara encendida. Presiona 'q' para salir.")

last_activation = {}  # guarda el tiempo de la última activación por patente

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ No se pudo capturar frame.")
        break

    # Redimensionar para mejor rendimiento
    frame = cv2.resize(frame, (640, 480))

    # Dibuja recuadro central donde mostrarás la patente
    h, w, _ = frame.shape
    x1, y1, x2, y2 = w//2 - 220, h//2 - 100, w//2 + 220, h//2 + 100
    roi = frame[y1:y2, x1:x2]
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Leer texto dentro del ROI
    from LPR import read_from_camera
    text, processed = read_from_camera(roi)

    # Mostrar la imagen binarizada (lo que ve Tesseract)
    cv2.imshow("Procesado OCR", processed)

    text = text.strip().upper()

    # Mostrar texto en pantalla
    cv2.putText(frame, f"OCR: {text}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Mostrar video
    cv2.imshow("Reconocimiento de Patente (Presiona Q para salir)", frame)

    # Si se detecta texto válido
    if text and text != "NO LICENSE PLATE FOUND":
        print(f"[OCR] Detectado: {text}")
        if text in AUTHORIZED_PLATES:
            now = time.time()
            last_time = last_activation.get(text, 0)
            if now - last_time > COOLDOWN:
                last_activation[text] = now
                print(f"[✔️] {text} autorizada. Enviando señal al Arduino...")
                if arduino:
                    try:
                        arduino.write(b"OPEN\n")
                        print("[SERIAL] Comando enviado.")
                    except Exception as e:
                        print(f"[SERIAL] Error al enviar: {e}")
                else:
                    print("[SIMULACIÓN] (No hay Arduino conectado)")
        else:
            print(f"[DENEGADO] {text} no está en la lista autorizada.")

    # Salir con 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()
print("Programa finalizado.")
