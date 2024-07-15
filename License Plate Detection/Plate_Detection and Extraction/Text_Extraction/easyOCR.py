import cv2
import pandas as pd
from ultralytics import YOLO
import cvzone
import numpy as np
import easyocr
from datetime import datetime

# Initialize EasyOCR reader 
reader = easyocr.Reader(['en'], gpu=False)

model = YOLO('model/best.pt')

cap = cv2.VideoCapture('mycarplate.mp4')

my_file = open("coco1.txt", "r")
data = my_file.read()
class_list = data.split("\n") 

area = [(32, 398), (16, 456), (1015, 451), (978, 392)]

count = 0
list1 = []
processed_numbers = set()

# Open file for writing car plate data
with open("car_plate_data.txt", "a") as file:
    file.write("NumberPlate\tDate\tTime\n")  # Writing column headers

while True:    
    ret, frame = cap.read()
    count += 1
    if count % 3 != 0:
        continue
    if not ret:
       break
   
    frame = cv2.resize(frame, (1020, 500))
    results = model.predict(frame)
    a = results[0].boxes.data
    px = pd.DataFrame(a).astype("float")
   
    for index, row in px.iterrows():
        x1 = int(row[0])
        y1 = int(row[1])
        x2 = int(row[2])
        y2 = int(row[3])
        
        d = int(row[5])
        c = class_list[d]
        cx = int(x1 + x2) // 2
        cy = int(y1 + y2) // 2
        result = cv2.pointPolygonTest(np.array(area, np.int32), ((cx, cy)), False)
        if result >= 0:
           crop = frame[y1:y2, x1:x2]
           gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
           gray = cv2.bilateralFilter(gray, 10, 20, 20)

           # Use EasyOCR for text extraction
           result = reader.readtext(gray)
           if result:
               text = result[0][-2].strip()
               text = text.replace('(', '').replace(')', '').replace(',', '').replace(']','').replace('!','').replace('"','').replace('“','')
               if text not in processed_numbers:
                  processed_numbers.add(text) 
                  list1.append(text)
                  current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                  with open("car_plate_data.txt", "a") as file:
                       file.write(f"{text}\t{current_datetime}\n")
                       cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
                     

    

    # Incase if the code is stuck in infinite loop 
    if count > 1000:  # Remove or Adjust this value as needed
        break

cap.release()