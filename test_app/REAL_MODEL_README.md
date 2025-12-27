# 🤖 WLASL İşaret Dili Tanıma Uygulaması

Bu uygulama WLASL (Word-Level American Sign Language) modelini kullanarak gerçek zamanlı işaret dili tanıma yapar.

## 🎯 Özellikler

### ✅ Tamamlanan Özellikler:

- **Gerçek TensorFlow Lite Entegrasyonu** - `wlasl_mobile_optimized.tflite` modeli
- **Kamera Test Sayfası** - Gerçek zamanlı görüntü yakalama
- **Mock Fallback Sistemi** - Model yüklenemezse mock tahminler
- **Material Design 3 UI** - Modern ve kullanıcı dostu arayüz
- **Cross-platform Destekgi** - iOS ✅, Android ⚠️ (Gradle sorunu)

### 📱 Sayfa Yapısı:

1. **Ana Sayfa** (`HomePage`)

   - Model durumu göstergesi
   - Dummy data test butonu
   - Kamera test sayfası linki
   - Sonuç gösterimi

2. **Kamera Test Sayfası** (`CameraTestPage`)
   - Gerçek zamanlı kamera preview
   - Start/Stop detection kontrolleri
   - 2 saniyede bir tahmin
   - Visual feedback ve sonuçlar

## 🧠 Model Detayları

### **WLASL Model Spesifikasyonları:**

- **Input Shape**: `[1, 50, 1629]` float32
- **Output Shape**: `[1, 9]` float32
- **Sınıflar**: drink, eat, hello, help, me, no, please, yes, you
- **Model Dosyası**: `assets/models/wlasl_mobile_optimized.tflite` (1.28 MB)

### **Label Mapping:**

```
0 → drink
1 → eat
2 → hello
3 → help
4 → me
5 → no
6 → please
7 → yes
8 → you
```

## 🚀 Çalıştırma

### **iOS (Çalışıyor ✅):**

```bash
flutter run -d "iPhone 16 Pro"
```

### **Android (Gradle Sorunu ⚠️):**

```bash
flutter run -d emulator-5554
# Java version conflict nedeniyle build hatası
```

## 🔧 Teknik Detaylar

### **Dependencies:**

- `tflite_flutter: ^0.9.1` - TensorFlow Lite runtime
- `camera: ^0.10.5+5` - Kamera erişimi
- `permission_handler: ^11.0.1` - İzin yönetimi
- `image: ^4.1.3` - Görüntü işleme

### **Permissions:**

#### iOS (`ios/Runner/Info.plist`):

```xml
<key>NSCameraUsageDescription</key>
<string>This app needs camera access to detect sign language gestures in real-time.</string>
```

#### Android (`android/app/src/main/AndroidManifest.xml`):

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-feature android:name="android.hardware.camera" android:required="true" />
```

## 🧪 Test Senaryoları

### **1. Model Loading Test:**

- Gerçek TensorFlow Lite model yükleme
- Fallback mock sistemi
- Label dosyası okuma

### **2. Dummy Data Test:**

- `[1, 50, 1629]` rastgele data generation
- Model inference testi
- Sonuç formatlaması

### **3. Kamera Test:**

- Kamera permission ve initialization
- Gerçek zamanlı preview
- 2 saniyede bir prediction
- UI feedback

## 🎨 UI/UX Tasarımı

### **Ana Sayfa UI:**

```
┌─────────────────────────────────┐
│ 🎯 WLASL Model Test            │
├─────────────────────────────────┤
│ ✅ Model Status: Model Ready    │
│                                 │
│ [Test Model with Dummy Data]    │
│ [Test with Camera (Real-time)]  │
│                                 │
│ 🧠 Prediction Results:         │
│ ┌─────────────────────────────┐ │
│ │        HELLO               │ │
│ │        23.5%               │ │
│ └─────────────────────────────┘ │
│                                 │
│ All Class Probabilities:        │
│ hello  ████████████████ 23.5%  │
│ drink  ████████████     18.2%  │
│ ...                             │
└─────────────────────────────────┘
```

### **Kamera Sayfası UI:**

```
┌─────────────────────────────────┐
│ 📹 Sign Language Detection     │
├─────────────────────────────────┤
│                                 │
│         CAMERA PREVIEW          │
│       [Recording Overlay]       │
│                                 │
├─────────────────────────────────┤
│ Status: Detecting...            │
│ [Start Detection] [Stop]        │
│                                 │
│ Last Detection: HELLO (23.5%)   │
└─────────────────────────────────┘
```

## 📊 Log Output Örneği

```
🔄 Loading WLASL TensorFlow Lite model...
🏷️ Loaded 9 labels: [drink, eat, hello, help, me, no, please, yes, you]
✅ WLASL model loaded successfully
📊 Input shape: [1, 50, 1629]
📊 Output shape: [1, 9]
🎯 Model ready for inference!

🧪 Starting model test with dummy data...
🎲 Generated dummy input: [1, 50, 1629]
🔮 Running TensorFlow Lite inference...
🔮 TensorFlow Lite prediction completed in 45ms
📊 Probabilities: [12.3, 8.1, 24.7, 15.2, 9.8, 7.4, 11.2, 6.8, 4.5]
🎯 Predicted: hello (24.7%)
```

## 🔮 Sonraki Adımlar

### **Gerçek Model Entegrasyonu İçin:**

1. **Pose Detection** - MediaPipe/OpenPose entegrasyonu
2. **Feature Extraction** - Hand landmarks → [1629] feature vector
3. **Sequence Processing** - 50 frame sequence management
4. **Real-time Pipeline** - Kamera → Pose → Features → Model → UI

### **Android Gradle Sorunu İçin:**

1. Java version uyumluluğu düzeltmesi
2. TensorFlow Lite Android build fix
3. Namespace configuration update

### **UI/UX İyileştirmeleri:**

1. Gesture rehberi ekleme
2. Confidence threshold ayarları
3. Video recording özelliği
4. Model performance metrics

## 💡 Notlar

- **iOS'da tam fonksiyonel** çalışıyor ✅
- **Model dosyası mevcut** (`wlasl_mobile_optimized.tflite`)
- **Mock fallback sistemi** her durumda çalışır
- **Production-ready UI** tasarımı
- **Gerçek kamera entegrasyonu** hazır

**Şu anki durum:** Model yükleme ve UI tamamen hazır, sadece gerçek pose detection pipeline'ı eklenecek! 🚀
