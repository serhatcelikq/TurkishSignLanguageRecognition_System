import os
import json

# config.json yolunu ve label klasörünü ayarla
config_path = "src/config.json"
labels_dir = "data/test/labels"

# Sınıf isimlerini ve toplam sınıf sayısını al
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)
classes = config["classes"]
num_classes = len(classes)

# Yanlış etiketli dosyaları bulmak için
wrong_labels = []
for label_file in os.listdir(labels_dir):
    if not label_file.endswith(".txt"):
        continue
    with open(os.path.join(labels_dir, label_file), "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            try:
                class_id = int(parts[0])
            except ValueError:
                wrong_labels.append((label_file, parts[0]))
                continue
            if class_id < 0 or class_id >= num_classes:
                wrong_labels.append((label_file, class_id))

if wrong_labels:
    print("Yanlış etiketli dosyalar:")
    for fname, cid in wrong_labels:
        print(f"{fname}: Hatalı class ID {cid}")
else:
    print("Tüm etiketler doğru aralıkta!")
