/*
while staring the server we must get the machine data from the machine contract to the startServer function


*/
async function startServer(machineID, userWID,financierWalletID, manufacturerWalletID) {

  var financierWID = financierWalletID
  var manufacturerWID = manufacturerWalletID
  const MAX_DATA_COUNT = 100;
  var socket = io.connect();

  var populateDayChartFlag = true ;
  var populateMetricsFlag = true;
  var startDate;
  const MAX_DAY_USAGE_COUNT = 31;
  const duc = document.getElementById("dayUsageChart");
  const ctx = document.getElementById("myChart").getContext("2d");

  const myChart = new Chart(ctx, {
    type: "line",
    data: {
      datasets: [

        { label: "Voltage",
          borderColor: ['rgba(25, 119, 12, 1)',],
        },
        {
          label: "Rotation",
          borderColor: ['rgba(255, 99, 132, 1)',],
        },
        {
          label: "Vibration",
          borderColor: ['rgba(115, 9, 122, 1)',],
        },
        {
          label: "Pressure",
          borderColor: ['rgba(215, 119, 12, 1)',],
        }
      ],
    }
  });


  const dayUsageChart = new Chart(duc,{
    type: "bar",
    data: {
      datasets: [
        {
          label: "Usage",
          backgroundColor: ['rgba(25, 99, 132, 1)',],
      }
    ],
    },
    options :{
      scales: {
        y: {
          title: {
            display: true,
            text: 'Machine Usage (hours)'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Date'
          }
        }
      }     
    }

  });

  const response  = await fetch('/lastMachineMetricsDate')
    .then(response => response.json())
    .then(data =>{
      console.log(data);
      startDate = data.date;
    })
  //console.log(data);
  //console.log(data.date);
  time_stamp = startDate;
  console.log(startDate);


  if(populateDayChartFlag){
    await populateMetrics(startDate);
    await populateDayChart(startDate,machineID,userWID);
    populateDayChartFlag = false;
  }



  socket.on("updateSensorData", async function () {
    max = 100;
    min = 90;
    volt_value = Math.random() * (170 - 160) + 160;
    rotate_value = Math.random() * (420 - 380) + 380;
    vibration_value = Math.random() * (max - min) + min;
    pressure_value = Math.random() * (max - min) + min;
    //console.log("Received sensorData :: " + time_stamp + " :: " + volt_value+" :: " + rotate_value+"::" + vibration_value+"::" + pressure_value);
    if (myChart.data.labels.length > MAX_DATA_COUNT) {
      removeFirstData();
    }
    addData(time_stamp,volt_value,rotate_value,vibration_value,pressure_value);
    
    //update date
    var dateYear = parseInt(time_stamp.slice(0,4));
    var dateMonth = parseInt(time_stamp.slice(5,7));
    var dateDate = parseInt(time_stamp.slice(8,10));
    var tempDate = new Date(dateYear,dateMonth-1,dateDate);
    var nextDate = new Date(tempDate)
    //console.log("next day "+time_stamp);
    //console.log("next day "+nextDate)
    var hour = parseInt(time_stamp.slice(11,13))
    //console.log("hour"+ hour);
    if(hour == 23){
      nextDate.setDate(nextDate.getDate()+1);
      hour = '00'
    }
    else if (hour<9){
      hour = hour + 1;
      hour = '0'+hour;
    }
    else{
      hour = hour+1;
    }
    var month = parseInt(nextDate.getMonth())+1;
    if(month<10)
    month = "0"+month;
  
    if(nextDate.getDate()<10)
      day = "0"+nextDate.getDate();
    else
      day = nextDate.getDate();
    var temp = (nextDate.getFullYear()+'-'+month+'-'+day);



    time_stamp = temp+" "+hour;
    //console.log("next day "+time_stamp);
    
    //write timestamp to file
    var updateTimeStampData = {
      'time_stamp': time_stamp
    } 
    var requestOptions = {
      method: "POST",
      headers: new Headers({
          'Content-Type': 'application/json'
      }),
      body: JSON.stringify(updateTimeStampData)
    }
    fetch('/updateMachineMetricsDate',requestOptions)
      .then(response => response.json())
      .catch(error => console.log('error', error));
  }
  );




  /*
  machine telemetry data chart 
  */



  function addDayUsageData(label, usage) {
    //console.log("addDayUsageData "+label+"::"+usage)
    var usage = usage/60;
    if (dayUsageChart.data.labels.length > MAX_DAY_USAGE_COUNT) {
      removeFirstDayUsageData();
    }
    dayUsageChart.data.labels.push(label);
    dayUsageChart.data.datasets[0].data.push(usage);
    dayUsageChart.update();
  }

  function removeFirstDayUsageData() {
    dayUsageChart.data.labels.splice(0, 1);
    dayUsageChart.data.datasets.forEach((dataset) => {
      dataset.data.shift();
    });
  }

  function addData(label, volt_data, rotate_data, vibration_data, pressure_data) {
    myChart.data.labels.push(label);
    myChart.data.datasets[0].data.push(volt_data);
    myChart.data.datasets[1].data.push(rotate_data);
    myChart.data.datasets[2].data.push(vibration_data);
    myChart.data.datasets[3].data.push(pressure_data);
    myChart.update();
    /*
    FORMULA FOR CALCULATING THE USAGE
    Vibration metric
    weight = 0.75
    max = 80
    formula = (value/max)*weight
    COST PER HOUR = 10 tokens per hour
    */
    var usage = (vibration_data/80)*0.75*60;
    //console.log("usage"+usage);

    usageContract(machineID,financierWID,usage,label);
    //console.log(label);
    var hour = parseInt(label.slice(11,13));
    if (hour === 23){
      var day = label.slice(0,10);
      var dayStamp = machineID+":"+label.slice(0,10);
      getDayUsageData(day,dayStamp);
      //console.log(dayUsage);
      //addDayUsageData(day,dayUsage);
    }
  }

  function getDayUsageData(day,dayStamp) {
    console.log("getDayUsageData"+dayStamp);
    
    var kld_from = "kld-from="+financierWID;
    var url = "https://u1afypqnup-u1qc0kallb-connect.us1-azure.kaleido.io/instances/machineusage/returnUsage?"+kld_from+"&kld-sync=true";
    var myHeaders = new Headers();
    myHeaders.append("Authorization", "Basic dTFzeDlhMmpkMTppZkdwNFFKS2gtU3RLTlZTR0RZc2xQMHBmZEdMelFJMHhiSXAzNHRzNGQ4");
    myHeaders.append("Content-Type", "application/json");

    var raw = JSON.stringify({"timeStamp":dayStamp});
    var requestOptions = {
      method: 'POST',
      headers: myHeaders,
      body: raw,
      redirect: 'follow'
    };

    fetch(url, requestOptions)
      .then(response => response.json())
      .then(result => {
        //console.log(result);
        //return parseInt(result.output);
        var dayUsage = parseInt(result.output);
        //console.log(dayUsage);
        addDayUsageData(day,dayUsage);
        
      })
      .catch(error => console.log('error', error));
  }

  async function usageContract(machineID,financierWID,usage,label) {
    var daystamp = label.slice(0,10);
    var monthStamp = label.slice(4,10);
    var timeStamp = machineID+":"+label;
    var dayStamp = machineID+":"+daystamp;
    var monthStamp = machineID+":"+monthStamp;
    usage = parseInt(usage);
    usage = usage.toString();
    //console.log(dayStamp+" "+timeStamp+" "+usage);
    var kld_from = "kld-from="+financierWID;

    var url = "https://u1afypqnup-u1qc0kallb-connect.us1-azure.kaleido.io/instances/machineusage/recordUsage?"+kld_from+"&kld-sync=true";

    var myHeaders = new Headers();
    myHeaders.append("Authorization", "Basic dTFzeDlhMmpkMTppZkdwNFFKS2gtU3RLTlZTR0RZc2xQMHBmZEdMelFJMHhiSXAzNHRzNGQ4");
    myHeaders.append("Content-Type", "application/json");
    var machineIDJSON = JSON.stringify({
      "machineID" : machineID
    })
    var raw = JSON.stringify({
      "dayStamp": dayStamp,
      "monthStamp": monthStamp,
      "timeStamp": timeStamp,
      "usage": usage,
    });
    //console.log("raw "+raw);
    
    var requestOptions = {
      method: 'POST',
      headers: myHeaders,
      body: raw,
      redirect: 'follow'
    };
    
    const response = await fetch(url, requestOptions)
      .then(response => response.text())
      .then(result => {
        
        var temp = result;
        //temp.append(raw);
        //console.log(temp);
        const obj1 = JSON.parse(machineIDJSON)
        const obj2 = JSON.parse(temp);
        const obj3 = JSON.parse(raw);
        const mergedObj = Object.assign(obj1, obj2,obj3);
        //const jsonStr = JSON.stringify(mergedObj);
        //console.log(mergedObj);
        writeTransactionToDB(mergedObj);

      })
      .catch(error => console.log('error', error));
  }

  async function writeTransactionToDB(jsonStr){
    var myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    var raw = JSON.stringify({
      "database": "demoDB",
      "collection": "recordUsage",
      "Document": {
        jsonStr
      }
    });

    var requestOptions = {
      method: 'POST',
      headers: myHeaders,
      body: raw,
      redirect: 'follow'
    };

    fetch("http://localhost:5000/mongodb", requestOptions)
      .then(response => response.text())
      .then(result => console.log(result))
      .catch(error => console.log('error', error));
  }

  function removeFirstData() {
    myChart.data.labels.splice(0, 1);
    myChart.data.datasets.forEach((dataset) => {
      dataset.data.shift();
    });
  }


  async function getDayUsageDataFromDB(machineId,day,time_stamp){
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
    //console.log(dayUsage);
    addDayUsageData(day,dayUsage);
    //return dayUsage;
  
  }
  
  async function addDayUsageData(label, usage) {
    //console.log("addDayUsageData "+label+"::"+usage)
    //console.log(dayUsageChart.data)
  
    var usage = usage/60;
    if (dayUsageChart.data.labels.length > MAX_DAY_USAGE_COUNT) {
      removeFirstDayUsageData();
    }
    dayUsageChart.data.labels.push(label);
    dayUsageChart.data.datasets[0].data.push(usage);
    dayUsageChart.update();
  }
  

  async function populateMetrics(){
    console.log(time_stamp)
    t = time_stamp.slice(0,10);
    hour = parseInt(time_stamp.slice(11,13));
    //console.log(time_stamp);
    
    var from = new Date(t);
    from.setDate(from.getDate()-3);
    hour = (hour+72)%24;
    console.log(from);

    for (var i = 0; i < 48; i++) {
      if(hour < 10){
        hour = "0"+parseInt(hour)+1;
      }
      else if(hour == 23){
        day = from.getDate();
        month = from.getMonth()+1;
        year = from.getFullYear();
        from.setDate(from.getDate()+1);

        if(day<10){
          day = '0'+day;
        }
        if(month<10){
          month = '0'+month;
        }
        time_stamp = year+'-'+month+'-'+day+" "+hour;
      }
      else{
        hour = parseInt(hour)+1;
      }
      time_stamp = time_stamp.slice(0,10)+" "+hour;
      //time_stamp = from.getFullYear()+'-'+(from.getMonth()+1)+'-'+from.getDate()+" "+hour;
      
      max = 100;
      min = 90;
      volt_value = Math.random() * (170 - 160) + 160;
      rotate_value = Math.random() * (420 - 380) + 380;
      vibration_value = Math.random() * (max - min) + min;
      pressure_value = Math.random() * (max - min) + min;
      //console.log("Received sensorData :: " + time_stamp + " :: " + volt_value+" :: " + rotate_value+"::" + vibration_value+"::" + pressure_value);
      if (myChart.data.labels.length > MAX_DATA_COUNT) {
        removeFirstData();
      }
      myChart.data.labels.push(time_stamp);
      myChart.data.datasets[0].data.push(volt_value);
      myChart.data.datasets[1].data.push(rotate_value);
      myChart.data.datasets[2].data.push(vibration_value);
      myChart.data.datasets[3].data.push(pressure_value);
      myChart.update();
      
    }

      //update date
      // var dateYear = parseInt(time_stamp.slice(0,4));
      // var dateMonth = parseInt(time_stamp.slice(5,7));
      // var dateDate = parseInt(time_stamp.slice(8,10));
      // var tempDate = new Date(dateYear,dateMonth-1,dateDate);
      // var nextDate = new Date(tempDate)
      // console.log("next day "+time_stamp);
      // console.log("next day "+nextDate)
      // var hour = parseInt(from.slice(11,13))
      // console.log("hour"+ hour);
      // if(hour == 23){
      //   nextDate.setDate(nextDate.getDate()+1);
      //   hour = '00'
      // }
      // else if (hour<9){
      //   hour = hour + 1;
      //   hour = '0'+hour;
      // }
      // else{
      //   hour = hour+1;
      // }
      // var month = parseInt(nextDate.getMonth())+1;
      // if(month<10)
      // month = "0"+month;
    
      // if(nextDate.getDate()<10)
      //   day = "0"+nextDate.getDate();
      // else
      //   day = nextDate.getDate();
      // var temp = (nextDate.getFullYear()+'-'+month+'-'+day);
  
  
  
      // from = temp+" "+hour;
      // console.log("next day "+from);
      
      //write timestamp to file
      // var updateTimeStampData = {
      //   'time_stamp': time_stamp
      // } 
      // var requestOptions = {
      //   method: "POST",
      //   headers: new Headers({
      //       'Content-Type': 'application/json'
      //   }),
      //   body: JSON.stringify(updateTimeStampData)
      // }
      // fetch('/updateMachineMetricsDate',requestOptions)
      //   .then(response => response.json())
      //   .catch(error => console.log('error', error));
    
  }
  async function populateDayChart(time_stamp,machine_id,userWID){
    console.log("populateDayChart");
    time_stamp = time_stamp.slice(0,10);
    console.log(time_stamp);
    
    var from = new Date(time_stamp);
    from.setDate(from.getDate()-30);
    for(var i=0;i<30;i++){
      
      //console.log(from)
      day = from.getDate();
      month = from.getMonth()+1;
      year = from.getFullYear();
      from.setDate(from.getDate()+1);
  
      if(day<10){
        day = '0'+day;
      }
      if(month<10){
        month = '0'+month;
      }
      time_stamp = machine_id+":"+year+'-'+month+'-'+day;
      day = day+'-'+month+'-'+year;
      dayUsage =Math.random() * (23*60 - 16*60) + 16*60;
      addDayUsageData(day,dayUsage);
      //const result = await getDayUsageDataFromDB(machine_id,day,time_stamp);
    }
  }
}




// async function populateDayChart(time_stamp,machine_id,userWID){
//   console.log("populateDayChart");
//   time_stamp = time_stamp.slice(0,10);
//   console.log(time_stamp);
  
//   var from = new Date(time_stamp);
//   from.setDate(from.getDate()-30);
//   for(var i=0;i<30;i++){
    
//     console.log(from)
//     day = from.getDate();
//     month = from.getMonth()+1;
//     year = from.getFullYear();
//     from.setDate(from.getDate()+1);

//     if(day<10){
//       day = '0'+day;
//     }
//     if(month<10){
//       month = '0'+month;
//     }
//     time_stamp = machine_id+":"+year+'-'+month+'-'+day;
//     day = day+'-'+month+'-'+year;
//     const result = await getDayUsageDataFromDB(machine_id,day,time_stamp);
    
//   }
// }





function appear(){
  console.log("appear");
  document.getElementById("view").style.display = "none";
  const hctx = document.getElementById('hChart');

  let delayed;
  let flagOne = true;
  const hChart = new Chart(hctx, {
    type: 'bar',
    data: {
      labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7', 'Day 8', 'Day 9', 'Day 10', 'Day 11', 'Day 12', 'Day 13', 'Day 14', 'Day 15', 'Day 16', 'Day 17', 'Day 18', 'Day 19', 'Day 20', 'Day 21', 'Day 22', 'Day 23', 'Day 24', 'Day 25', 'Day 26', 'Day 27', 'Day 28', 'Day 29', 'Day 30', 'Day 31'],
      datasets: [{
        label: '# of Hours Used',
        data: [12, 10, 3, 5, 2, 3, 1, 2, 3, 4, 5, 6, 7, 10, 9, 1, 4, 12, 6, 8, 7, 2, 4, 3, 9, 2, 4, 6, 5, 4, 10],
        borderWidth: 1
      }]
    }, 
    options: {
      animation:{
        onComplete: () => {delayed = true
          if(flagOne){
          console.log("animation complete");
          document.getElementById("generateBill").style.display = "block";
          flagOne = false;
          }
        },
        delay: (context) => {
          let delay = 0;
          if (context.type === 'data' && context.mode === 'default' && !delayed) {
            delay = context.dataIndex * 300 + context.datasetIndex * 100;
            console.log(delay);
          }
          return delay;
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });

}


//pie chart
var myPieChart = null
  var config = {
    options:{
          responsive:true,
          rotation: -90,
          circumference: 180,
    },
    type:'pie'}
  function pchart(ftb,mtb) {
      var ftb = ftb,
        mtb = mtb,
        ctx = document.getElementById('pieChart').getContext('2d');
                    config.data = {
        labels: ["Financier","Manufacturer"],
        datasets:
            [{
              data: [ftb,mtb],
              backgroundColor: ["#a64d79", "#3d85c6"],
            }]
      };
      if(myPieChart == null){
                        myPieChart = new Chart(ctx, config);
                    }else{
                        myPieChart.update()
                    }
  }