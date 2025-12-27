import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
// Eğer dosya adın veya klasörün farklıysa burayı kendine göre düzelt:
import '../models/wlasl_model.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  late CameraController controller;
  late SignLanguageModel _modelLogic;
  
  bool isCameraInitialized = false;
  bool isDetecting = false;
  
  List<Map<String, dynamic>> yoloResults = [];
  
  // Kameradan gelen ham görüntünün boyutları
  double cameraImageHeight = 0;
  double cameraImageWidth = 0;

  @override
  void initState() {
    super.initState();
    _initializeSystem();
  }

  Future<void> _initializeSystem() async {
    // 1. Modeli Başlat
    _modelLogic = SignLanguageModel();
    await _modelLogic.loadModel();

    // 2. Kamerayı Başlat
    final cameras = await availableCameras();
    if (cameras.isEmpty) return;

    controller = CameraController(
      cameras[0], 
      ResolutionPreset.medium, // Performans için medium idealdir
      enableAudio: false,
    );
    
    await controller.initialize();
    
    // NOT: Android'de dikey modda (Portrait) genişlik ve yükseklik genelde ters gelir.
    // previewSize.height -> Telefonun Genişliği olur
    // previewSize.width  -> Telefonun Yüksekliği olur
    cameraImageWidth = controller.value.previewSize!.height;
    cameraImageHeight = controller.value.previewSize!.width;

    // 3. Görüntü Akışını Başlat
    controller.startImageStream((image) async {
      if (!isDetecting && _modelLogic.isLoaded) {
        isDetecting = true;
        
        final results = await _modelLogic.processCameraImage(image);
        
        if (mounted) {
          setState(() {
            yoloResults = results;
          });
        }
        
        isDetecting = false;
      }
    });

    setState(() {
      isCameraInitialized = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (!isCameraInitialized) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: CircularProgressIndicator()),
      );
    }

    final Size screenSize = MediaQuery.of(context).size;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand, // Tüm ekranı kapla
        children: [
          // 1. KAMERA GÖRÜNTÜSÜ
          // Kamerayı ekrana sığdırmak için SizedBox ve AspectRatio yerine
          // Transform ve Scale kullanmak, tam ekran (full screen) etkisi için daha iyidir.
          SizedBox(
            width: screenSize.width,
            height: screenSize.height,
            child: CameraPreview(controller),
          ),
          
          // 2. KUTULAR (Düzeltilmiş Matematik ile)
          ..._displayBoxes(screenSize),

          // 3. ÜST BİLGİ PANELİ (HUD)
          Positioned(
            top: 50,
            left: 20,
            right: 20,
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.6),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.yellow.withOpacity(0.5)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("ALGILANAN:", 
                        style: TextStyle(color: Colors.white70, fontSize: 12)),
                      Text(
                        _modelLogic.currentResult.toUpperCase(),
                        style: const TextStyle(
                          color: Colors.yellow, 
                          fontSize: 32, 
                          fontWeight: FontWeight.w900,
                          letterSpacing: 1.5
                        ),
                      ),
                    ],
                  ),
                  const Icon(Icons.back_hand, color: Colors.yellow, size: 40),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // 🛠️ KUTU ÇİZİM FONKSİYONU (DÜZELTİLMİŞ)
  List<Widget> _displayBoxes(Size screen) {
    if (yoloResults.isEmpty) return [];

    // Görüntü Oranları
    double screenRatio = screen.height / screen.width;
    double imageRatio = cameraImageHeight / cameraImageWidth;

    double scale;
    double dx = 0;
    double dy = 0;

    // CameraPreview, ekranı doldurmak için (BoxFit.cover gibi) çalışır.
    // Hangi kenarın kırpıldığını bulup ona göre scale ve offset (kaydırma) hesaplıyoruz.
    if (screenRatio > imageRatio) {
      // Ekran daha uzun (Dikey), yanlardan kırpma var
      scale = screen.height / cameraImageHeight;
      dx = (screen.width - (cameraImageWidth * scale)) / 2;
    } else {
      // Ekran daha geniş, üstten/alttan kırpma var
      scale = screen.width / cameraImageWidth;
      dy = (screen.height - (cameraImageHeight * scale)) / 2;
    }

    return yoloResults.map((result) {
      // YOLO Koordinatları (x1, y1, x2, y2)
      // List<dynamic> olduğu için double'a çeviriyoruz
      double x1 = result["box"][0].toDouble();
      double y1 = result["box"][1].toDouble();
      double x2 = result["box"][2].toDouble();
      double y2 = result["box"][3].toDouble();

      // Koordinat Dönüşümü: (Orijinal * Büyütme) + Kaydırma
      // dx ve dy negatif olabileceği için "+" ile topluyoruz (formül gereği)
      double left = (x1 * scale) + dx;
      double top = (y1 * scale) + dy;
      double right = (x2 * scale) + dx;
      double bottom = (y2 * scale) + dy;

      // Genişlik ve Yükseklik
      double width = right - left;
      double height = bottom - top;

      // Etiket ve Güven Skoru
      String tag = result['tag'];
      double conf = result['box'][4] * 100;

      // Renk Seçimi
      Color color = conf > 80 ? Colors.green : Colors.orange;

      return Positioned(
        left: left,
        top: top,
        width: width,
        height: height,
        child: Container(
          decoration: BoxDecoration(
            border: Border.all(color: color, width: 3),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Align(
            alignment: Alignment.topLeft,
            child: Container(
              color: color,
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
              child: Text(
                "$tag %${conf.toStringAsFixed(0)}",
                style: const TextStyle(
                  color: Colors.black, 
                  fontSize: 12, 
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
        ),
      );
    }).toList();
  }

  @override
  void dispose() {
    controller.dispose();
    _modelLogic.dispose();
    super.dispose();
  }
}