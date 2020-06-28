from flask import Flask, request, redirect, session, url_for, Response, json, render_template, send_from_directory
from werkzeug.utils import secure_filename
from flask.json import jsonify
import json
import os
import random
import time
import requests
from pymongo import MongoClient
from pprint import pprint
from google.cloud import datastore
from google.cloud import vision
from google.cloud import storage
from flask_cors import CORS
from google.cloud import automl_v1beta1
from google.cloud.automl_v1beta1.proto import service_pb2
from clarifai.rest import ClarifaiApp
import gcpocrlib
import gcpvisionlib

from bson import ObjectId

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)



with open('credentials.json', 'r') as f:
    creds = json.load(f)

mongostr = creds["mongostr"]
client = MongoClient(mongostr)
clarifaikey = creds["clarifai"]["api_key"]

capp = ClarifaiApp(api_key=clarifaikey)
model = capp.public_models.food_model
# response = model.predict_by_url('@@sampleTrain')



db = client["everestfridge"]




ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config.from_object(__name__)
CORS(app)



datastore_client = datastore.Client.from_service_account_json('gc.json')

def downloadpic(pic_url):
    

    with open('pic1.jpg', 'wb') as handle:
            response = requests.get(pic_url, stream=True)

            if not response.ok:
                print (response)

            for block in response.iter_content(1024):
                if not block:
                    break

                handle.write(block)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_top_labels(uri):
    """Detects labels in the file located in Google Cloud Storage or on the
    Web."""
    # imageurl = "https://storage.googleapis.com/hacklarious/testimage.jpg"
    
    client = vision.ImageAnnotatorClient.from_service_account_json('gc.json')
    image = vision.types.Image()
    image.source.image_uri = uri

    
    response = client.label_detection(image=image)

    print ('hereeeeeeeeeeeeeeeeeeeeeee')

    labels = response.label_annotations
    # print('Labels:')

    i = 0

    keywords = []
    for label in labels:
        print(label.description)
        keywords.append(label.description)
        # i = i + 1
        # if i == 3:
        #     break
 
 
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    if len(keywords) == 0:
        keywords.append("random")
    return keywords


def uploadtogcp(filename):
    # Explicitly use service account credentials by specifying the private key
    # file.
    storage_client = storage.Client.from_service_account_json('gc.json')

    # Make an authenticated API request
    ##buckets = list(storage_client.list_buckets())
    ##print(buckets)

    bucketname = "hackybucket"
    # filename = sys.argv[2]


    bucket = storage_client.get_bucket(bucketname)

    destination_blob_name = "current.jpg"
    source_file_name = filename

    blob = bucket.blob(destination_blob_name)
    blob.cache_control = "no-cache"

    blob.upload_from_filename(source_file_name)
    blob.make_public()
    blob.cache_control = "no-cache"

    print('File {} uploaded to {}.'.format(source_file_name, destination_blob_name))


@app.route("/file_upload", methods=["POST"])
def fileupload():

    if 'file' not in request.files:
          return "No file part"
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
      return "No selected file"
    if file and allowed_file(file.filename):
        UPLOAD_FOLDER = "./uploads"
  
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        uploadtogcp(os.path.join(UPLOAD_FOLDER, filename))
        return 'file uploaded successfully'
    
    return 'file not uploaded successfully'



@app.route("/textifyFile", methods=["POST"])
def textifyFile():

    if 'file' not in request.files:
          return "No file part"
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
      return "No selected file"
    if file and allowed_file(file.filename):
        UPLOAD_FOLDER = "./uploads"
  
        filename = secure_filename(file.filename)
        print("filename is " +filename)
        fileuploadname = "./uploads/"+filename
        fileuploadname = filename
        file.save(fileuploadname)
        uploadtogcp(fileuploadname)
        # file.save(os.path.join(UPLOAD_FOLDER, filename))
        # uploadtogcp(os.path.join(UPLOAD_FOLDER, filename))
    
        print('file uploaded successfully')
    imgurl = 'https://storage.googleapis.com/hackybucket/current.jpg'
    labels = gcpocrlib.detect_text_uri(imgurl)
    status = {}
    # status["server"] = "up"
    # status["message"] = "some random message here"
    # status["request"] = "image request" 
    status["results"] = labels

    statusjson = json.dumps(status)

    print(statusjson)

    js = "<html> <body>OK THIS WoRKS</body></html>"

    resp = Response(statusjson, status=200, mimetype='application/json')
    ##resp.headers['Link'] = 'http://google.com'

    return resp








@app.route("/getfoodlabels", methods=["POST"])
def foodify():


    print(request)

    res = request.get_json()
    print (res)
    if res is None:
        return "invalid JSON"


    resraw = request.get_data()
    print (resraw)

    imgurl = res["imgurl"]
    if imgurl is None:
        return "invalid image url"

    # response = model.predict_by_url('https://storage.googleapis.com/hackybucket/current.jpg')
    print(imgurl)
    response = model.predict_by_url(imgurl)
    
    # print (response)
    calorievalue = 0
    names = []
    for x in response["outputs"][0]["data"]["concepts"]:
        print(x["name"])
        if float(x["value"]) < 0.7:
            continue
        print(x["name"])
        print(x["value"])
        name = x["name"]
        names.append(name)   
            

    print (calorievalue)

    ret = {} 
    # ret["calories"] = str(calorievalue)
    ret["names"] = names

    statusjson = json.dumps(ret)

    print(statusjson)

    resp = Response(statusjson, status=200, mimetype='application/json')
    return resp



@app.route("/foodify", methods=["POST"])
def foodifyFile():


    if 'file' not in request.files:
            return "No file part"
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
      return "No selected file"
    if file and allowed_file(file.filename):
        UPLOAD_FOLDER = "./uploads"
  
        filename = secure_filename(file.filename)
        print("filename is " +filename)
        fileuploadname = "./uploads/"+filename
        fileuploadname = filename
        file.save(fileuploadname)
        uploadtogcp(fileuploadname)
        # file.save(os.path.join(UPLOAD_FOLDER, filename))
        # uploadtogcp(os.path.join(UPLOAD_FOLDER, filename))
    
        print('file uploaded successfully')

    response = model.predict_by_url('https://storage.googleapis.com/hackybucket/current.jpg')
    # print(imgurl)
    # response = model.predict_by_url(imgurl)
    
    # print (response)
    calorievalue = 0
    names = []
    for x in response["outputs"][0]["data"]["concepts"]:
        print(x["name"])
        if float(x["value"]) < 0.7:
            continue
        print(x["name"])
        print(x["value"])
        name = x["name"]
        names.append(name)   
            

    print (calorievalue)

    ret = {} 
    # ret["calories"] = str(calorievalue)
    ret["names"] = names

    statusjson = json.dumps(ret)

    print(statusjson)

    resp = Response(statusjson, status=200, mimetype='application/json')
    return resp





@app.route("/textify", methods=['POST'])
def textify():

    print(request)

    res = request.get_json()
    print (res)
    if res is None:
        return "invalid JSON"

    resraw = request.get_data()
    print (resraw)

    imgurl = res["imgurl"]
    if imgurl is None:
        return "invalid image url"
    labels = gcpocrlib.detect_text_uri(imgurl)
    status = {}
    status["server"] = "up"
    status["message"] = "some random message here"
    status["request"] = "some text" 
    status["results"] = labels

    statusjson = json.dumps(status)

    print(statusjson)

    js = "<html> <body>OK THIS WoRKS</body></html>"

    resp = Response(statusjson, status=200, mimetype='application/json')
    ##resp.headers['Link'] = 'http://google.com'

    return resp


@app.route("/textifydate", methods=['POST'])
def textifydate():

    print(request)

    res = request.get_json()
    print (res)
    if res is None:
        return "invalid JSON"

    resraw = request.get_data()
    print (resraw)

    imgurl = res["imgurl"]
    if imgurl is None:
        return "invalid image url"
    labels = gcpocrlib.detect_date_uri(imgurl)
    print(labels)
    labelz = labels.split(" ")
    label = ""
    for l in labelz:
        if "2020" in l:
            label = l
            break
        if "2021" in l:
            label = l
            break
    


    print (label)

    status = {}
    status["server"] = "up"
    status["message"] = "some random message here"
    status["request"] = "some text" 
    status["results"] = label

    statusjson = json.dumps(status)

    print(statusjson)

    js = "<html> <body>OK THIS WoRKS</body></html>"

    resp = Response(statusjson, status=200, mimetype='application/json')
    ##resp.headers['Link'] = 'http://google.com'

    return resp






@app.route("/labelanimage", methods=['POST'])
def labels():

    print(request)

    res = request.get_json()
    print (res)
    if res is None:
        return "invalid JSON"

    resraw = request.get_data()
    print (resraw)



    imageurl = res["imgurl"]
    if imageurl is None:
        return "invalid image url"
    labels = get_top_labels(imageurl)

    status = {}
    status["server"] = "up"
    status["message"] = "some random message here"
    status["request"] = "some request" 
    status["results"] = labels

    statusjson = json.dumps(status)

    print(statusjson)

    js = "<html> <body>OK THIS WoRKS</body></html>"

    resp = Response(statusjson, status=200, mimetype='application/json')
    ##resp.headers['Link'] = 'http://google.com'

    return resp




@app.route("/dummyJson", methods=['GET', 'POST'])
def dummyJson():

    print(request)

    res = request.get_json()
    print (res)

    resraw = request.get_data()
    print (resraw)

##    args = request.args
##    form = request.form
##    values = request.values

##    print (args)
##    print (form)
##    print (values)

##    sres = request.form.to_dict()
 

    status = {}
    status["server"] = "up"
    status["message"] = "some random message here"
    status["request"] = res 

    statusjson = json.dumps(status)

    print(statusjson)

    js = "<html> <body>OK THIS WoRKS</body></html>"

    resp = Response(statusjson, status=200, mimetype='application/json')
    ##resp.headers['Link'] = 'http://google.com'

    return resp




@app.route("/dummy", methods=['GET', 'POST'])
def dummy():

    ##res = request.json

    js = "<html> <body>OK THIS WoRKS</body></html>"

    resp = Response(js, status=200, mimetype='text/html')
    ##resp.headers['Link'] = 'http://google.com'

    return resp

@app.route("/api", methods=["GET"])
def index():
    if request.method == "GET":
        return {"hello": "world"}
    else:
        return {"error": 400}


if __name__ == "__main__":
    app.run(debug=True, host = 'localhost', port = 8002)
    # app.run(debug=True, host = '45.79.199.42', port = 8002)
