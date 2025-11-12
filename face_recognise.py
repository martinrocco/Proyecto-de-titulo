# import the required libraries
import cv2
import pickle
import serial
import time

# Ajusta el puerto COM según tu sistema (ej: 'COM3' en Windows o '/dev/ttyUSB0' en Linux)
arduino = serial.Serial('COM6', 9600)
time.sleep(2)  # Espera a que Arduino se reinicie

video = cv2.VideoCapture(0)
cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

# Loaading the face recogniser and the trained data into the program
recognise = cv2.face.LBPHFaceRecognizer_create()
recognise.read("trainner.yml")

labels = {} # dictionary
# Opening labels.pickle file and creating a dictionary containing the label ID
# and the name
with open("labels.pickle", 'rb') as f:##
    og_label = pickle.load(f)##
    labels = {v:k for k,v in og_label.items()}##
    print(labels)


while True:
    check,frame = video.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    face = cascade.detectMultiScale(gray, scaleFactor = 1.2, minNeighbors = 5)
    #print(face)

    for x,y,w,h in face:
        face_save = gray[y:y+h, x:x+w]
        
        # Predicting the face identified
        ID, conf = recognise.predict(face_save)
        #print(ID,conf)
        if conf >= 20 and conf <= 115:
            print(ID)
            print(labels[ID])
            cv2.putText(frame,labels[ID],(x-10,y-10),cv2.FONT_HERSHEY_COMPLEX ,1, (18,5,255), 2, cv2.LINE_AA )
        frame = cv2.rectangle(frame, (x,y), (x+w,y+h),(0,255,255),4)
        if ID == 0:  # Reemplaza TU_ID con el número que te asignó el entrenamiento
            print("¡Martín reconocido!")
            arduino.write(b'1')  # Enviar señal para abrir
            time.sleep(2)
            arduino.write(b'0')  # Cerrar después de 2 segundos


    cv2.imshow("Video",frame)
    key = cv2.waitKey(1)
    if(key == ord('q')):
        break

video.release()
cv2.destroyAllWindows()
