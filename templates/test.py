var myHeaders = new Headers();
myHeaders.append("Authorization", "Bearer u0bt01lis8-YaONAPbJ287Vj4FhH06clwCQRse+dPwwKrPhlpuWpkQ=");

var requestOptions = {
  method: 'GET',
  headers: myHeaders,
  redirect: 'follow'
};

fetch("https://console.kaleido.io/api/v1/ledger/u0sdbvxn14/u0anrngbym/addresses/0xa1ff08170e00ebc2086518548128213c3036f545/transactions", requestOptions)
  .then(response => response.text())
  .then(result => console.log(result))
  .catch(error => console.log('error', error));