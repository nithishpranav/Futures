import json
from flask import Flask, json,Response, render_template, redirect, request, session, jsonify
import requests
from flask_session import Session
from flask_socketio import SocketIO
from pymongo import MongoClient
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
        print(database)
        print(collection)
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

class SymbolMongoAPI:
    def __init__(self, data):
        self.client = MongoClient("mongodb://localhost:27017/")
        database = "Futures"
        collection = "Symbols"
        cursor = self.client[database]
        self.collection = cursor[collection]
        self.data = data

    def read(self):
        log.info('Reading All Data')
        documents = self.collection.find()
        output = [{item: data[item] for item in data if item != '_id'} for data in documents]
        return output
    
    def find(self, symbol):
        log.info('Reading All Data')
        documents = self.collection.find_one({"symbol": symbol})
        output = [{item: documents[item] for item in documents if item != '_id'}]
        #return documents
        return output
    


class UserMongoAPI:
    def __init__(self, data):
        self.client = MongoClient("mongodb://localhost:27017/")
        database = "Futures"
        collection = "users"
        cursor = self.client[database]
        self.collection = cursor[collection]
        self.data = data
    
    def find(self, walletAddress):
        log.info('Reading All Data')
        documents = self.collection.find_one({"walletAddress": walletAddress})
        output = [{item: documents[item] for item in documents if item != '_id'}]
        #return documents
        return output
    
    def getOrders(self, walletAddress):
        log.info('Reading All Data')
        document = self.collection.find_one({"walletAddress": walletAddress})
        if document is None:
            return jsonify({'error': 'Document not found'})
        #return documents
        orders = document.get('Orders', [])
        return jsonify({'Orders': orders})
    
    def getTrades(self, walletAddress):
        log.info('Reading All Data')
        document = self.collection.find_one({"walletAddress": walletAddress})
        if document is None:
            return jsonify({'error': 'Document not found'})
        #return documents
        trades = document.get('Trades', [])
        return jsonify({'Trades': trades})

    def addOrder(self, data):
        #data = data.json
        print(data)
        # Extract the necessary information from the input
        walletAddress = data['userWID']
        symbol = data['symbol']
        orderID = data['orderID']
        log.info('Reading All Data')
        documents = self.collection.update_one({"walletAddress": walletAddress}, {"$push": {"Orders": {"order": {"symbol": symbol, "orderID": orderID}}}})
        #output = [{item: documents[item] for item in documents if item != '_id'}]
        #return documents
        return documents.modified_count    

    def deleteOrder(self, data):
        print(data)
        walletAddress = data['userWID']
        symbol = data['symbol']
        orderID = data['orderID']
        documents = self.collection.update_one(
            {'walletAddress': walletAddress},
            {'$pull': {'Orders': {'order.symbol': symbol, 'order.orderID': orderID}}}
        )
        return documents.modified_count

    def addTrade(self, data):
        print(data)
        walletAddress = data['userWID']
        symbol = data['symbol']
        tradeID = data['tradeID']
        documents = self.collection.update_one(
            {"walletAddress": walletAddress}, 
            {"$push": {"Trades": {"trade": {"symbol": symbol, "tradeID": tradeID}}}}
        )
        return documents.modified_count
    

    def deleteTrade(self, data):
        print(data)
        walletAddress = data['userWID']
        symbol = data['symbol']
        tradeID = data['tradeID']
        documents = self.collection.update_one(
            {'walletAddress': walletAddress},
            {'$pull': {'Trades': {'trade.symbol': symbol, 'trade.tradeID': tradeID}}}
        )
        return documents.modified_count


# get the list of all the orders/trades placed by the user

@app.route('/getOrders', methods=['POST'])
def getOrders():
    print("get_orders")
    data = request.json
    print(data)
    obj = UserMongoAPI(data)
    response  = obj.getOrders(data['userWID'])
    return response


@app.route('/getTrades', methods=['POST'])
def getTrades():
    print("get_trades")
    data = request.json
    print(data)
    obj = UserMongoAPI(data)
    response  = obj.getTrades(data['userWID'])
    return response

    


# the order placed by the user is added to user's openTrades array
@app.route('/addOrder', methods=['POST'])
def addOrder():
    print("add_order")
    data = request.json
    print(data)
    obj = UserMongoAPI(data)
    response  = obj.addOrder(data)
    if response == 1:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})


# the order is executed and becomes a trade
#  delete the order from the orders array and add it to the trades array

@app.route('/deleteOrder', methods=['POST'])
def deleteOrder():
    print("delete_order")
    #print(request.json)
    # Parse the JSON input received from the client-side

    data = request.json
    print(data)
    obj = UserMongoAPI(data)
    response  = obj.deleteOrder(data)
    if response == 1:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})
    

@app.route('/addTrade', methods=['POST'])
def addTrade():
    print("add_trade")

    data = request.json
    print(data)
    obj = UserMongoAPI(data)
    response  = obj.addTrade(data)


    if response == 1:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})


@app.route('/deleteTrade', methods=['POST'])
def deleteTrade():
    print("delete_trade")
    #print(request.json)
    # Parse the JSON input received from the client-side

    data = request.json
    print(data)
    obj = UserMongoAPI(data)
    response  = obj.deleteTrade(data)
    if response == 1:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})
    

# events

@app.route('/orderMatched', methods=['POST'])
def orderMatched():
    data = request.json
    print(data)
    return jsonify({'success': True})
    # delete the order from the orders array 
    

@app.route('/tradeCreated', methods=['POST'])
def tradeCreated():
    data = request.json
    print(data)
    return jsonify({'success': True})
    # add the trade to the trades array





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



@app.route("/createTrade", methods=["POST", "GET"])
def createTrade():
    if not session.get("userWID"):
        return redirect("/login")
    return render_template('createTrade.html')

@app.route("/myTrades", methods=["POST", "GET"])
def myTrades():
    if not session.get("userWID"):
        return redirect("/login")
    return render_template('myTrades.html')
 
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
            "userWID": session["userWID"]
        }
        return jsonify(info)

@app.route('/getAccountDetails' , methods=["POST", "GET"])
def getAccountDetails():
    if request.method == "GET":
        
        #"userWID": session["userWID"]
        url = "https://console-us1.kaleido.io/api/v1/consortia/u1zcnjj8mm/environments/u1afypqnup/eth/getbalance/"+ session["userWID"]

        payload = {}
        headers = {
        'Authorization': 'Bearer u0mywx3301-z7CQdXd2DwI5exnrL5oEA/0/7vRa2wko6sYWdGybNCA='
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        
        data = json.loads(response.text)
        data.update({"userWID": session["userWID"]})
        print(data)

        return (data)


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
# @app.route('/getTransactions', methods=["POST", "GET"])
# def mongo_read():
    
    # data = request.json
    # dataJson = jsonify(data)
    # filter = "testMachine10"
    # print(filter["machineID"])
    #print(dataJson)
    # if data is None or data == {}:
    #     return Response(response=json.dumps({"Error": "Please provide connection information"}),
    #                     status=400,
    #                     mimetype='application/json')
    #response = [{"jsonStr": {"blockHash": "0xcacb00edb9e8bb89683f1932c96f1416f1c385d8098a06f43e3d99f9b5372a38", "blockNumber": "873519", "cumulativeGasUsed": "70031", "dayStamp": "testMachine10:2021-03-11", "from": "0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8", "gasUsed": "70031", "headers": {"id": "e6977ff7-5df1-4e2b-5d69-6163f5e993db", "requestId": "0383a570-8b08-4a88-799b-320fb02a0c6b", "requestOffset": "", "timeElapsed": 4.516024203, "timeReceived": "2023-03-06T12:30:53.200918569Z", "type": "TransactionSuccess"}, "machineID": "testMachine10", "monthStamp": "testMachine10:-03-11", "nonce": "0", "status": "1", "timeStamp": "testMachine10:2021-03-11", "to": "0x17dfd393f35a889702c9c4530757e82e5052fb35", "transactionHash": "0x28b1bdc7fcbe3aa1782cd90875532d08dde7e4fbd5e5f0a2ded4cc66d2892446", "transactionIndex": "0", "usage": "55"}}, {"jsonStr": {"blockHash": "0xb4a8143633c93b755cb67eb7cbd3eb6e5c3bb1864fd7c3cec87c6336f8cb60e0", "blockNumber": "873520", "cumulativeGasUsed": "59279", "dayStamp": "testMachine10:2021-03-11", "from": "0x81db5f1e9d7fdd3bb8ca2ec20edb4dbd2f58b8a8", "gasUsed": "59279", "headers": {"id": "1eb26c7a-d8fc-4826-57e4-230a1e7d70b5", "requestId": "a1b6cf1e-1410-4077-73fc-d65be2648e8a", "requestOffset": "", "timeElapsed": 4.508500977, "timeReceived": "2023-03-06T12:31:03.2010915Z", "type": "TransactionSuccess"}, "machineID": "testMachine10", "monthStamp": "testMachine10:-03-11", "nonce": "0", "status": "1", "timeStamp": "testMachine10:2021-03-11 NaN", "to": "0x17dfd393f35a889702c9c4530757e82e5052fb35", "transactionHash": "0x9447d77e58620b8b609ca77d5b041b243144415035d33e94fc84d7970f3cca5d", "transactionIndex": "0", "usage": "53"}}]


    
    # result = []
    # for x in response:
    #     for key, value in x.items():
    #         if(key == "jsonStr"):
    #             #print(type(value))
    #                     #print(value.get('machineID'))
    #                     result.append(x)
    #                     continue

    # return Response(response=json.dumps(result),
    #                 status=200,
    #                 mimetype='application/json')



#write machine usage to database
@app.route('/mongodb', methods=['GET'])
def mongo_readall():
    data = request.json
    if data is None or data == {}:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    obj1 = MongoAPI(data)
    response = obj1.read()
    return Response(response=json.dumps(response),
                    status=200,
                    mimetype='application/json')

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


@app.route('/mongodb', methods=['GET'])
def mongo_read():
    data = request.json
    if data is None or data == {}:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    obj1 = MongoAPI(data)
    response = obj1.read()
    return Response(response=json.dumps(response),
                    status=200,
                    mimetype='application/json')

@app.route('/getSymbols', methods=['GET', 'POST'])
def getSymbols():
    data = request.json
    if data is None or data == {}:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    obj1 = SymbolMongoAPI(data)
    response = obj1.read()
    return Response(response=json.dumps(response),
                    status=200,
                    mimetype='application/json')

@app.route('/findBySymbol/<symbol>', methods=['GET', 'POST'])
def findBySymbol(symbol):
    session["symbol"] = symbol
    data = request.json
    if data is None or data == {}:
        return Response(response=json.dumps({"Error": "Please provide connection information"}),
                        status=400,
                        mimetype='application/json')
    obj1 = SymbolMongoAPI(data)
    print("symbol:"+symbol)
    response = obj1.find(symbol)
    return Response(response=json.dumps(response),
                    status=200,
                    mimetype='application/json')




"""
Main function
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
