let aliveSecond = 0;
let heartbeatRate = 2000;
let myChannel = "johns_sd3a_pi";

let pubnub;

sendEvent('get_user_token')

const setupPubNub = () => {
    // Update this block with your publish/subscribe keys
    pubnub = new PubNub({
        publishKey : "Your publish key",
        subscribeKey : "Your subscribe key",
	uuid:"client"
    });

    // add listener
    const listener = {
        status: (statusEvent) => {
            if (statusEvent.category === "PNConnectedCategory") {
                console.log("Connected to PubNub");
            }
        },
        message: (messageEvent) => {
            if(messageEvent.message.motion){
                document.getElementById("motion_id").innerHTML = messageEvent.message.motion;   
            }
        },
        presence: (presenceEvent) => {
            // handle presence
        }
    };
    pubnub.addListener(listener);

    // subscribe to a channel
    //pubnub.subscribe({
    //    channels: [myChannel]
    //});
};

function publishUpdate(channel, message)
{
    pubnub.publish({
        channel: channel,
        message: message
    });
}

function time()
{
        let d = new Date();
        var currentSecond = d.getTime();
        if(currentSecond - aliveSecond > heartbeatRate + 1000)
        {
                document.getElementById("connection_id").innerHTML="Dead";
        }
        else
        {
                document.getElementById("connection_id").innerHTML="Alive";
        }
        setTimeout('time()', 1000);
}

function keepAlive()
{
        fetch('/keep_alive')
        .then(response=>{
                if(response.ok){
                        let date = new Date();
                        aliveSecond = date.getTime();
                        return response.json();
                }
                throw new Error("Server offline");
        })
        .then(responseJson => {
                if(responseJson.motion == 1){
                        document.getElementById("motion_id").innerHTML = "Motion Detected";
                }
                else{
                        document.getElementById("motion_id").innerHTML = "No Motion Detected";
                }
        })
        .catch(error=>console.log(error));
        setTimeout('keepAlive()', heartbeatRate);
}

function handleClick(cb)
{
	console.log("HandleClick");
        if(cb.checked)
        {
                value = "on";
        }
        else
        {
                value = "off";
        }
	console.log({"buzzer":value})
        publishUpdate(myChannel, {"buzzer": value});
}

function logout()
{
	pubnub.unsubscribe({
		channels: [myChannel]
	})
	location.replace('logout')
}

function grantAccess(ab)
{
	let userId = ab.id.split("-")[2];
	let readState = document.getElementById("read-user-"+userId).checked;
	let writeState = document.getElementById("write-user-"+userId).checked;
	console.log("grant-"+userId+"-"+readState+"-"+writeState);
	sendEvent("grant-"+userId+"-"+readState+"-"+writeState);
}

function grantDeviceAccess(ab)
{
	let uuid = document.getElementById('sensoruuid').value;
	let readState = document.getElementById("read-device").checked;
	let writeState = document.getElementById("write-device").checked;
	console.log("grant-"+uuid+"-"+readState+"-"+writeState);
	sendEvent("grant-"+uuid+"-"+readState+"-"+writeState);
}

function sendEvent(value)
{
	fetch(value,
	{
		method:"POST",
	})
	.then(response => response.json())
	.then(responseJson =>{
		console.log(responseJson);
		if(responseJson.hasOwnProperty('token'))
		{
			pubnub.setToken(responseJson.token);
			//pubnub.setCipherKey(responseJson.cipher_key);
			pubnub.setUUID(responseJson.uuid);
			subscribe();
		}
	});
}

function subscribe()
{
	pubnub.subscribe({channels: [myChannel]},
		function(status, response)
		{
			if(status.error)
			{
				console.log("Subscribe failed ", status)
			}
			else
			{
				console.log("Subscribe success", status)
			}
		}
	);
}
