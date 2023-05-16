// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;


/*


    states
        orderExecuted - true, false
        trade - active, expired
        transfer

    margin call
        the margin call should take place when any of the participants margin is called


    order to trade transition
    A trade is created when two opposing orders are matched


    orderbook



    Queue 
        Two Queues
            Fixed Payment Order    - bool 0
            Variable Payment Order - bool 1




    Functions 
        placeOrder(uint256 orderType)
        transfer(uint256 tradeID, address transferInitiator)
        orderMatching()public returns(bool)
        payoutTransferInitiator(uint256 tradeID, address payable transferInitiator)
        transferTrade (uint256 _tradeID, address _participantA, address _participantB)
        createTrade(address _participantA, address _participantB)
        eodTracker( uint256 cost) public payable
        expiry(uint256 index)
        payout(address payable _to, uint256 value)
        checkIfTradeActive(uint256 tradeID)
        checkOrderStatus(uint256 orderID)
        getContractBalance()
        getContractDetails()
        
    Events
        event CreateTrade(uint256 tradeID, address indexed participantA, address indexed participantB)
        event EODTracker(uint256 currentFixedValue, uint256 currentVariableValue)
        event PayoutTransferInitiator(uint256 tradeID, address transferInitiator);
        event TransferTrade(uint256 tradeID, address indexed _participantA, address _participantB);


    Changes to be made 
        add cancel order feature

    Checks
        during transfer make sure that the trade is still active

*/

contract Futures{

    // Function to receive Ether. msg.data must be empty
    receive() external payable {}
    // Fallback function is called when msg.data is not empty
    fallback() external payable {}

/* 
    ***Symbol Datatypes***
*/
    string futuresSymbol;
    uint256 day = 0;    // the start of the contract (will be incremented till expiry day)
    uint256 expriryDay;
    uint256 fixedPay;
    uint256 fixedPayPerDay;// fixedPayPerday
    uint256 margin;
    uint256 marginPercentage;
/*
    ///Symbols Dataypes///
*/

/*
    ***Order DataTypes*** 
*/
    struct Order{
        uint256 orderID;
        address participant;
        uint256 orderType;
        bool orderExecuted;
        uint256 transferredTradeID;
    }
    Order[] public orders;
    mapping(uint256=>uint256) public orderIndex;
    uint256 orderNumber = 0;
/*
    ///Order DataTypes/// 
*/

/*
    ***Trade DataTypes*** 
*/
    struct Trade{
        uint256 tradeID; //uniquie ID for the trade
        address payable participantA;
        address payable participantB;
        bool tradeActive;
        bool flag; // a flag that is used to calulate/ recalculate the margin when trade is created/transferred
        uint256 currentFixedValue;
        uint256 currentVariableValue;
        uint256 fixedPaymentMarginCall;
        uint256 variablePaymentMarginCall;
        uint256 tradeValue;
    }
    Trade[] public trades;
    mapping(uint256=>uint256) public tradeIndex; // trade index maps the tradeID to the Trades[] array index
    uint256 tradeNumber = 0; 
/*
    ///Trade DataTypes/// 
*/
    constructor(string memory _futuresSymbol, uint256 _expiryDay, uint256 _fixedPay, uint256 _marginPercentage){
        futuresSymbol = _futuresSymbol;
        expriryDay = _expiryDay;
        fixedPay = _fixedPay;
        marginPercentage = _marginPercentage;
        margin =  (_fixedPay*_marginPercentage)/100;
        fixedPayPerDay = fixedPay/expriryDay;
    }
/*
    ***Order Queue***
*/
    mapping (uint256 => uint256) fixedPaymentOrderQueue;
    uint256 fixedPaymentOrderFirst = 1;
    uint256 fixedPaymentOrderLast = 1;

    mapping (uint256 => uint256) variablePaymentOrderQueue;
    uint256 variablePaymentOrderFirst = 1;
    uint256 variablePaymentOrderLast = 1;

    function enqueue(uint256 index, uint256 orderType) public {
        if(orderType == 0){
            fixedPaymentOrderQueue[fixedPaymentOrderLast] = orders[index].orderID;
            ++fixedPaymentOrderLast;

        }
        else{
            variablePaymentOrderQueue[variablePaymentOrderLast] = orders[index].orderID;
            variablePaymentOrderLast = variablePaymentOrderLast + 1;

        }
    }

    function dequeue(uint256 orderType) public returns (address) {
        address participant;
        uint256 index;
        if(orderType == 0 && fixedPaymentOrderLast >= fixedPaymentOrderFirst){
            index = orderIndex[fixedPaymentOrderQueue[fixedPaymentOrderFirst]];
            delete fixedPaymentOrderQueue[fixedPaymentOrderFirst];
            fixedPaymentOrderFirst += 1;
        }
        else if(orderType == 1 && variablePaymentOrderLast >= variablePaymentOrderFirst){
            index = orderIndex[variablePaymentOrderQueue[variablePaymentOrderFirst]];
            delete variablePaymentOrderQueue[variablePaymentOrderFirst];
            variablePaymentOrderFirst += 1;
        }
        //
        participant = orders[index].participant;
        return participant;
    }

    function queueInfo(uint256 orderType, uint256 index) public view returns(uint256){
        if(orderType ==0){
            return fixedPaymentOrderQueue[index];
        }
        else{
            return variablePaymentOrderQueue[index];
        }
    }

    function queueLength(uint256 orderType) public view returns (uint256) {
        if(orderType == 0){
            return fixedPaymentOrderLast-fixedPaymentOrderFirst;
        }
        else{
            return variablePaymentOrderLast - variablePaymentOrderFirst;
        }
    }
/*
    ///Order Queue///
*/

    function placeOrder(uint256 orderType) public payable{
        address _to = address(this);
        (bool sent, bytes memory data) = _to.call{value: msg.value}("");
        require(sent, "Failed to send Ether");
        require(msg.value == margin);

        //create a order stuct 
        orderNumber = orderNumber+1;
        Order memory order;
        order.orderID = orderNumber;
        order.orderType = orderType;
        order.orderExecuted = false;
        order.participant = msg.sender;
        order.transferredTradeID = 0;
        orders.push(order);

        uint256 index = orders.length -1;
        orderIndex[order.orderID] = index;

        enqueue(index,orderType);
    }


    function transfer(uint256 tradeID, address transferInitiator) public{
        uint256 orderType;
        address participant;
        uint256 tIndex = tradeIndex[tradeID];
        if(trades[tIndex].participantA == transferInitiator){
            // initiator order type is orderType = 0;
            orderType = 1;
            participant = trades[tIndex].participantB;
        }
        else{
            orderType = 0;
            participant = trades[tIndex].participantA;
        }
        orderNumber = orderNumber+1;
        Order memory order;
        order.orderID = orderNumber;
        order.orderExecuted = false;
        order.participant = trades[tIndex].participantB;
        order.transferredTradeID = tradeID;
        orders.push(order);
        uint256 index = orders.length -1;
        orderIndex[order.orderID] = index;
        enqueue(index,orderType);      
    }



    event OrderMatching(address indexed fixedParticipant, uint256 fixedOrderID, address indexed variableParticipant, uint256 variableOrderID);

    function orderMatching()public returns(bool){
        uint256 fixedPaymentOrderLength = fixedPaymentOrderLast - fixedPaymentOrderFirst;
        uint256 variablePaymentOrderLength = variablePaymentOrderLast - variablePaymentOrderFirst;
        uint256 fixedIndex = orderIndex[fixedPaymentOrderQueue[fixedPaymentOrderFirst]];
        uint256 variableIndex = orderIndex[variablePaymentOrderQueue[variablePaymentOrderFirst]];
        if(fixedPaymentOrderLength > 0 && variablePaymentOrderLength >0){
            if(orders[fixedIndex].transferredTradeID == 0 && orders[variableIndex].transferredTradeID == 0){
                createTrade(orders[fixedIndex].participant, orders[variableIndex].participant);
                orders[fixedIndex].orderExecuted = true;
                orders[variableIndex].orderExecuted = true;
                dequeue(0);
                dequeue(1);
                fixedPaymentOrderLength -= 1;
                variablePaymentOrderLength -= 1;
            }
            else{
                uint256 tradeID;
                address transferInitiator;
                if(orders[fixedIndex].transferredTradeID > 0){
                    tradeID = orders[fixedIndex].transferredTradeID;
                    transferInitiator = trades[tradeIndex[tradeID]].participantB;
                }   
                else{
                    tradeID = orders[variableIndex].transferredTradeID;
                    transferInitiator = trades[tradeIndex[tradeID]].participantA;
                }
                payoutTransferInitiator(tradeID,payable (transferInitiator));

                transferTrade(tradeID,orders[fixedIndex].participant, orders[variableIndex].participant);

                trades[tradeIndex[tradeID]].flag = true;
                dequeue(0);
                dequeue(1);
                fixedPaymentOrderLength -= 1;
                variablePaymentOrderLength -= 1;
            }
        }
        else{
            return false;
        }

        emit OrderMatching(orders[fixedIndex].participant, orders[fixedIndex].orderID, orders[variableIndex].participant, orders[variableIndex].orderID);
        return true;
    }

    event PayoutTransferInitiator(uint256 tradeID, address transferInitiator);

    function payoutTransferInitiator(uint256 tradeID, address payable transferInitiator)public{
        uint256 index = tradeIndex[tradeID];
        uint256 payoutToTransferInitiator;
        if(trades[index].participantA == transferInitiator){
            //initiator is a fixedPaymentPerson
            payoutToTransferInitiator =  trades[index].fixedPaymentMarginCall - trades[index].currentVariableValue;
        }
        else{
            payoutToTransferInitiator = trades[index].currentVariableValue - trades[index].variablePaymentMarginCall;
        }
       // payout(transferInitiator, payout);
        transferInitiator.transfer(payoutToTransferInitiator);
        //decrease the margin value with the payout
        trades[index].tradeValue = trades[index].tradeValue - payoutToTransferInitiator;

        emit PayoutTransferInitiator(tradeID,transferInitiator);
    }


    event TransferTrade(uint256 tradeID, address indexed _participantA, address _participantB);

    function transferTrade (uint256 _tradeID, address _participantA, address _participantB) public {
        uint256 index = tradeIndex[_tradeID];
        trades[index].participantA = payable(_participantA);
        trades[index].participantB = payable(_participantB);
        trades[index].flag = true;
        trades[index].tradeValue += margin;

        emit TransferTrade(_tradeID, _participantA, _participantB);
    }

    event CreateTrade(uint256 tradeID, address indexed participantA, address indexed participantB);

    function createTrade(address _participantA, address _participantB) public{
        //initialize an empty struct and then update it
        tradeNumber = tradeNumber+1;
        Trade memory trade;

        trade.tradeID = tradeNumber;
        trade.participantA = payable(_participantA);
        trade.participantB = payable(_participantB);
        trade.tradeActive = true;
        trade.flag = true;
        trade.currentFixedValue = 0;
        trade.currentVariableValue = 0;
        trade.fixedPaymentMarginCall = margin;
        trade.variablePaymentMarginCall = 0;
        trade.tradeValue = margin*2;
        trades.push(trade);

        //index to address mapping
        uint256 index = trades.length -1;
        tradeIndex[trade.tradeID] = index;

        emit CreateTrade(trade.tradeID,trade.participantA,trade.participantA);

    }

    /*
        margin expansion 
            margin transfer
                the upper margin (profit for variable is always called when the fixed margin losses are reached
                the lower margin (profit for fixed is called when the variable losses are called 

    */
    event EODTracker(uint256 currentFixedValue, uint256 currentVariableValue);

    function eodTracker( uint256 cost) public payable{
        //the eodTracker must convert the cost from fiat to crypto, but for now we assume the cost is in crypto
        day = day+1;
        //trades[i].fixedPaymentMarginCall += trades[i].fixedPaymentMarginCall + fixedPayPerDay;
        //trades[i].variablePaymentMarginCall += trades[i].variablePaymentMarginCall + fixedPayPerDay;

        //imagine 3 lines 

        for(uint i = 0;i<trades.length;i++){
            //check if trade is active            
            if(trades[i].tradeActive){
                trades[i].currentFixedValue = trades[i].currentFixedValue + fixedPayPerDay;
                trades[i].currentVariableValue = trades[i].currentVariableValue + cost;
                trades[i].fixedPaymentMarginCall += fixedPayPerDay;
                if(trades[i].currentVariableValue >= margin && trades[i].flag == true){
                    trades[i].variablePaymentMarginCall = trades[i].currentVariableValue - margin;
                    trades[i].flag = false;
                }
                else if(trades[i].flag == false){
                    trades[i].variablePaymentMarginCall += fixedPayPerDay;
                }
                if(trades[i].currentVariableValue > trades[i].currentFixedValue){
                    if(trades[i].currentVariableValue >= trades[i].fixedPaymentMarginCall){  
                        expiry(i);
                    }
                }
                else if(trades[i].currentFixedValue > trades[i].currentVariableValue && trades[i].flag == false){
                    if(trades[i].currentVariableValue <= trades[i].variablePaymentMarginCall){
                        expiry(i);
                    }
                }
                else if(day == expriryDay){
                    expiry(i);
                }
                emit EODTracker(trades[i].currentFixedValue, trades[i].currentVariableValue);
            }
        }
    }


// 60000000000000000
// 36000000000000000




    function expiry(uint256 index) public {
        uint256 participantAPayout;
        uint256 participantBPayout;
        uint256 total = trades[index].tradeValue;
        
        //margin called
        if(trades[index].currentVariableValue >= trades[index].fixedPaymentMarginCall){
            participantAPayout = 0;
            participantBPayout = total;
        }
        else if(trades[index].variablePaymentMarginCall >= trades[index].currentVariableValue){
            participantAPayout = total;
            participantBPayout = 0;
        }
        else{
            participantAPayout = trades[index].fixedPaymentMarginCall - trades[index].currentVariableValue;
            participantBPayout = trades[index].currentVariableValue - trades[index].variablePaymentMarginCall;
        }

        payout(trades[index].participantA, participantAPayout);
        payout(trades[index].participantB, participantBPayout);
        trades[index].tradeActive = false;

    }

    function payout(address payable _to, uint256 value) public payable{
        _to.transfer(value);
    }

    function checkIfTradeActive(uint256 tradeID) public view returns( bool){
        uint256 index = tradeIndex[tradeID];
        return( trades[index].tradeActive);
    }
     
    function checkOrderStatus(uint256 orderID) public view returns(bool, uint256 orderType){
        uint256 index = orderIndex[orderID];
        return(orders[index].orderExecuted, orders[index].orderType);
    }

    
    function getContractBalance() public view returns (uint) {
        return address(this).balance;
    }

    function getContractDetails() public view returns(string memory, uint256, uint256, uint256, uint256, uint256){
        return (futuresSymbol, day, expriryDay, fixedPay, margin, fixedPayPerDay);
    }



}
