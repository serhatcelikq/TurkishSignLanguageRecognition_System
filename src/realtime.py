import cv2
import time
import os
import numpy as np
from ultralytics import YOLO
from collections import deque, Counter

# ================================================================
# ⚙️ AYARLAR VE KONFİGÜRASYON
# ================================================================
# Model Dosyası Yolu
MODEL_PATH = "checkpoints/best.pt" 

# Kamera Seçimi (0: Laptop kamerası, 1: USB Kamera)
CAMERA_ID = 1 

# Hafıza Uzunluğu (Son kaç kareye bakılarak karar verilsin?)
# 10 idealdir. Çok artırırsan (örn: 30) sonuçlar geç gelir.
HISTORY_LENGTH = 10 

# ================================================================
# 🧠 AKILLI FİLTRELEME KURALLARI
# ================================================================
def check_smart_filter(class_name, confidence):
    """
    Sınıfa özel eşik değerleri (Threshold) burada belirlenir.
    True dönerse ekrana çizilir, False dönerse gizlenir.
    """
    
    # KURAL 1: Baklava (Parmak ile karışmasını engellemek için SIKI kural)
    if class_name == "baklava":
        return confidence > 0.60  # %60'tan azsa Baklava deme!
    
    # KURAL 2: Zor Sınıflar (Jilet, Sabır - Görülmesi zor olduğu için GEVŞEK kural)
    elif class_name in ["jilet", "sabır", "sabir", "oy", "fıstık"]:
        return confidence > 0.25  # %25 bile olsa göster
    
    # KURAL 3: Diğer Tüm Sınıflar (Standart Ayar)
    else:
        return confidence > 0.45  # %45 altını gösterme

# ================================================================
# 🚀 ANA PROGRAM
# ================================================================
def main():
    print("="*60)
    print("🚀 GELİŞMİŞ REAL-TIME İŞARET DİLİ TESPİTİ")
    print("✨ Özellikler: Akıllı Filtreleme + Titreme Önleme")
    print("="*60)

    # 1. Model Kontrolü
    if not os.path.exists(MODEL_PATH):
        print(f"❌ HATA: Model bulunamadı: {MODEL_PATH}")
        return

    # 2. Modeli Yükle
    print("📦 Model yükleniyor...")
    try:
        model = YOLO(MODEL_PATH)
    except Exception as e:
        print(f"❌ HATA: {e}")
        return

    # 3. Kamerayı Aç
    cap = cv2.VideoCapture(CAMERA_ID)
    if not cap.isOpened():
        print(f"❌ HATA: {CAMERA_ID} nolu kamera açılamadı!")
        return

    # Kamera Ayarları (Hız için 640x480)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("✅ Sistem çalışıyor. Çıkmak için 'q' tuşuna basın.")
    
    # Değişkenler
    prev_frame_time = 0
    history = deque(maxlen=HISTORY_LENGTH) # Sonuç hafızası
    final_decision = "..." # Ekrana yazılacak son karar
    
    while True:
        success, frame = cap.read()
        if not success: break

        # ---------------------------------------------------------
        # 1. TAHMİN (INFERENCE)
        # ---------------------------------------------------------
        # conf=0.20 yapıyoruz ki model fısıldasa bile duyalım.
        # Elemeyi aşağıda biz yapacağız.
        results = model(frame, imgsz=640, conf=0.20, verbose=False)
        
        # Temiz bir kopya al (Çizimleri bunun üzerine yapacağız)
        annotated_frame = frame.copy()
        
        # Bu karede geçerli not alan tespitleri buraya atacağız
        current_frame_valid_detections = []

        # ---------------------------------------------------------
        # 2. FİLTRELEME VE ÇİZİM
        # ---------------------------------------------------------
        if results[0].boxes:
            for box in results[0].boxes:
                # Verileri al
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                name = model.names[cls_id]
                x1, y1, x2, y2 = map(int, box.xyxy[0]) # Koordinatlar

                # ---> AKILLI FİLTRE KONTROLÜ <---
                if check_smart_filter(name, conf):
                    
                    # Eğer filtreden geçtiyse listeye ekle
                    current_frame_valid_detections.append((name, conf))
                    
                    # Ekrana Kutu Çiz (Yeşil)
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Kutunun üzerine isim yaz
                    label = f"{name} %{int(conf*100)}"
                    cv2.putText(annotated_frame, label, (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # ---------------------------------------------------------
        # 3. KARAR SABİTLEME (SMOOTHING)
        # ---------------------------------------------------------
        # Bu karede en yüksek güvene sahip olanı hafızaya at
        if current_frame_valid_detections:
            # En yüksek güven oranına sahip olanı bul (conf değerine göre sırala)
            best_det = max(current_frame_valid_detections, key=lambda x: x[1])
            history.append(best_det[0]) # Sadece ismini hafızaya at
        else:
            history.append("bos") # Tespit yoksa 'bos' at

        # Hafızanın analizi (Son 10 karenin çoğunluğu ne diyor?)
        if len(history) > 0:
            count = Counter(history)
            most_common, frequency = count.most_common(1)[0]
            
            # Eğer son 10 karenin en az 6 tanesi aynıysa KARAR ver.
            if frequency >= 6 and most_common != "bos":
                final_decision = most_common
            elif most_common == "bos" and frequency >= 6:
                final_decision = "..."
        
        # ---------------------------------------------------------
        # 4. ARAYÜZ (HUD)
        # ---------------------------------------------------------
        # FPS Hesapla
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time) if prev_frame_time > 0 else 0
        prev_frame_time = new_frame_time

        # Üst Siyah Panel
        cv2.rectangle(annotated_frame, (0, 0), (640, 85), (0, 0, 0), -1)
        
        # Sonuç Yazısı (Sarı ve Büyük)
        cv2.putText(annotated_frame, f"SONUC: {final_decision}", (20, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 255), 3)
        
        # FPS Yazısı (Sağ üst, Gri)
        cv2.putText(annotated_frame, f"FPS: {int(fps)}", (520, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

        # Görüntüyü Göster
        cv2.imshow("Isaret Dili Tespiti (Gelistirilmis)", annotated_frame)

        # 'q' ile çıkış
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("👋 Program sonlandırıldı.")

if __name__ == "__main__":
    main()