// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

contract marginDeposit {





    //The contract will hold the ether
    //There are two participants
    //Participant A - Fixed Payment
    //Participant B - Varibale Payment
    address participantA;
    address participantB;

    address payable participantAPayable;
    address payable participantBPayable;
    


    //boolen to keep track if the participants have made deposit to the contract
    bool participantADeposit = false;
    bool participantBDeposit = false;

    // Function to receive Ether. msg.data must be empty
    receive() external payable {}

    // Fallback function is called when msg.data is not empty
    fallback() external payable {}

    string machineID;
    uint256 day = 0;    // the start of the contract (will be incremented till expiry day)
    uint256 expriryDay;
    uint256 fixedPay;
    uint256 fixedPayPerDay;// fixedPayPerday
    uint256 margin;
    uint256 marginPercentage;
    uint256 totalPool;
    bool marginDeposited;
    
    uint256 marginDepositedByA = 0;
    uint256 marginDepositedByB = 0;
    
    uint256 currentVariableValue = 0;
    uint256 currentFixedValue = 0;




    constructor(string memory _machineID, uint256 _expiriyDay, uint256 _fixedPay, uint256 _marginPercentage,address _participantA, address _participantB){
        machineID = _machineID;
        expriryDay = _expiriyDay;
        fixedPay = _fixedPay;
        marginPercentage = _marginPercentage;
        margin =  (_fixedPay*_marginPercentage)/100;
        fixedPayPerDay = fixedPay/expriryDay;
        participantA = _participantA;
        participantB = _participantB;
        participantAPayable = payable(_participantA);
        participantBPayable = payable(_participantB);

    }


    function getBalance() public view returns (uint) {
        return address(this).balance;
    }

    function getContractDetails() public view returns(string memory, uint256, uint256, uint256, uint256, uint256, address, address ){
        return (machineID, day, expriryDay, fixedPay, margin, fixedPayPerDay, participantA, participantB);
    }

    function deposit() public payable {
        // Call returns a boolean value indicating success or failure.
        // This is the current recommended method to use.
        address _to = address(this);
        (bool sent, bytes memory data) = _to.call{value: msg.value}("");
        require(sent, "Failed to send Ether");

        checkIfDeposited(msg.sender, msg.value);
    }

    function checkIfDeposited(address  sender, uint256 value) private {
        //this function is called when eth is deposited by a participant
        //it checks how much each participant has deposited
        //if a participant has deposited the total margin value, bool value is set true
        if(sender == participantA){
            marginDepositedByA += value;
            totalPool += value;
            if(marginDepositedByA >= margin){
                participantADeposit = true;
            }
        }
        else if(sender == participantB){
            marginDepositedByB += value;
            totalPool += value;
            if(marginDepositedByB >= margin){
                participantBDeposit = true;
            }
        }
    }



    // once both the participants have deposited the margin amount, the contract is activated

    //end of day tracker

    event EODTracker(uint256 currentFixedValue, uint256 currentVariableValue);

    function eodTracker(uint256 hoursUsed, uint256 cost) public payable{
        //the eodTracker must convert the cost from fiat to crypto, but for now we assume the cost is in crypto

        day = day+1;
        currentFixedValue = currentFixedValue + fixedPayPerDay;
        currentVariableValue = currentVariableValue + cost;
        if(currentVariableValue > currentFixedValue){
            if((currentVariableValue-currentFixedValue)>=margin){  
                expiry();
            }
        }
        
        else if(currentVariableValue>currentFixedValue){
            if((currentFixedValue-currentVariableValue)>=margin){
                expiry();
            }
        }
        else if(day == expriryDay){
            expiry();
        }
        emit EODTracker(currentFixedValue, currentVariableValue);
    }


    function transfer() public{

    }

    function exit() public{
        
    }

    function expiry() public{
        uint256 difference;
        uint256 participantAPayout;
        uint256 participantBPayout;
        if(currentFixedValue>currentVariableValue){
            difference = currentFixedValue-currentVariableValue;
            if(difference>totalPool){
                participantAPayout = 0;
                participantBPayout = totalPool;
            }
            participantBPayout = difference;
            participantAPayout = totalPool-difference;
        }
        else{
            difference = currentVariableValue-currentFixedValue;
            if(difference>totalPool){
                participantBPayout = 0;
                participantAPayout = totalPool;
            }
            participantAPayout = difference;
            participantBPayout = totalPool-difference;
        }
        payout(participantAPayable, participantAPayout);
        payout(participantBPayable, participantBPayout);
    }

    function payout(address payable _to, uint256 value) public payable{
        _to.transfer(value);
    }

    function checker() public view returns(uint256, bool, uint256, bool){
        return(marginDepositedByA, participantADeposit, marginDepositedByB, participantBDeposit);
    }
     

}

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
