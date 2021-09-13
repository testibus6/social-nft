const nft_vote_address='0x703091392E1BEa715d9F93DaB57DAfA8bB0f45bF'
var tile_size=0
var epoch_px=[[0,0],[0,0]]
async function getAccount() {
    const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
    const account = accounts[0];
    console.log(account)
    document.getElementById("add").value = account;
    validated_address()
}

async function submitTransaction(){
    try {
        const transactionHash = await ethereum.request({
          method: 'eth_sendTransaction',
          params: [
            {
              to: nft_vote_address,
              from: String(document.getElementById("add").value),
              value: web3.utils.numberToHex(web3.utils.toWei(document.getElementById("amount").value))
            },
          ],
        });
        console.log(transactionHash);
      } 
    catch (error) {
        console.error(error);
      }
}

function validated_address(){
    try {
        const address = web3.utils.toChecksumAddress(document.getElementById("add").value)
        result=web3.utils.isAddress(address)
        if(result){
            console.log("verfied address")
            document.getElementById("add").style.color='green'
        }
        else{
            console.log("unverfied address")
            document.getElementById("add").style.color='red'
        }
      } catch(e) { 
        console.error('invalid ethereum address', e.message) 
        document.getElementById("add").style.color='red'
      }
}

async function submitVote() {
    document.getElementById("vote_loader").style.display="inline-block"
    data={}
    px_values=[]
    for (let i = 0; i < tile_size*tile_size; i++) {
        px_values.push(document.getElementById("px_"+String(i)).value)
    }
    data['px']=px_values
    data["address"]=document.getElementById("add").value  
    data["amount"]=document.getElementById("amount").value

    if(data["address"].length==42){
        if(data["amount"] >0){    
            headers = {'Content-Type': 'application/json'};
            
            await fetch('https://us-central1-create-nft.cloudfunctions.net/handle_vote',{
                        method: 'POST',
                        headers: headers,
                        body: JSON.stringify(data),
                    }
            ).then(res => res.text()).then(function(response) {
                console.log(response)
                document.getElementById("vote_loader").style.display="none"
                document.getElementById("vote_result").style.display="block"
                document.getElementById("vote_result_li").style.display="block"
                
                if(response=="okay"){
                    document.getElementById("transaction_details").style.display="block"
                    document.getElementById("sendTransaction").style.display="block"
                    document.getElementById("vote_result").innerHTML="Your vote was successfully registered. Please send the following transaction to validate your vote:"
                    document.getElementById("from_add").innerHTML="From: "+data["address"]
                    document.getElementById("to_add").innerHTML="To: "+nft_vote_address
                    document.getElementById("vote_amount").innerHTML="Amount [ETH]: "+data["amount"]
                }
                else{
                    document.getElementById("vote_result").innerHTML="Following error occured: "+ response+""
                }
            })
        }
        else{
            document.getElementById("vote_result").style.display="block"
            document.getElementById("vote_result").innerHTML="Please check your amount. It seems not to be a positive number"
        }
    }else{
        document.getElementById("vote_result").style.display="block"
        document.getElementById("vote_result").innerHTML="Please check your address. It seems not to be a valid address"
    }
}
function indicate_epoch(epoch){

    pos=0
    // create an offscreen canvas
    var canvas=document.createElement("canvas");
    var ctx=canvas.getContext("2d");

    // size the canvas to your desired image
    canvas.width=tile_size;
    canvas.height=tile_size;

    // get the imageData and pixel array from the canvas
    var imgData=ctx.getImageData(0,0,tile_size,tile_size);
    var data=imgData.data;

    for(var k = 0; k < tile_size * tile_size; k++) {
        if(k<2*tile_size || k>tile_size* tile_size-tile_size*2 || k%tile_size ==0 || k%tile_size ==1 || k%tile_size ==tile_size-1 || k%tile_size ==tile_size-2){
            data[pos  ] = 0;           // some R value [0, 255]
            data[pos+1] = 0;           // some G value
            data[pos+2] = 0;           // some B value
            data[pos+3] = 255;           // set alpha channel
        }
        else{
            data[pos  ] = 255;           // some R value [0, 255]
            data[pos+1] = 255;           // some G value
            data[pos+2] = 255;           // some B value
            data[pos+3] = 255;           // set alpha channel
        }
        pos=pos+4
    }

    // put the modified pixels back on the canvas
    ctx.putImageData(imgData,0,0);

    //ctx.fillText("EP"+String(epoch), 1, 1);
    document.getElementById("tile_img").src =canvas.toDataURL();
    document.getElementById("tile_img").style.left=String(epoch_px[0][0]+"px");
    document.getElementById("tile_img").style.top=String(epoch_px[0][1]+"px");
    //document.getElementById("tile_img").style.width=String(tile_size*2+"px");

}
function onchange_px_value(){
    pos=0
    // create an offscreen canvas
    var canvas=document.createElement("canvas");
    canvas.width=tile_size;
    canvas.height=tile_size;
    var ctx=canvas.getContext("2d");

    // size the canvas to your desired image
    canvas.width=tile_size;
    canvas.height=tile_size;

    // get the imageData and pixel array from the canvas
    var imgData=ctx.getImageData(0,0,tile_size,tile_size);
    var data=imgData.data;
    for(var k = 0; k < tile_size * tile_size; k++) {
            let hex_value=document.getElementById("px_"+String(k)).value
            let rgb_value=hexToRgb(hex_value)
            data[pos  ] = rgb_value["r"];           // some R value [0, 255]
            data[pos+1] = rgb_value["g"];           // some G value
            data[pos+2] = rgb_value["b"];           // some B value
            data[pos+3] = 255;           // set alpha channel
            pos=pos+4
    }
    // put the modified pixels back on the canvas
    ctx.putImageData(imgData,0,0);

    document.getElementById("tile_img").src =canvas.toDataURL();
    document.getElementById("tile_img").style.left=String(epoch_px[0][0]+"px");
    document.getElementById("tile_img").style.top=String(epoch_px[0][1]+"px");
}
function rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
  }
function hexToRgb(hex) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  }

function copyaddress(id) {
    /* Get the text field */
    var copyText = document.getElementById(id);
    /* Select the text field */
    copyText.select();
    copyText.setSelectionRange(0, 99999); /* For mobile devices */    
    /* Copy the text inside the text field */
    document.execCommand("copy");
    document.getElementById("copied").style.color="green"
    setTimeout(function(){ 
        document.getElementById("copied").style.color="black"
        }, 2000);
  }
function check_image(e) {
            let imageFile = document.getElementById("file_id").files[0];
            var reader = new FileReader();
            reader.onload = function (e) {
                var img = document.createElement("img");
                img.crossOrigin = '';
                img.onload = function (event) {
                    // Dynamically create a canvas element
                    var canvas = document.createElement("canvas");
                    canvas.width=tile_size
                    canvas.height=tile_size
                    var ctx = canvas.getContext("2d");

                    // Actual resizing
                    ctx.drawImage(img, 0, 0, tile_size, tile_size);
                   
                    //Update vote-pixel
                    var imgd = ctx.getImageData(0, 0, tile_size, tile_size);
                    var pix = imgd.data;
                    var counter=0                    
                    for (var i = 0, n = pix.length; i < n; i += 4) {
                        document.getElementById("px_"+String(counter)).value=rgbToHex(pix[i  ], pix[i+1], pix[i+2])
                        counter=counter+1
                    }
                    // Show resized image in preview element
                    console.log(tile_size,canvas.width,canvas.height)
                    console.log(img.width,img.height)
                    var dataurl = canvas.toDataURL(imageFile.type);
                    document.getElementById("tile_img").src = dataurl;
                    document.getElementById("tile_img").style.left=String(epoch_px[0][0]+"px");
                    document.getElementById("tile_img").style.top=String(epoch_px[0][1]+"px");
                    document.getElementById("tile_img").style.width=String(tile_size+"px");
                    document.getElementById("tile_img").style.height=String(tile_size+"px");
                }
                img.setAttribute('crossOrigin', '');
                img.src = e.target.result;
            }
            reader.readAsDataURL(imageFile);
}
function create_table(size){
    counter=0
    for (let i = 0; i < size; i++) {
        var tr=document.createElement('tr');
        for (let i = 0; i < size; i++) {
            var td = document.createElement('td');

            var input = document.createElement("input");
            input.type = "color";
            input.value="#e66465";
            input.id="px_"+String(counter)
            
            td.appendChild(input)
            tr.appendChild(td);
            counter=counter+1
        }
        document.getElementById("vote_table").appendChild(tr)
    }
}

function countdown(countDownDate){
    // Update the count down every 1 second
    var x = setInterval(function() {

    // Get today's date and time
    var now = new Date().getTime();

    // Find the distance between now and the count down date
    var distance = countDownDate - now;

    // Time calculations for days, hours, minutes and seconds
    var days = Math.floor(distance / (1000 * 60 * 60 * 24));
    var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = Math.floor((distance % (1000 * 60)) / 1000);

    // Display the result in the element with id="demo"
    document.getElementById("countdown").innerHTML =days + "d " + hours + "h "+ minutes + "m " + seconds + "s ";

    // If the count down is finished, write some text
    if (distance < 0) {
        clearInterval(x);
        document.getElementById("countdown").innerHTML = "EXPIRED";
    }
    }, 1000);
}

async function change_main_network(){
    console.log("Change to ETH-network")
    await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: '0x1' }], // chainId must be in hexadecimal numbers
      }); 
}

async function init(){
    if ((typeof window.ethereum !== 'undefined') || (typeof window.web3 !== 'undefined')){
        web3 = new Web3(web3.currentProvider);
        web3.eth.net.getNetworkType().then(function(network){
            if(network!="main"){
                change_main_network();
            }
        }); 
        window.ethereum.on('chainChanged', function handleChainChanged(_chainId) {
            // We recommend reloading the page, unless you must do otherwise
            window.location.reload();
        });        
        window.ethereum.on('accountsChanged', function (accounts) {
            console.log('accountsChanges',accounts);
            if (accounts.length === 0){console.log('Please connect to MetaMask.');}
            else{
                document.getElementById("add").value = accounts[0];
            }
          });
    } else{
      alert("No Metamask plugin detected. Please install Metamask. Otherwise proceed carefully and manually copy the transaction details")
      document.getElementById("enableEthereumButton").style.display = "none";
      document.getElementById("sendTransaction").style.display = "none";
      web3 = new Web3();
      
    }
    document.getElementById("nft_address").innerHTML=nft_vote_address
    //get current epoch
    await fetch('./epoch.json',{
                method: 'GET'
            }
    ).then(res => res.text()).then(function(data) {
        const data_obj = JSON.parse(data)
        console.log("current epoch: ",data_obj["epoch"])
        if("epoch_"+data_obj["epoch"] in data_obj){
            let end_epoch=data_obj["epoch_"+data_obj["epoch"]]["time"]["end_epoch"]
            epoch_px=data_obj["epoch_"+data_obj["epoch"]]["px"]
            tile_size=epoch_px[1][0]-epoch_px[0][0]+1
            create_table(tile_size)
            indicate_epoch(data_obj["epoch"])
            document.getElementById("vote_creation").innerHTML=data_obj["epoch"]   

            if (data_obj["epoch_"+data_obj["epoch"]]["time"]["start_epoch"] - new Date().getTime() > 0){
            //current epoch has not started yet
                delta_ms=data_obj["epoch_"+data_obj["epoch"]]["time"]["start_epoch"] - new Date().getTime()
                delta_h=Math.round(delta_ms/1000/60/60)
                document.getElementById("vote_creation").innerHTML = "Voting for this period will open in: ~"+delta_h+" hours"
                document.getElementById("countdown").innerHTML = "EXPIRED";
            }
            else if (end_epoch - new Date().getTime() < 0){
            //current epoch has already ended
                next_epoch=1+data_obj["epoch"]
                console.log(next_epoch)
                delta_ms=Math.abs(data_obj["epoch_"+next_epoch]["time"]["start_epoch"] - new Date().getTime())
                delta_h=Math.round(delta_ms/1000/60/60)
                document.getElementById("vote_creation").innerHTML = "Voting for next period will open in: ~"+delta_h+" hours"
                document.getElementById("countdown").innerHTML = "EXPIRED";
            }
            else{
                countdown(end_epoch)
            }
        }
        else{
            document.getElementById("nft_end").style.display = "block"
            document.getElementById("vote_row").style.display = "none";
            document.getElementById("final_nft").innerHTML = "Voted NFT:";
        }
     });
    //get current lead_vote
    await fetch('./lead_vote.json',{
                method: 'GET'
            }
    ).then(res => res.text()).then(function(data) {
        const data_obj = JSON.parse(data);       
        document.getElementById("highestvote").innerHTML=data_obj["amount"]
        document.getElementById("last_update").innerHTML=create_timestamp(data_obj["timestamp"])
        document.getElementById("verfied_votes").innerHTML=data_obj["verfied_votes"]
     })
}

function create_timestamp(timestamp){
    var dateob = new Date(timestamp);
    return dateob.toLocaleString()
}
