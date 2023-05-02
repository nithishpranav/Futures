// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

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


    string machineID;
    uint256 day = 0;    // the start of the contract (will be incremented till expiry day)
    uint256 expriryDay;
    uint256 fixedPay;
    uint256 fixedPayPerDay;// fixedPayPerday
    uint256 margin;
    uint256 marginPercentage;
    uint256 totalPool;


    constructor(string memory _machineID, uint256 _expiryDay, uint256 _fixedPay, uint256 _marginPercentage){
        machineID = _machineID;
        expriryDay = _expiryDay;
        fixedPay = _fixedPay;
        marginPercentage = _marginPercentage;
        margin =  (_fixedPay*_marginPercentage)/100;
        fixedPayPerDay = fixedPay/expriryDay;
    }


    event CreateTrade(bytes32 tradeID, address indexed participantA, address indexed participantB);

    function createTrade(address _participantA, address _participantB) public{
        //initialize an empty struct and then update it
        Trade memory trade;

        trade.tradeID = keccak256(abi.encodePacked(machineID,_participantA,_participantB));
        trade.participantA = payable(_participantA);
        trade.participantB = payable(_participantB);
        trade.tradeActive = false;
        trade.participantAMargin = 0;
        trade.participantBMargin = 0;
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
        return (machineID, day, expriryDay, fixedPay, margin, fixedPayPerDay);
    }

    function deposit(bytes32 _tradeID) public payable {
        // Call returns a boolean value indicating success or failure.
        // This is the current recommended method to use.
        address _to = address(this);
        (bool sent, bytes memory data) = _to.call{value: msg.value}("");
        require(sent, "Failed to send Ether");
        checkIfDeposited(msg.sender, msg.value, _tradeID);
    }

    event CheckIfDeposited(address indexed sender, uint256 value, bytes32 tradeID, bool tradeActive);

    function checkIfDeposited(address  sender, uint256 value, bytes32 tradeID) private {
        //this function is called when eth is deposited by a participant
        //it checks how much each participant has deposited

        uint256 index = tradeIndex[tradeID];

        if(sender == trades[index].participantA){
            trades[index].participantAMargin += value;
        }
        else if(sender == trades[index].participantB){
            trades[index].participantBMargin += value;
        }

        if(trades[index].participantAMargin >= margin && trades[index].participantBMargin >= margin){
            trades[index].tradeActive = true;
        }
        emit CheckIfDeposited(sender, value, tradeID, trades[index].tradeActive);
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
//0x20827bccec17a27bb7145171aceb0592e73e496fbe8a2195b3ff6c8c0e056d03
//0xc52000a954b83f72b64c564305b7dbadff7c3c6a9dd5f48c334bcdfa7eea0c3d
//240000000030000000
//240000000030000000
// contract SendEther {
//     function sendViaTransfer(address payable _to) public payable {
//         // This function is no longer recommended for sending Ether.
//         _to.transfer(msg.value);
//     }

//     function sendViaSend(address payable _to) public payable {
//         // Send returns a boolean value indicating success or failure.
//         // This function is not recommended for sending Ether.
//         bool sent = _to.send(msg.value);
//         require(sent, "Failed to send Ether");
//     }

//     function sendViaCall(address payable _to) public payable {
//         // Call returns a boolean value indicating success or failure.
//         // This is the current recommended method to use.
//         (bool sent, bytes memory data) = _to.call{value: msg.value}("");
//         require(sent, "Failed to send Ether");
//     }
// }
