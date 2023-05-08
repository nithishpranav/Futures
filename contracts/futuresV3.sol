// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;


/*
    Queue 
        Two Queues
            Fixed Payment Order    - bool 0
            Variable Payment Order - bool 1

    participateInTrade
    orderMatching
    createTrade
    eodTracker

*/

contract Futures{

    // Function to receive Ether. msg.data must be empty
    receive() external payable {}

    // Fallback function is called when msg.data is not empty
    fallback() external payable {}

    struct Trade{
        bytes32 tradeID; //uniquie ID for the trade
        address payable participantA;
        address payable participantB;
        bool tradeActive;
        uint256 participantAMargin;
        uint256 participantBMargin;
        uint256 currentFixedValue;
        uint256 currentVariableValue;
    }

    Trade[] public trades;

    mapping(bytes32=>uint256) public tradeIndex;

    string futuresSymbol;
    uint256 day = 0;    // the start of the contract (will be incremented till expiry day)
    uint256 expriryDay;
    uint256 fixedPay;
    uint256 fixedPayPerDay;// fixedPayPerday
    uint256 margin;
    uint256 marginPercentage;
    uint256 totalPool;

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
    mapping (uint256 => address) fixedPaymentOrderQueue;
    uint256 fixedPaymentOrderFirst = 1;
    uint256 fixedPaymentOrderLast = 1;

    mapping (uint256 => address) variablePaymentOrderQueue;
    uint256 variablePaymentOrderFirst = 1;
    uint256 variablePaymentOrderLast = 1;

    function enqueue(address participant, uint256 orderType) public {
        if(orderType == 0){
            fixedPaymentOrderLast += 1;
            fixedPaymentOrderQueue[fixedPaymentOrderLast] = participant;
        }
        else{
            variablePaymentOrderLast += 1;
            variablePaymentOrderQueue[variablePaymentOrderLast] = participant;
        }
    }

    function dequeue(uint256 orderType) public returns (address) {
        address participant;
        if(orderType == 0 && fixedPaymentOrderLast >= fixedPaymentOrderFirst){
            participant = fixedPaymentOrderQueue[fixedPaymentOrderFirst];
            delete fixedPaymentOrderQueue[fixedPaymentOrderFirst];
            fixedPaymentOrderFirst += 1;
        }
        else if(orderType == 1 && variablePaymentOrderLast >= variablePaymentOrderFirst){
            participant = variablePaymentOrderQueue[variablePaymentOrderFirst];
            delete variablePaymentOrderQueue[variablePaymentOrderFirst];
            variablePaymentOrderFirst += 1;
        }
        return participant;
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


    /*
        ***Transfer Queue***
    */


    /*

    */

    function participateInTrade(uint256 orderType) public payable{
        address _to = address(this);
        (bool sent, bytes memory data) = _to.call{value: msg.value}("");
        require(sent, "Failed to send Ether");
        require(msg.value == margin);
        enqueue(msg.sender,orderType);
        orderMatching();        
    }

    function orderMatching()public {
        uint256 fixedPaymentOrderLength = fixedPaymentOrderLast - fixedPaymentOrderFirst;
        uint256 variablePaymentOrderLength = variablePaymentOrderLast - variablePaymentOrderFirst;

        while(fixedPaymentOrderLength > 0 && variablePaymentOrderLength >0){
            createTrade(fixedPaymentOrderQueue[fixedPaymentOrderFirst], variablePaymentOrderQueue[variablePaymentOrderFirst]);
            dequeue(0);
            dequeue(1);
            fixedPaymentOrderLength -= 1;
            variablePaymentOrderLength -= 1;
        }
    }


    event CreateTrade(bytes32 tradeID, address indexed participantA, address indexed participantB);

    function createTrade(address _participantA, address _participantB) public{
        //initialize an empty struct and then update it
        Trade memory trade;

        trade.tradeID = keccak256(abi.encodePacked(futuresSymbol,_participantA,_participantB));
        trade.participantA = payable(_participantA);
        trade.participantB = payable(_participantB);
        trade.tradeActive = true;
        trade.participantAMargin = margin;
        trade.participantBMargin = margin;
        trade.currentFixedValue = 0;
        trade.currentVariableValue = 0;

        trades.push(trade);

        //index to address mapping
        uint256 index = trades.length -1;
        tradeIndex[trade.tradeID] = index;

        emit CreateTrade(trade.tradeID,trade.participantA,trade.participantA);

    }

    function getContractBalance() public view returns (uint) {
        return address(this).balance;
    }

    function getContractDetails() public view returns(string memory, uint256, uint256, uint256, uint256, uint256){
        return (futuresSymbol, day, expriryDay, fixedPay, margin, fixedPayPerDay);
    }


    // once both the participants have deposited the margin amount, the contract is activated

    //end of day tracker

    event EODTracker(uint256 currentFixedValue, uint256 currentVariableValue);

    function eodTracker( uint256 cost) public payable{
        //the eodTracker must convert the cost from fiat to crypto, but for now we assume the cost is in crypto
        day = day+1;

        for(uint i = 0;i<trades.length;i++){
            //check if participants have deposited the margin
            if(trades[i].tradeActive){
                trades[i].currentFixedValue = trades[i].currentFixedValue + fixedPayPerDay;
                trades[i].currentVariableValue = trades[i].currentVariableValue + cost;
            }
            if(trades[i].currentVariableValue > trades[i].currentFixedValue){
                if((trades[i].currentVariableValue - trades[i].currentFixedValue)>=margin){  
                    expiry(i);
                }
            }
            else if(trades[i].currentVariableValue > trades[i].currentFixedValue){
                if((trades[i].currentFixedValue- trades[i].currentVariableValue)>=margin){
                    expiry(i);
                }
            }
            else if(day == expriryDay){
                expiry(i);
            }
            emit EODTracker(trades[i].currentFixedValue, trades[i].currentVariableValue);
        }
    }


    function transfer() public{
        //
    }

    function exit() public{
        
    }

    function expiry(uint256 index) public {
        uint256 difference;
        uint256 participantAPayout;
        uint256 participantBPayout;
        
        if(trades[index].currentFixedValue > trades[index].currentVariableValue){
            difference = trades[index].currentFixedValue - trades[index].currentVariableValue;
            if(difference>margin){
                participantAPayout = 0;
                participantBPayout = margin*2;
            }
            else{
                participantBPayout = difference;
                participantAPayout = (margin*2)-difference;
            }
        }
        else{
            difference = trades[index].currentVariableValue - trades[index].currentFixedValue;
            if(difference>margin){
                participantBPayout = 0;
                participantAPayout = margin*2;
            }
            else{
                participantAPayout = difference;
                participantBPayout = (margin*2)-difference;
            }
        }
        payout(trades[index].participantA, participantAPayout);
        payout(trades[index].participantB, participantBPayout);
        trades[index].tradeActive = false;

    }

    function payout(address payable _to, uint256 value) public payable{
        _to.transfer(value);
    }

    function checker(bytes32 tradeID) public view returns(uint256, uint256, bool){
        uint256 index = tradeIndex[tradeID];
        return(trades[index].participantAMargin, trades[index].participantBMargin, trades[index].tradeActive);
    }
     

}
