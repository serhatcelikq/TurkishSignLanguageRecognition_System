from ultralytics import YOLO
import torch
from pathlib import Path
import matplotlib.pyplot as plt
import cv2
import numpy as np

# Model ve classlar
MODEL_PATH = "checkpoints/best.pt"  # YOLOv8 ile eğittiğin modelin yolu
IMG_SIZE = 640  # Eğitimde kullandığın çözünürlük
CONF_THRESHOLD = 0.5  # Eşik değeri

# Test klasörü
TEST_IMAGES_DIR = "data/test/images"

# Modeli yükle
model = YOLO(MODEL_PATH)
class_names = model.names


# Dinamik olarak kaç resim varsa ona göre subplot oluştur
import math
image_paths = list(Path(TEST_IMAGES_DIR).glob("*.jpg"))
num_images = len(image_paths)
if num_images == 0:
    print("Test klasöründe hiç .jpg resim bulunamadı!")
    exit()

import random
random.seed(42)
# Rastgele 20 resim seç
max_images = min(400, num_images)
image_paths = random.sample(image_paths, max_images)

# Her resim 340x340 px olacak şekilde (1 inç = 96 px)
fig_width = (340 * max_images) / 96  # inç cinsinden genişlik
fig_height = 340 / 96  # inç cinsinden yükseklik
fig, axs = plt.subplots(1, max_images, figsize=(fig_width, fig_height))
if max_images == 1:
    axs = [axs]

for idx, img_path in enumerate(image_paths[:max_images]):
    img = cv2.imread(str(img_path))
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = model(img_rgb, imgsz=IMG_SIZE, conf=CONF_THRESHOLD)
    boxes = results[0].boxes
    annotated_img = img_rgb.copy()

    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf = float(box.conf[0])
        cls = int(box.cls[0])
        label = f"{class_names[cls]}: {conf:.2f}"
        color = (0, 255, 0)
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(annotated_img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    
    plt.figure(figsize=(6, 6))
    plt.imshow(annotated_img)
    plt.title(img_path.name, fontsize=10)
    plt.axis("off")
    plt.tight_layout()
    plt.show()

# Kullanılmayan subplot'ları gizle
for j in range(max_images, len(axs)):
    axs[j].axis("off")

plt.tight_layout()
plt.show()