import json
from flask import Flask, json,Response, render_template, redirect, request, session, jsonify
import requests
from flask_session import Session
from flask_socketio import SocketIO
import logging as log
from random import random
from threading import Lock
from datetime import datetime
import csv
from pathlib import Path
import pathlib
import os


import time
"""
Background Thread
"""
thread = None
thread_lock = Lock()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'donsky!'
socketio = SocketIO(app, cors_allowed_origins='*')

class MongoAPI:
    def __init__(self, data):
        self.client = MongoClient("mongodb://localhost:27017/") 
        database = data['database']
        collection = data['collection']
        cursor = self.client[database]
        self.collection = cursor[collection]
        self.data = data

    def read(self):
        log.info('Reading All Data')
        documents = self.collection.find()
        output = [{item: data[item] for item in data if item != '_id'} for data in documents]
        return output

    def write(self, data):
        log.info('Writing Data')
        new_document = data['Document']
        response = self.collection.insert_one(new_document)
        output = {'Status': 'Successfully Inserted',
                  'Document_ID': str(response.inserted_id)}
        return output

def get_current_datetime():
    now = datetime.now()
    return now.strftime("%H:%M:%S")


"""
Creating a Resumeable CSV Reader
Map the machine id to the line counter 
when the machine is started, the line counter is set to 0
when the machine is stopped, the line counter is saved
when the machine is started again, the line counter is set to the saved value
"""

def background_thread():

    print("Sensor Data Thread Started...") 
    while(True):
        socketio.emit('updateSensorData', {})
        socketio.sleep(1)

"""
Serve root index file
"""
@app.route("/", methods=["POST", "GET"])
def index():
    if not session.get("userWID"):
        return redirect("/login")
    return render_template('index.html')



@app.route("/createMachine", methods=["POST", "GET"])
def createMachine():
    if not session.get("userWID"):
        return redirect("/login")
    return render_template('createMachine.html')
 
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        session["userWID"] = request.form.get("userWID")
        return redirect("/")
    return render_template("login.html")
 
 
@app.route("/logout")
def logout():
    session["userWID"] = None
    session["machineID"] = None
    return redirect("/")

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/machineRegistration')
def machineRegistration():
    return render_template('machineRegistration.html')

@app.route('/machineSession', methods=["POST", "GET"])
def machineSession():
    if request.method == "POST":
        print(request.json)
        data = request.json
        machineID = data["machineID"]
        session["machineID"] = machineID
        print(machineID)
        return jsonify({})


@app.route('/machineDashboard' , methods=["POST", "GET"])
def machineDashboard():
    if(session["machineID"]):
        return render_template('machineDashboard.html')
    
    
@app.route('/machineTransactions' , methods=["POST", "GET"])
def machineTransactions():
    if(session["machineID"]):
        return render_template('machineTransactions.html')
    

@app.route('/getInfo' , methods=["POST", "GET"])
def getInfo():
    if request.method == "GET":
        info = {
            "machineID": session["machineID"],
            "userWID": session["userWID"]
        }
        return jsonify(info)

@app.route('/getLastTransaction/<address>', methods=["POST", "GET"])
def getLastTransaction(address):
    machineContractAddress = address
    print(machineContractAddress)
    url = "https://console.kaleido.io/api/v1/ledger/u0sdbvxn14/u0anrngbym/addresses/"+machineContractAddress+"/transactions?limit=1"
    payload={}
    headers = {
    'Authorization': 'Bearer u0bt01lis8-YaONAPbJ287Vj4FhH06clwCQRse+dPwwKrPhlpuWpkQ='
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    print(response.json)
    return response.json()


@app.route('/lastMachineMetricsDate', methods=["POST", "GET"])
def lastMachineMetrics():
    machineID = session["machineID"]
    dateFile = pathlib.Path("./state/"+machineID+"date.csv")

    # if(dateFile.exists()):
    #     f = open(dateFile, 'r')
    #     date = f.readline()
    #     f.close()
    # else:
    #     f = open(dateFile, 'w')
    #     f.write("2021-01-01 00") 
    #     f.close()
    date = "2023-01-01 00"

    if request.method == "GET":
        info = {
            "date": date
        }
        return jsonify(info)


@app.route('/updateMachineMetricsDate', methods=["POST", "GET"])
def updateMachineMetricsDate():
    
    if request.method == "POST":
        #print(request.json)
        data = request.json
        date = data["time_stamp"]
        #print(date)
        machineID = session["machineID"]
        dateFile = pathlib.Path("./state/"+machineID+"date.csv")
        f = open(dateFile, 'w')
        f.write(date)
        f.close()
        return jsonify({})


"""
Demo Pages
    machineDashboardDemo
"""
@app.route('/machineDashboardDemo' , methods=["POST", "GET"])
def machineDashboardDemo():
    if(session["machineID"]):
        return render_template('machineDashboardDemo.html')
    
"""
// Demo pages
"""



"""
Decorator for connect
"""
@socketio.on('connect')
def connect():
    global thread
    print('Client connected')
    
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)


"""
Decorator for disconnect
"""
@socketio.on('disconnect')
def disconnect():

    print('Client disconnected',  request.sid)

"""
Database API
    Dashboard Page API
    Transac tion Page API
"""

"""
Dashboard Page API
"""


"""
Transaction Page API
    read machine usage from database using Machine Contract Address
"""
#read machine usage from database using Machine Contract Address
@app.route('/getTransactions', methods=["POST", "GET"])
def mongo_read():
    
    # data = request.json
    # dataJson = jsonify(data)
    filter = "testMachine10"
    # print(filter["machineID"])
    #print(dataJson)
    # if data is None or data == {}:
    #     return Response(response=json.dumps({"Error": "Please provide connection information"}),
    #                     status=400,
    #                     mimetype='application/json')
    #response = [{"jsonStr": {"blockHash": "0xcacb00edb9e8bb89683f1932c96f1416f1c385d8098a06f43e3d99f9b5372a38", "blockNumber": "873519", "cumulativeGasUsed": "70031", "dayStamp": "testMachine10:2021-03-11", "from": "0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8", "gasUsed": "70031", "headers": {"id": "e6977ff7-5df1-4e2b-5d69-6163f5e993db", "requestId": "0383a570-8b08-4a88-799b-320fb02a0c6b", "requestOffset": "", "timeElapsed": 4.516024203, "timeReceived": "2023-03-06T12:30:53.200918569Z", "type": "TransactionSuccess"}, "machineID": "testMachine10", "monthStamp": "testMachine10:-03-11", "nonce": "0", "status": "1", "timeStamp": "testMachine10:2021-03-11", "to": "0x17dfd393f35a889702c9c4530757e82e5052fb35", "transactionHash": "0x28b1bdc7fcbe3aa1782cd90875532d08dde7e4fbd5e5f0a2ded4cc66d2892446", "transactionIndex": "0", "usage": "55"}}, {"jsonStr": {"blockHash": "0xb4a8143633c93b755cb67eb7cbd3eb6e5c3bb1864fd7c3cec87c6336f8cb60e0", "blockNumber": "873520", "cumulativeGasUsed": "59279", "dayStamp": "testMachine10:2021-03-11", "from": "0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8", "gasUsed": "59279", "headers": {"id": "1eb26c7a-d8fc-4826-57e4-230a1e7d70b5", "requestId": "a1b6cf1e-1410-4077-73fc-d65be2648e8a", "requestOffset": "", "timeElapsed": 4.508500977, "timeReceived": "2023-03-06T12:31:03.2010915Z", "type": "TransactionSuccess"}, "machineID": "testMachine10", "monthStamp": "testMachine10:-03-11", "nonce": "0", "status": "1", "timeStamp": "testMachine10:2021-03-11 NaN", "to": "0x17dfd393f35a889702c9c4530757e82e5052fb35", "transactionHash": "0x9447d77e58620b8b609ca77d5b041b243144415035d33e94fc84d7970f3cca5d", "transactionIndex": "0", "usage": "53"}}]


    response = [{"jsonStr":{"blockHash":"0xcacb00edb9e8bb89683f1932c96f1416f1c385d8098a06f43e3d99f9b5372a38","blockNumber":"873519","cumulativeGasUsed":"70031","dayStamp":"testMachine10:2021-03-11","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"70031","headers":{"id":"e6977ff7-5df1-4e2b-5d69-6163f5e993db","requestId":"0383a570-8b08-4a88-799b-320fb02a0c6b","requestOffset":"","timeElapsed":4.516024203,"timeReceived":"2023-03-06T12:30:53.200918569Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-03-11","nonce":"0","status":"1","timeStamp":"testMachine10:2021-03-11","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x28b1bdc7fcbe3aa1782cd90875532d08dde7e4fbd5e5f0a2ded4cc66d2892446","transactionIndex":"0","usage":"55"}},{"jsonStr":{"blockHash":"0xb4a8143633c93b755cb67eb7cbd3eb6e5c3bb1864fd7c3cec87c6336f8cb60e0","blockNumber":"873520","cumulativeGasUsed":"59279","dayStamp":"testMachine10:2021-03-11","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"59279","headers":{"id":"1eb26c7a-d8fc-4826-57e4-230a1e7d70b5","requestId":"a1b6cf1e-1410-4077-73fc-d65be2648e8a","requestOffset":"","timeElapsed":4.508500977,"timeReceived":"2023-03-06T12:31:03.2010915Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-03-11","nonce":"0","status":"1","timeStamp":"testMachine10:2021-03-11 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x9447d77e58620b8b609ca77d5b041b243144415035d33e94fc84d7970f3cca5d","transactionIndex":"0","usage":"53"}},{"jsonStr":{"blockHash":"0x046b1271c35426d456588a52f7b2632cfc55c6285eea0f933afca62f07a34311","blockNumber":"873521","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-03-11","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"c70d5818-f077-456c-74d6-26814b72f41e","requestId":"90a8728c-731e-424e-56e3-c5b368f1a823","requestOffset":"","timeElapsed":4.509843783,"timeReceived":"2023-03-06T12:31:13.198594124Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-03-11","nonce":"0","status":"1","timeStamp":"testMachine10:2021-03-11 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x18605ebd68d7c987d33dcea801a7f737abeefa04b1ab79512c9cb9d2a66209ce","transactionIndex":"0","usage":"52"}},{"jsonStr":{"blockHash":"0xe8cf2517a0e0684660e7dfa9d7489a6d9fe8ecf2dcb51a541b2146d25397d282","blockNumber":"873522","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-03-11","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"5ebe8994-68a9-4257-48cc-078efffd5a78","requestId":"ddb97be2-c015-47f9-62c3-e7e44092a0bb","requestOffset":"","timeElapsed":4.5144367,"timeReceived":"2023-03-06T12:31:23.223088352Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-03-11","nonce":"0","status":"1","timeStamp":"testMachine10:2021-03-11 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x8002d72974f523deacd834abcd6e752ba107b2036f18067051d98064f86f8e08","transactionIndex":"0","usage":"53"}},{"jsonStr":{"blockHash":"0xe63df3a9a22b143d301e05e0774451fb9a7fbb208232335559bfb85f373a8d4e","blockNumber":"873523","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-03-11","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"fbd15df0-09e7-4072-6ec3-eacd8715ef4f","requestId":"69d90502-4ae9-412c-7471-706fc10d9d52","requestOffset":"","timeElapsed":4.514586402,"timeReceived":"2023-03-06T12:31:33.228903412Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-03-11","nonce":"0","status":"1","timeStamp":"testMachine10:2021-03-11 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x978ae3190202d681c13d670b31a13151e841a9b1a71834b01eafc44bfe40e931","transactionIndex":"0","usage":"50"}},{"jsonStr":{"blockHash":"0x8778981fa33424f36cd54bfce51af19f960aebc65843bc6638ec3ce2fe4f9736","blockNumber":"873524","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-03-11","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"e554ae69-50b8-434d-69fa-f9e0ac823570","requestId":"d4877118-66bc-43ea-44d3-74a75c2303db","requestOffset":"","timeElapsed":3.781492259,"timeReceived":"2023-03-06T12:31:43.234510773Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-03-11","nonce":"0","status":"1","timeStamp":"testMachine10:2021-03-11 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0xc386417ef769c17bcba7d8d62402438ed0c79d232c9c7c03a4b8dd63eb6d38a5","transactionIndex":"0","usage":"56"}},{"jsonStr":{"blockHash":"0x7336b1ff455607526e471431a7486827e44b1bca07c1bacb1c78b39c0705b3e7","blockNumber":"873525","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-03-11","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"f40ce080-a2dd-4e4f-67b4-79b5439e7265","requestId":"ab1606b9-f5c1-4bff-4606-419037747d9e","requestOffset":"","timeElapsed":3.774697635,"timeReceived":"2023-03-06T12:31:53.249653373Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-03-11","nonce":"0","status":"1","timeStamp":"testMachine10:2021-03-11 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x983f1f7101b2d6d27bddd9d15b5433a1e7e1213bf47d349fc57c6d613e66fba6","transactionIndex":"0","usage":"53"}},{"jsonStr":{"blockHash":"0x465ea7fdb36a92e852a8fbeca5a74e72f736e5630c933d4e2c60708b1c1f629a","blockNumber":"873526","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-03-11","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"522abfd1-4562-4cbc-6f54-1f7ddf0a7632","requestId":"ccc84a56-0bf9-4b44-44e9-77ad6ccdc125","requestOffset":"","timeElapsed":4.4781331699999996,"timeReceived":"2023-03-06T12:32:03.25534894Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-03-11","nonce":"0","status":"1","timeStamp":"testMachine10:2021-03-11 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x766e88f3955e0cbd0a9053c055e905c2a7bc30f1d3f9f2830d31d94dc3e316d1","transactionIndex":"0","usage":"51"}},{"jsonStr":{"blockHash":"0x24587135bfee7485cec0bb95b3ccf14ead3a19c1c9aef636aa86ab1074687b94","blockNumber":"873528","cumulativeGasUsed":"70031","dayStamp":"testMachine10:2021-05-19","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"70031","headers":{"id":"98b5bb22-4f87-4bef-4036-325afb59d00b","requestId":"ef2e4c85-9fd6-47bd-4b4c-0ba5515dc7a6","requestOffset":"","timeElapsed":3.726699857,"timeReceived":"2023-03-06T12:32:23.835639313Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-05-19","nonce":"0","status":"1","timeStamp":"testMachine10:2021-05-19","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x94623e6b9dfa2d7c44ebc8ca7e6f60b23c86363fc3407e8e6d82a7c04675b4d7","transactionIndex":"0","usage":"55"}},{"jsonStr":{"blockHash":"0x1bd3eb1a7f7f06adbcd4b9504aaf80570defd0f865b6ca92dbf247f84727aeeb","blockNumber":"873529","cumulativeGasUsed":"59279","dayStamp":"testMachine10:2021-05-19","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"59279","headers":{"id":"8daa2186-5327-4e0b-6670-9c9c11227014","requestId":"c14f1255-f645-4dce-782b-ba10dfcfd5f4","requestOffset":"","timeElapsed":4.411382522,"timeReceived":"2023-03-06T12:32:33.290219524Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-05-19","nonce":"0","status":"1","timeStamp":"testMachine10:2021-05-19 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x55d0372350a459226192c39a1af134b36c914ce89e5d1d394b1fcafde3c2d124","transactionIndex":"0","usage":"53"}},{"jsonStr":{"blockHash":"0x3ba6103cab702d575c75d9dd211ead86f0ae939ead243cdbb04fed3d5e200ca5","blockNumber":"873530","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-05-19","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"bf730928-0f31-443d-4f58-6b0ee08141a5","requestId":"4ecb8af7-87d7-463a-4000-7c67f9dc591d","requestOffset":"","timeElapsed":4.393770458,"timeReceived":"2023-03-06T12:32:43.295942301Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-05-19","nonce":"0","status":"1","timeStamp":"testMachine10:2021-05-19 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0xd26b6685089dd1cc036289cdc0db64b7ca63f7181a2528698c0f53482883fe1f","transactionIndex":"0","usage":"52"}},{"jsonStr":{"blockHash":"0xc618782e073f0bb97715a6459fd0b0241c00dfc624a0ae33408a32d4c853e2f0","blockNumber":"873531","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-05-19","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"a2109986-f523-4e05-47a5-cdf2c5027267","requestId":"2b20e70b-5ace-4606-4141-e553e09fe031","requestOffset":"","timeElapsed":4.374979189,"timeReceived":"2023-03-06T12:32:53.302116582Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-05-19","nonce":"0","status":"1","timeStamp":"testMachine10:2021-05-19 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x60c54fdba6af7546bb1162e8a27fdb1f013c01e1711f8e6286a8891dc70fc91b","transactionIndex":"0","usage":"54"}},{"jsonStr":{"blockHash":"0xf162fcf488116169d085dbd5103aa8acc01d44ac7045607bc7bedce71821f909","blockNumber":"873532","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-05-19","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"a3baed27-6880-4134-695b-0a66fed15a95","requestId":"24e70c79-c437-473c-67a3-88b848581781","requestOffset":"","timeElapsed":3.642076244,"timeReceived":"2023-03-06T12:33:03.743888498Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-05-19","nonce":"0","status":"1","timeStamp":"testMachine10:2021-05-19 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x8ab8a3ca0edf9f839ecb1f1620bf982348f8b830c00ac7d0fd1d4c4a8726d124","transactionIndex":"0","usage":"53"}},{"jsonStr":{"blockHash":"0xca8eb3964bb4569a68ef8e85d861567a2fee7739e4dfee79c09af4946fd5c702","blockNumber":"873533","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-05-19","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"085931e3-961c-4794-442c-88ab7cfdf3a2","requestId":"9ebd0f51-8950-4bd1-7de6-0fa8a27918d0","requestOffset":"","timeElapsed":3.617938255,"timeReceived":"2023-03-06T12:33:13.760402523Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-05-19","nonce":"0","status":"1","timeStamp":"testMachine10:2021-05-19 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x3f81c1a6ff98a064d4fac8c0b549b50a2953a29193806fe54dd306e661abc094","transactionIndex":"0","usage":"56"}},{"jsonStr":{"blockHash":"0x544aac71247802da53a4dac82b45c62a782de881eb54ebe10c8a1bfb9c9d9bc2","blockNumber":"873534","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-05-19","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"1ea90678-696e-4208-47a0-a7c4d67046c2","requestId":"11c39834-c21f-46d3-682c-50de1026f94b","requestOffset":"","timeElapsed":3.61367274,"timeReceived":"2023-03-06T12:33:23.768955821Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-05-19","nonce":"0","status":"1","timeStamp":"testMachine10:2021-05-19 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x75afb73e1f9dcec38215234093f81f8e13135c27a8677b1aab12d3529686d638","transactionIndex":"0","usage":"54"}},{"jsonStr":{"blockHash":"0xa1171a5b77942316f612afa34a93cc734086ee3b4f65c41f65e7d95b86126626","blockNumber":"873535","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-05-19","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"d7914df3-0abf-4956-5778-05f2144c7423","requestId":"8b069424-a8b5-4e1d-554f-93cfb53facdc","requestOffset":"","timeElapsed":4.087725616,"timeReceived":"2023-03-06T12:33:33.767647885Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-05-19","nonce":"0","status":"1","timeStamp":"testMachine10:2021-05-19 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0xaa2592a17526b877b8bd9eff8c4d17d5dd4b30872825773d9cae9e8f0d055515","transactionIndex":"0","usage":"52"}},{"jsonStr":{"blockHash":"0x2c180727e9a50661ec4326a27835c2a5b57e0b6dd458c01baf8eb55adb4e0d61","blockNumber":"873551","cumulativeGasUsed":"40031","dayStamp":"testMachine10:2021-03-11","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"40031","headers":{"id":"ded03966-5dd4-448c-60a9-cdf90245ad1c","requestId":"f79ab461-d335-466e-46c9-2f2dc2da5c3c","requestOffset":"","timeElapsed":3.612706551,"timeReceived":"2023-03-06T12:36:14.232479951Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-03-11","nonce":"0","status":"1","timeStamp":"testMachine10:2021-03-11","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x1298e1015ddeea0356a56093b6438c302a3ed0b455858ab30636d1284c473389","transactionIndex":"0","usage":"55"}},{"jsonStr":{"blockHash":"0x943b5e63132aaf1e392dadd7d49a958a4bb49514620ccfdf5cb22c88bfe78f78","blockNumber":"873552","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-03-11","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"d3cd0ed8-f536-4d06-5455-6192c8a4f0bb","requestId":"b26f8e4e-6160-4309-6d0c-278f7d78aa47","requestOffset":"","timeElapsed":3.586458153,"timeReceived":"2023-03-06T12:36:23.745968636Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-03-11","nonce":"0","status":"1","timeStamp":"testMachine10:2021-03-11 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x67ae331591f4c7151737b08de28104e802a608148938412fbdaf02556f3cdc41","transactionIndex":"0","usage":"53"}},{"jsonStr":{"blockHash":"0x02281d3cd4f1303dc997df566e5516e87fef5e60340bfb4531f0231452bc972f","blockNumber":"873553","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-03-11","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"63c9c432-40a1-4ea0-5d9b-f49ae3f7d8e5","requestId":"a866eda2-b8c8-472a-41b6-dbef194c9b94","requestOffset":"","timeElapsed":3.57746062,"timeReceived":"2023-03-06T12:36:33.7598689Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-03-11","nonce":"0","status":"1","timeStamp":"testMachine10:2021-03-11 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0xc40bcad477e5b3601995697a419e5a238ab3662e733c4db6593cdb65c4a192b2","transactionIndex":"0","usage":"55"}},{"jsonStr":{"blockHash":"0x63df9bd72e89b4db71802b528ed43eeb394a48c43bdf0036595c04f9d7b4ca73","blockNumber":"873554","cumulativeGasUsed":"44279","dayStamp":"testMachine10:2021-03-11","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44279","headers":{"id":"7c3ebc4a-3c2c-4636-50a6-65b2d24e5ec0","requestId":"e9852e14-0c24-41f9-5b93-7d7786bd4976","requestOffset":"","timeElapsed":3.568280686,"timeReceived":"2023-03-06T12:36:43.77482537Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-03-11","nonce":"0","status":"1","timeStamp":"testMachine10:2021-03-11 NaN","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0xe9e14b733ea783db4c2b6a1b940e697a5e24eb3978842141472f6baf7393e96f","transactionIndex":"0","usage":"51"}},{"jsonStr":{"blockHash":"0x219fdc03ada9c2ef0fe60742339ec86cba79be44c74a2e18167eacae36dbd327","blockNumber":"873800","cumulativeGasUsed":"44267","dayStamp":"testMachine10:2020-12-31","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44267","headers":{"id":"0f13156e-9e4f-4994-5e2e-5a9bf2afe443","requestId":"4e1bd83d-3341-48c3-4b08-f7722dbfa67d","requestOffset":"","timeElapsed":5.990993231,"timeReceived":"2023-03-06T13:17:42.285044458Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-12-31","nonce":"0","status":"1","timeStamp":"testMachine10:2020-12-31 16","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x37c0887d7343a283013b6b524cccea11fbe750d55c338f933a69a993c29dd894","transactionIndex":"0","usage":"53"}},{"jsonStr":{"blockHash":"0x37da82d3c13438b7e0f088687bd687c095cfb59ab1a36669e3c04a52655b8d11","blockNumber":"873801","cumulativeGasUsed":"44267","dayStamp":"testMachine10:2020-12-31","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"44267","headers":{"id":"6ab1cde4-e472-40a0-7569-3c12c011997a","requestId":"2958898d-c560-4962-489a-fce41a0dc63e","requestOffset":"","timeElapsed":5.9829644,"timeReceived":"2023-03-06T13:17:52.3275242Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-12-31","nonce":"0","status":"1","timeStamp":"testMachine10:2020-12-31 17","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x960aa9e2755f8b650ad4e61137f659d4f1f77b4525f352028a6b993d3507b75a","transactionIndex":"0","usage":"51"}},{"jsonStr":{"blockHash":"0x36e04d4f60bc026d7627bfe64bc66336a3260be13d18de71b69bd8331563b0f1","blockNumber":"874401","cumulativeGasUsed":"89267","dayStamp":"testMachine10:2020-12-30","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"89267","headers":{"id":"0f078812-d599-41e3-549a-fa714a64c332","requestId":"46bda05e-882c-45e5-634a-dfc591e302f6","requestOffset":"","timeElapsed":8.678269676,"timeReceived":"2023-03-06T14:57:48.333827623Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-12-30","nonce":"0","status":"1","timeStamp":"testMachine10:2020-12-30 22","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0xa87d959f83f809d34b15ab9c972321e116aaab020c7e50a9e3ab1a3b896ef7b2","transactionIndex":"0","usage":"50"}},{"jsonStr":{"blockHash":"0xd5e6384924a3dd37165cb1b646763f23b52465c609a37d4c4a7d5aa8ef0e9396","blockNumber":"874402","cumulativeGasUsed":"59267","dayStamp":"testMachine10:2020-12-30","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"59267","headers":{"id":"5c6d51d2-0180-48ed-6f41-45ac88bbadfd","requestId":"8148a0d4-3573-4a86-615e-cedb490a9d72","requestOffset":"","timeElapsed":8.736466312,"timeReceived":"2023-03-06T14:57:58.344250175Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-12-30","nonce":"0","status":"1","timeStamp":"testMachine10:2020-12-30 23","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x7bafab6c9519bd2da7f10e0d506d44b8838f17d9d06d224cf9ad0acc816af9c5","transactionIndex":"0","usage":"53"}},{"jsonStr":{"blockHash":"0xb327d702cd3854e7873be7d6c83f8b316d67caff2b2c5ac1f7e87e20508eb924","blockNumber":"874403","cumulativeGasUsed":"59267","dayStamp":"testMachine10:2020-12-31","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"59267","headers":{"id":"de4d2e17-d8f1-43b2-7f4d-3cb3ba73aaa7","requestId":"5f8f621f-da16-4c9c-7d95-f2d01a4aaa3f","requestOffset":"","timeElapsed":8.801522476,"timeReceived":"2023-03-06T14:58:08.368763182Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-12-31","nonce":"0","status":"1","timeStamp":"testMachine10:2020-12-31 00","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0xeeabf6c81e25d6035a29df9c4aa17a975f1fb55b11e6ea5386757d1c3a847d4b","transactionIndex":"0","usage":"50"}},{"jsonStr":{"blockHash":"0x7b8ec6d71306d156a9331d3a7c27c5a4381988140f41054f1b7f75000781739d","blockNumber":"874404","cumulativeGasUsed":"59267","dayStamp":"testMachine10:2020-12-31","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"59267","headers":{"id":"c2a947a9-4d4b-426f-7a21-2da24d7a2f3d","requestId":"98f10d22-c9c5-40f7-432f-493691fce9c3","requestOffset":"","timeElapsed":8.854123788999999,"timeReceived":"2023-03-06T14:58:18.396060196Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-12-31","nonce":"0","status":"1","timeStamp":"testMachine10:2020-12-31 01","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x7f92303c7fdde0183edf4c052659d531fd7f7a13462780ce143eea376d3a3740","transactionIndex":"0","usage":"56"}},{"jsonStr":{"blockHash":"0x392bffcbee776ba1bae51ce4b72b4888d4533bb17d6b063230dff7b3a7e65f20","blockNumber":"874495","cumulativeGasUsed":"59267","dayStamp":"testMachine10:2020-12-31","from":"0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8","gasUsed":"59267","headers":{"id":"c85fca8b-ab17-4a67-77e8-dc1240d287b4","requestId":"639fa9d5-9c66-4ac7-6bfd-e5787020cb6b","requestOffset":"","timeElapsed":7.361089181,"timeReceived":"2023-03-06T15:13:30.41366466Z","type":"TransactionSuccess"},"machineID":"testMachine10","monthStamp":"testMachine10:-12-31","nonce":"0","status":"1","timeStamp":"testMachine10:2020-12-31 78","to":"0x17dfd393f35a889702c9c4530757e82e5052fb35","transactionHash":"0x36b94c0e35b2f0c12fc07792444e19c1daac354920fa81851c68e3b3d3f3dbcd","transactionIndex":"0","usage":"51"}}]
    
    result = []
    for x in response:
        for key, value in x.items():
            if(key == "jsonStr"):
                #print(type(value))
                        #print(value.get('machineID'))
                        result.append(x)
                        continue

    return Response(response=json.dumps(result),
                    status=200,
                    mimetype='application/json')


#write machine usage to database
@app.route('/mongodb', methods=['POST'])
def mongo_write():
    data = request.json
    if data is None or data == {} or 'Document' not in data:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    obj1 = MongoAPI(data)
    response = obj1.write(data)
    return Response(response=json.dumps(response),
                    status=200,
                    mimetype='application/json')

"""
Main function
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
