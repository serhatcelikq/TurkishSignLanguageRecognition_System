import 'dart:ui';
import 'package:flutter_vision/flutter_vision.dart';
import 'package:camera/camera.dart';

class SignLanguageModel {
  late FlutterVision _vision;
  bool _isLoaded = false;
  
  // 🧠 SABİTLEME AYARLARI (SMOOTHING)
  // Son 5 kareyi hafızada tutacağız
  final List<String> _history = [];
  final int _historyLimit = 5; 
  
  // Ekranda görünecek son nihai karar
  String _finalDecision = "...";

  bool get isLoaded => _isLoaded;
  String get currentResult => _finalDecision;

  // 1. MODELİ YÜKLEME
  Future<void> loadModel() async {
    _vision = FlutterVision();
    await _vision.loadYoloModel(
      labels: 'assets/models/labels.txt',
      modelPath: 'assets/models/best_float16.tflite',
      modelVersion: "yolov8",
      quantization: false,
      numThreads: 2,
      useGpu: true, // Poco X6 Pro için GPU hızlandırma
    );
    _isLoaded = true;
    print("✅ YOLO Model Yüklendi! (Kıyaslamalı + Sabitlemeli Mod)");
  }

  // 2. KAREYİ İŞLEME VE MANTIK
  Future<List<Map<String, dynamic>>> processCameraImage(CameraImage image) async {
    if (!_isLoaded) return [];

    // A) TAHMİN AL (INFERENCE)
    final result = await _vision.yoloOnFrame(
      bytesList: image.planes.map((plane) => plane.bytes).toList(),
      imageHeight: image.height,
      imageWidth: image.width,
      iouThreshold: 0.4,
      confThreshold: 0.20, // Ham veriyi alıp kendimiz eleyeceğiz
      classThreshold: 0.20,
    );

    List<Map<String, dynamic>> validDetections = [];
    String bestTagInFrame = "bos";
    double highestConf = 0.0;

    // B) KIYASLAMA MANTIĞI (BAKLAVA vs PARMAK)
    // Önce bu karedeki en yüksek skorları bulalım
    double maxBaklavaScore = 0.0;
    double maxParmakScore = 0.0;

    for (var res in result) {
      if (res['tag'] == 'baklava') {
        if (res['box'][4] > maxBaklavaScore) maxBaklavaScore = res['box'][4];
      }
      if (res['tag'] == 'parmak') {
        if (res['box'][4] > maxParmakScore) maxParmakScore = res['box'][4];
      }
    }

    // Şimdi kazananı belirleyelim
    bool baklavaKazandi = false;
    bool parmakKazandi = false;

    // Eğer ikisi de tespit edildiyse, puanı yüksek olan diğerini yener!
    if (maxBaklavaScore > 0 && maxParmakScore > 0) {
      if (maxBaklavaScore > maxParmakScore) {
        baklavaKazandi = true; // Parmak kaybeder, listeye giremez
      } else {
        parmakKazandi = true; // Baklava kaybeder, listeye giremez
      }
    }

    // C) FİLTRELEME VE SEÇME
    for (var res in result) {
      String tag = res['tag'];
      double conf = res['box'][4]; 

      // --- ÇAKIŞMA ELEMELERİ ---
      // Eğer Parmak kazandıysa, Baklavaları görmezden gel
      if (parmakKazandi && tag == 'baklava') continue;

      // Eğer Baklava kazandıysa, Parmakları görmezden gel
      if (baklavaKazandi && tag == 'parmak') continue;

      // --- AKILLI EŞİK KONTROLÜ ---
      if (_checkSmartFilter(tag, conf)) {
        validDetections.add(res);
        
        // Bu karedeki en yüksek skorluyu "o anki tahmin" olarak seç
        if (conf > highestConf) {
          highestConf = conf;
          bestTagInFrame = tag;
        }
      }
    }

    // D) KARAR SABİTLEME (SONUÇ GÜNCELLEME)
    _updateHistory(bestTagInFrame);

    return validDetections;
  }

  // 3. TARİHÇE VE KARAR VERME
  void _updateHistory(String detection) {
    // Listeye ekle
    _history.add(detection);

    // Boyutu koru (max 5)
    if (_history.length > _historyLimit) {
      _history.removeAt(0);
    }

    // Yeterli veri biriktiyse analiz yap
    if (_history.length >= _historyLimit) {
      // En çok tekrar edeni bul
      var counts = <String, int>{};
      for (var item in _history) {
        counts[item] = (counts[item] ?? 0) + 1;
      }

      var mostCommon = counts.entries.reduce((a, b) => a.value > b.value ? a : b);

      // KURAL: 5 karenin en az 4'ü aynıysa sonucu değiştir.
      if (mostCommon.value >= 4) {
        if (mostCommon.key != "bos") {
          _finalDecision = mostCommon.key;
        } else {
          // Eğer 5 karenin 4'ünde bir şey yoksa yazıyı sil
          _finalDecision = "...";
        }
      }
    }
  }

  // 4. EŞİK DEĞERLERİ (THRESHOLD)
  bool _checkSmartFilter(String className, double confidence) {
    // KURAL 1: Baklava (Daha zor tespit edildiği için hata payı yüksek, eşik yüksek)
    if (className == "baklava") {
      return confidence > 0.65; // %65'ten azsa Baklava deme
    }
    
    // KURAL 2: Parmak (Yarış mantığı olduğu için normal seviyede)
    else if (className == "parmak") {
      return confidence > 0.50; 
    }

    // KURAL 3: Zor Sınıflar (Kolay algılansın diye düşük eşik)
    else if (["jilet", "sabır", "sabir", "oy", "fıstık"].contains(className)) {
      return confidence > 0.25;
    }
    
    // KURAL 4: Standart Diğerleri
    else {
      return confidence > 0.45;
    }
  }

  // Kaynakları temizle
  Future<void> dispose() async {
    await _vision.closeYoloModel();
  }
}