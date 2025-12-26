# ================================================================
# YOLOv8 SIGN LANGUAGE TRAINING - ZIPPED DATA VERSION
# ================================================================

import os
import shutil
from ultralytics import YOLO
import yaml
import torch
import warnings

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------
# 1. ZIP DOSYASINI AÇMA (Eğer yüklendiyse)
# ----------------------------------------------------------------
if os.path.exists("data.zip"):
    print("📦 data.zip bulundu, dışarı çıkartılıyor...")
    # Zip'i aç (-q sessiz mod, -o üzerine yaz)
    os.system("unzip -q -o data.zip")
    print("✅ Zip açıldı! Klasör yapısı kontrol ediliyor...")
else:
    print("⚠️ UYARI: 'data.zip' dosyası bulunamadı!")
    print("Lütfen bilgisayarınızdaki 'data' klasörünü zip yapıp Colab'e yükleyin.")

# ----------------------------------------------------------------
# 2. CLASS İSİMLERİ (Senin 28 Sınıfın)
# ----------------------------------------------------------------
CLASSES = [
    "ada", "aferin", "baklava", "bana", "evlenmek", "ezan", "fizik", "fıstık", 
    "geyik", "inek", "japonya", "jilet", "lazım", "nabız", "namaz", "omuz", "oy", 
    "parmak", "radyo", "sabır", "saç", "taksi", "veda", "öpmek", "üye", "üçgen", 
    "ırmak", "şık"
]

# ----------------------------------------------------------------
# 3. KONFIGÜRASYON (Senin Resim Yapına Göre)
# ----------------------------------------------------------------
class Config:
    # Google Colab'de zip açılınca "data" klasörü oluşur
    # Senin görselindeki yapı: data -> train -> images
    
    BASE_DIR = os.path.abspath("data") # Tam yolunu al
    
    TRAIN_IMAGES = os.path.join(BASE_DIR, "train", "images")
    TEST_IMAGES = os.path.join(BASE_DIR, "test", "images")
    
    # Model Ayarları (Optimize Edilmiş)
    MODEL_SIZE = "yolov8s.pt"  # Small model (Dengeli)
    IMG_SIZE = 640             # Senin 660px resimlerine en uygun boyut
    BATCH_SIZE = 16
    EPOCHS = 100
    PATIENCE = 30
    
    # Augmentation (70 resim için güçlendirilmiş ayarlar)
    MOSAIC = 1.0
    MIXUP = 0.1
    DEGREES = 15.0  # El dönmesi
    FLIPLR = 0.5    # Aynalama
    
    PROJECT_NAME = "sign_language_final"
    OUTPUT_DIR = "runs/train"

# ----------------------------------------------------------------
# 4. DATA.YAML OLUŞTURMA
# ----------------------------------------------------------------
def create_yaml():
    # Klasörlerin gerçekten var olup olmadığını kontrol et
    if not os.path.exists(Config.TRAIN_IMAGES):
        print(f"❌ HATA: Klasör bulunamadı: {Config.TRAIN_IMAGES}")
        print("Lütfen data.zip dosyasının içinde 'data' klasörü olduğundan emin olun.")
        return None

    yaml_data = {
        'path': Config.BASE_DIR,
        'train': 'train/images', # data.yaml konumu baz alınarak relative path
        'val': 'test/images',
        'test': 'test/images',
        'nc': len(CLASSES),
        'names': CLASSES
    }
    
    with open(f"{Config.BASE_DIR}/data.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ data.yaml oluşturuldu: {Config.BASE_DIR}/data.yaml")
    return f"{Config.BASE_DIR}/data.yaml"

# ----------------------------------------------------------------
# 5. EĞİTİMİ BAŞLAT
# ----------------------------------------------------------------
def start_training():
    yaml_path = create_yaml()
    
    if yaml_path:
        print("\n🚀 EĞİTİM BAŞLIYOR...")
        print(f"Model: {Config.MODEL_SIZE} | Resim: {Config.IMG_SIZE}")
        
        model = YOLO(Config.MODEL_SIZE)
        
        model.train(
            data=yaml_path,
            imgsz=Config.IMG_SIZE,
            epochs=Config.EPOCHS,
            batch=Config.BATCH_SIZE,
            patience=Config.PATIENCE,
            optimizer="AdamW",
            lr0=0.001,
            lrf=0.01,
            
            # Veri Çoğaltma
            mosaic=Config.MOSAIC,
            mixup=Config.MIXUP,
            degrees=Config.DEGREES,
            fliplr=Config.FLIPLR,
            
            project=Config.OUTPUT_DIR,
            name=Config.PROJECT_NAME,
            verbose=True
        )
        print("🎉 Eğitim Tamamlandı!")
        
        # Drive'a kaydetme (İsteğe bağlı)
        try:
            from google.colab import drive
            drive.mount('/content/drive')
            dest = "/content/drive/MyDrive/SignLanguage_Model_Final"
            if os.path.exists(dest): shutil.rmtree(dest)
            shutil.copytree(f"{Config.OUTPUT_DIR}/{Config.PROJECT_NAME}", dest)
            print(f"💾 Model Drive'a yedeklendi: {dest}")
        except:
            print("ℹ️ Drive'a kaydedilmedi (Mount edilmedi veya hata).")

if __name__ == "__main__":
    start_training()