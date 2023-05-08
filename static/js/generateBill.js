/*
    Generate Bill
    Author: Nithish Pranav
    
    This file is used to generate the bill for the machine.
    It uses the machine contract address to fetch the last transaction timestamp.
    It uses the last transaction from the machine contract to calculate the usage.
    It uses the machine value to calculate the bill.
    It uses the manufacturer and financier wallet id to transfer the bill amount to the manufacturer.

    Functions:
    generateBill() - start the flow of generating the bill. Gets the machine id and user id from the server.
    getContractDetails() - This function is used to get the contract details of the machine.
    getLastTransaction() - This function is used to get the last transaction details of the machine.
    calculateBill() - This function is used to calculate the bill amount.
    getUsage() - This function is called by the calculate bill to fetch the usage details per date.

    we assume the per hour usage is 10 tokens.
    per_hour_usage = 10;
*/

const { json } = require("body-parser");

  function generateBill(){
    document.getElementById("billContainer").style.display = "none";
    document.getElementById("billContainerLoader").style.display = "block";

    console.log("machineDetails");
    fetch('/getInfo')
      .then(response => response.json())
      .then(data => {
        console.log(data);
        machineId = data.machineID;
        userWID = data.userWID;
        calculateBill(machineId,userWID);
      })
      .catch(error => console.log('error', error)); 
  }
  async function getContractDetails(machineId,userWID){
    return new Promise(async (resolve, reject) => {
    var machine_id = machineId;
    // var machine_value;
    // var manufacturer_wallet_id;
    // var financier_wallet_id;
    // var machine_contract_address;
    var kld_from = "kld-from="+userWID;
    var url ="https://u1afypqnup-u1qc0kallb-connect.us1-azure.kaleido.io/instances/"+machine_id+"/contractDetails?"+kld_from;
    var myHeaders = new Headers();
    myHeaders.append("Authorization", "Basic dTFzeDlhMmpkMTppZkdwNFFKS2gtU3RLTlZTR0RZc2xQMHBmZEdMelFJMHhiSXAzNHRzNGQ4");
    var requestOptions = {
        method: 'POST',
        headers: myHeaders,
        redirect: 'follow'
    };
    const response  = await fetch(url, requestOptions)
      .then(response => response.text())
      .then(result => {
          console.log(result);
          var machineDetails = JSON.parse(result);
          resolve(machineDetails);
          // machine_value = machineDetails.output1;
          // financier_wallet_id = machineDetails.output2;
          // manufacturer_wallet_id = machineDetails.output3;
          // machine_contract_address = machineDetails.output4;
          // calculateBill(machineId,financier_wallet_id,manufacturer_wallet_id,machine_contract_address);        
      })
      .catch(error => console.log('error', error));
    });

  }

  async function calculateBill(machine_id,userWID){

    // const data = await getContractDetails(machine_id, userWID);
    // console.log(data);

    //var financier_wallet_id = data.output2;



    var from_date = document.getElementById("from_date").value;
    var to_date = document.getElementById("to_date").value;
    var per_hour_usage = 10;

    console.log("from_date"+from_date);
    console.log("to_date"+to_date);

    var totalUsage = 0;
    var from_dateDate = from_date;
    var from_dateYear = parseInt(from_date.slice(0,4));
    var from_dateMonth = parseInt(from_date.slice(5,7));
    var from_dateDate = parseInt(from_date.slice(8,10));

    const tempDate = new Date(from_dateYear,from_dateMonth-1,from_dateDate);
    var d = new Date(tempDate);

    var dateYear = parseInt(to_date.slice(0,4));
    var dateMonth = parseInt(to_date.slice(5,7));
    var dateDate = parseInt(to_date.slice(8,10));

    temp_to_date = new Date(dateYear,dateMonth-1,dateDate);
    var td = new Date(temp_to_date);

    // var tempYear = from_dateYear;
    // var tempMonth = from_dateMonth;
    console.log("tempDate"+tempDate);
    console.log("to_date"+temp_to_date);
    
    
    while(tempDate<temp_to_date){
      console.log("while loop"+tempDate,to_date);
      totalUsage+= await getDayUsageDataFromDB(tempDate,machine_id);
      console.log("totalUsage"+totalUsage);
      tempDate.setDate(tempDate.getDate()+1);
      console.log(tempDate);
    }
    totalUsage = totalUsage/60;
    console.log("totalUsage"+totalUsage);
    
    var bill = totalUsage*per_hour_usage;
    document.getElementById("bill_usage").innerHTML = totalUsage;
    document.getElementById("bill_cost").innerHTML = bill;
    document.getElementById("bill").style.display = "block";
    document.getElementById("billContainerLoader").style.display = "none";

    document.getElementById("billContainer").style.display = "block";
  }

  async function getDayUsageDataFromDB(date,machine_id){


    var month = parseInt(date.getMonth())+1;
    if(month<10)
    month = "0"+month;
  
    if(date.getDate()<10)
      day = "0"+date.getDate();
    else
      day = date.getDate();

    var time_stamp = (date.getFullYear()+'-'+month+'-'+day);
    var time_stamp = machine_id+":"+time_stamp;



    var getTransaction;
    console.log(time_stamp);
    var myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");
    
  
    var raw = JSON.stringify({
    "database": "demoDB",
    "collection": "recordUsage",
    "filter": {
        "machineID": machineId
    }
    });
  
    var requestOptions = {
    method: 'POST',
    headers: myHeaders,
    body: raw,
    redirect: 'follow'
    };
    const res = await fetch("http://localhost:5000/getTransactions", requestOptions)
    .then(res => res.json())
    .then(
        result => {
            getTransaction = result;
        }
        )
    .catch(error => console.log('error', error));
    
    var dayUsage = 0;
    getTransaction.forEach(element => {
      //console.log(element.jsonStr["dayStamp"]);
        if(element.jsonStr["dayStamp"] == time_stamp){
          //console.log(element.jsonStr["usage"]);
            dayUsage += parseInt(element.jsonStr["usage"]);
        }
    });
    console.log(dayUsage);
    return(dayUsage);
    //return dayUsage;
  
  }

  async function getUsage(date,machine_id,financier_wallet_id){
    var month = parseInt(date.getMonth())+1;
    if(month<10)
    month = "0"+month;
  
    if(date.getDate()<10)
      day = "0"+date.getDate();
    else
      day = date.getDate();

    var dayStamp = (date.getFullYear()+'-'+month+'-'+day);
    var dayStamp = machine_id+":"+dayStamp;
    var kld_from = "kld-from="+financier_wallet_id;
    console.log(dayStamp);
    var dayUsage;
    var usage = 0;
    var data = "timeStamp="+dayStamp;
    var url = "https://u0anrngbym-u0kuxslxro-connect.us0-aws.kaleido.io/instances/0xa8b0124d967f9e18c16d8a5dfcff1bc10ef8cb1c/returnUsage?"+data+"&"+kld_from+"&kld-sync=true";
    var myHeaders = new Headers();
    myHeaders.append("Authorization", "Basic dTBwNjgwb3pvMDpqN3dLUHRZa0xrNnBITlNDQTlDckJaNVM3MlBFemtCSGtxbjVSVkdESGRF");
    myHeaders.append("Content-Type", "application/json");

    //var raw = JSON.stringify({"timeStamp":dayStamp});
    var requestOptions = {
      method: 'GET',
      headers: myHeaders,
      redirect: 'follow'
    };

    const response  = await fetch(url, requestOptions)
      .then(response => response.json())
      .then(result => {
        console.log(result);
        //return parseInt(result.output);
        dayUsage = parseInt(result.output);
        console.log("dayUsage"+dayUsage);
        
      })
      .catch(error => console.log('error', error));
      console.log("dayUsage"+dayUsage);
      return dayUsage;
  }



  function payBill(){
    document.getElementById("main").style.display = "none";
    document.getElementById("l").style.display = "block";
    document.getElementById("loader").style.display = "block";
    var machine_id
    console.log("machineDetails");
    fetch('/getInfo')
      .then(response => response.json())
      .then(data => {
        console.log(data);
        machine_id = data.machineID;
        userWID = data.userWID;
        transferTokens(machine_id, userWID);
      })
      .catch(error => console.log('error', error)); 

    }

  async function transferTokens(machine_id, userWID){
    //var machine_id = document.getElementById("machine_id").value;

    const data = await getContractDetails(machine_id, userWID);

    var amount = document.getElementById("bill_cost").innerHTML;//must be changed to backend
    amount = Math.round(parseInt(amount));
    var recipient = data.output3;
    var sender = data.output2;

    var kld_from = "kld-from="+sender;
    var myHeaders = new Headers();
    myHeaders.append("Authorization", "Basic dTFzeDlhMmpkMTppZkdwNFFKS2gtU3RLTlZTR0RZc2xQMHBmZEdMelFJMHhiSXAzNHRzNGQ4");
    myHeaders.append("Content-Type", "application/json");
    var raw = JSON.stringify({
      "amount": amount,
      "to": recipient,
      "from": sender
    });
    var requestOptions = {
      method: 'POST',
      headers: myHeaders,
      body: raw,
      redirect: 'follow'
    };
    fetch("https://u1afypqnup-u1qc0kallb-connect.us1-azure.kaleido.io/instances/"+machine_id+"/transferFrom?"+kld_from+"&kld-sync=true" , requestOptions)
      .then(response => response.text())
      .then(result => {
        console.log(result);
        setTimeout(() => getAddressBalance(machine_id, userWID, sender, recipient), 6000);
        document.getElementById("main").style.display = "block";
        document.getElementById("l").style.display = "none";

      })
      .catch(error => console.log('error', error));
  }    
