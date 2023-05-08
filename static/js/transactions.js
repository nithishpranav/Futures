async function getTransactions(){
    var getTransaction
    var machineId;
    console.log("machineDetails");
    const response = await fetch('/getInfo')
          .then(response => response.json())
          .then(data => {
              console.log(data);
              machineId = data.machineID;
          });

    var myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");
    

    var raw = JSON.stringify({
    "database": "demoDB",
    "collection": "recordUsage",
    "filter": {
        "machineID": "testMachine10"
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
            console.log(result);     
            var length = result.length;
            console.log(length);

            getTransaction = result;
            console.log(getTransaction[0].jsonStr);
        }
        )
    .catch(error => console.log('error', error));
     

    console.log(getTransaction[0].jsonStr);

    let tableElements = ['blockHash', 'transactionHash',  'timeStamp', 'usage','from','to','headers','gasUsed', 'blockNumber'];


    let tbody = document.getElementById("transactionTableBody");
    getTransaction.forEach((item) => {
        let tr = document.createElement("tr");
        tableElements.forEach((elem) => {
            let td = document.createElement("td");
            //console.log(item.jsonStr[elem])
            if(elem == 'headers'){
                timeReceived = item.jsonStr[elem].timeReceived;
                
                td.innerText = timeReceived;
                td.style = "display:none";                
            }
            else{
                if(elem == 'from' || elem == 'to' || elem == 'gasUsed' || elem == 'blockNumber' ){
                    td.style = "display:none";
                }
                td.innerText = item.jsonStr[elem];
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    

    // let container = document.getElementById("container");
         
    //      // Create the table element
    //      let table = document.createElement("table");
    //      table.className = "table table-striped table-bordered table-hover";
    //      table.id = "transactionTable";
         
    //      // Get the keys (column names) of the first object in the JSON data
    //      // console.log(getTransaction[0].jsonStr);
    //      //let cols = Object.keys(getTransaction[0].jsonStr);
         
    //      // Create the header element
    //      let thead = document.createElement("thead");
    //      let tr = document.createElement("tr");
    //      tr.className = "alert";
    //      tr.role = "alert";
    //      tableElements.forEach((item) => {
    //         console.log(item)
    //         let th = document.createElement("th");
    //         th.innerText = item; 
    //         tr.appendChild(th);
    //         });
    //     thead.appendChild(tr);
    //     table.append(tr)
    //     getTransaction.forEach((item) => {
    //         console.log(item.jsonStr)
    //         let tr = document.createElement("tr");
    //         tableElements.forEach((elem) => {
    //             let td = document.createElement("td");
    //             td.innerText = item.jsonStr[elem];
    //             tr.appendChild(td);
    //         });
    //         table.appendChild(tr);
    //     });
    //     container.appendChild(table)
        document.getElementById("loader").style.display = "none";
        jQuery(document).ready(function($) {
            $('#example').DataTable({
                searching: false,
                responsive: true,
                "autoWidth": false,
            });
            var table = $('#example').DataTable();
            $('#example tbody').on('click', 'tr', function () {
              //console.log(table.row(this).index());
              //console.log(table.row(this).data());
              $(".modal-body div span").text("");
              $(".blockHash span").text(table.row(this).data()[0]); 
              $(".transactionHash span").text(table.row(this).data()[1]); 
              $(".timeStamp span").text(table.row(this).data()[2]); 
              $(".usage span").text(table.row(this).data()[3]); 
              $(".from span").text(table.row(this).data()[4]);
              $(".to span").text(table.row(this).data()[5]);
              $(".timeReceived span").text(table.row(this).data()[6]);
              $(".gasUsed span").text(table.row(this).data()[7]);
              $(".blockNumber span").text(table.row(this).data()[8]);
              $("#transactionModal").modal("show");
              
            });
        } );
        // $('#transactionTable').DataTable({
        //     order: [1, 'asc'],
        //     searching: false,
        //     responsive: true,
        //     "autoWidth": false,
        // });
        // var t = $('#transactionTable').DataTable();
        // $('#transactionTable tbody').on('click', 'tr', function () {
        //     //console.log(table.row(this).data());
        //     $(".modal-body div span").text("");
        //     $(".blockHash span").text(t.row(this).data()[0]);
        //     $(".transactionHash span").text(t.row(this).data()[1]);
        //     $(".timeStamp span").text(t.row(this).data()[2]);
        //     $(".usage span").text(t.row(this).data()[3]);
        
        //     $("#myModal").modal("show");
        // });
}

