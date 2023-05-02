// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

//symbol = machineID+expiryDate

/*
    functions required
        create trade contract
        receive machine usage
        send machine usage to trades
*/
contract broker{
    // maps the futuresSymbol to the trade contracts assosiated with it
    mapping(string=>address[]) public futuresSymbolMapper;

    function tradeContactMapper(address tradeContractAddress, string memory futuresSymbol) public {
        futuresSymbolMapper[futuresSymbol].push(tradeContractAddress);
    }

    function eventTrigger(string memory futuresSymbol, uint256 value) public {
        for(uint i = 0;i<futuresSymbolMapper[futuresSymbol].length;i++){
            address contractAddress = futuresSymbolMapper[futuresSymbol][i];
            abstractTradeContact(contractAddress).eodTracker(value);
        }
    }

}

interface abstractTradeContact{
    function eodTracker(uint256 cost) external payable;
}

