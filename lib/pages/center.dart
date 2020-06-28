import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:macrohacks/widgets/custom_button.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:http/http.dart' as http;


class CenterPage extends StatefulWidget {
  @override
  _CenterPageState createState() => _CenterPageState();
}


class _CenterPageState extends State<CenterPage> {
  Future<File> file;
  File _file;
  String status = '';
  String base64Image;
  File tmpFile;
  String errMessage = 'Error Uploading Image';
  final FlutterTts flutterTts = FlutterTts();

  Future<http.StreamedResponse> uploadImage(filename, url) async {
    var request = http.MultipartRequest('POST', Uri.parse(url));
    request.files.add(await http.MultipartFile.fromPath('file', filename));
    var res = await request.send();
    return res;
  }




  Widget displaySelectedFile(File file) {
    return new ClipRRect(
      borderRadius: BorderRadius.only(
        topLeft: Radius.circular(8.0),
        topRight: Radius.circular(8.0),
      ),
      child: file == null
          ? new Image(image: AssetImage(
        'assets/images/no-image-available.png.jpeg'
      ),)
          : new Image.file(file, width: 300, height: 300, fit: BoxFit.fill,),
    );
  }



  String respStr = '';
  String returnData = '';

  @override
  void initState() {
    super.initState();
    _speak('Tap anywhere on the screen to take a picture.');
  }

  _speak(String input) async{
    await flutterTts.setLanguage('en-US');
    await flutterTts.speak(input);
  }


  @override
  Widget build(BuildContext context) {


    return Scaffold(
      body: GestureDetector(
        onTap: ()async{
          var file = await ImagePicker.pickImage(source: ImageSource.camera);
          var res = await uploadImage(file.path, "http://4aa134b5af7c.ngrok.io/textifyFile");
          respStr = await res.stream.bytesToString();
          setState(() {
            _file = file;
            returnData = respStr;
          });
          _speak(returnData);
        },
        child: SingleChildScrollView(
          child: Container(
            padding: EdgeInsets.all(16),
            child: Column(
              children: <Widget>[
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: <Widget>[
                    Container(width: MediaQuery.of(context).size.width/ 3.5 - 15,),
                    SendButton(
                      icon: Icon(Icons.camera_alt, size: 75,),
                      callback: () async{
                        var file = await ImagePicker.pickImage(source: ImageSource.camera);
                        var res = await uploadImage(file.path, "http://4aa134b5af7c.ngrok.io/foodify");
                        respStr = await res.stream.bytesToString();
                        setState(() {
                          _file = file;
                          returnData = respStr;
                        });
                        _speak(returnData);
                      },
                    ),
                    SizedBox(width: 30,),
                    SendButton(
                        icon: Icon(Icons.image, size: 75,),
                        callback: () async {
                          var file = await ImagePicker.pickImage(source: ImageSource.gallery);
//                        var res = await uploadImage(file.path, "http://292bde44c00c.ngrok.io/file_analysis");
//                        respStr = await res.stream.bytesToString();
                          setState(() {
                            _file = file;
                            returnData = respStr;
                          });
                        }
                    ),
                  ],
                ),
                SizedBox( height: 50,),
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: <Widget>[
                    Container(
                      padding: EdgeInsets.all(16),
                      decoration: BoxDecoration(
                          color: Colors.greenAccent,
                          borderRadius: BorderRadius.all(Radius.circular(25))
                      ),
                      child: Column(
                        children: <Widget>[
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: <Widget>[
                              Icon(
                                Icons.remove_red_eye, size: 40,
                              )
//                            Text('Label Reader', style: TextStyle(
//                                fontWeight:FontWeight.bold,
//                                color: Colors.black,
//                                fontSize: 25
//
//                            ),)

                            ],
                          ),
                          Divider(thickness: 5,),
                          SizedBox(height: 10,),
                          displaySelectedFile(_file),
                          SizedBox(height: 10,),
                          Container(
                            padding: EdgeInsets.all(16),
                            decoration: BoxDecoration(
                                color: Colors.greenAccent,
                                borderRadius: BorderRadius.all(Radius.circular(25))
                            ),
                            child: respStr == '' ? Text('Select an Image.', style: TextStyle(
                                fontSize: 22
                            ),) : Text(returnData, style: TextStyle(
                                fontSize: 22
                            ),),
                          ),
                          SizedBox(
                            height: 10,
                          ),
                        ],

                      ),
                    )

                  ],

                ),
              ],
            ),

          ),
        ),
      )
    );
  }
}
