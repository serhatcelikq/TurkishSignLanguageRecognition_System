import 'package:flutter/material.dart';
import 'pages/home_page.dart';

void main() {
  runApp(const WLASLTestApp());
}

class WLASLTestApp extends StatelessWidget {
  const WLASLTestApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'WLASL Model Test',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
        fontFamily: 'Roboto',
      ),
      home: const HomePage(),
    );
  }
}
