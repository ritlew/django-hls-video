function trackVideoProcessing(upload_ids, callback, query_rate){
    /* determine websocket protocol */
    /* https://stackoverflow.com/questions/414809/how-do-i-determine-whether-a-page-is-secure-via-javascript */
    if (location.protocol === 'https:'){
        WEBSOCKET_PROTOCOL = 'wss://'
    } else {
        WEBSOCKET_PROTOCOL = 'ws://'
    }

    proSocket = new WebSocket(WEBSOCKET_PROTOCOL + window.location.host + "/ws/upload_progress/");

    /* interval for periodic read from websocket */
    intervalID = setInterval(function(){
        if (proSocket.readyState == 1){
            /* ping the endpoint for data */
            proSocket.send(JSON.stringify({'upload_ids': upload_ids}));
        }
    }, query_rate);

    proSocket.onmessage = function(e){
        callback($.parseJSON(e.data));
    };
}

