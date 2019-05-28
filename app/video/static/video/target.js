var proSocket = null;
var intervalID = null;
var upload_id = null;
$(document).ready(function() {
    var first = true;
    var csrf = $("input[name='csrfmiddlewaretoken']")[0].value;
    /* https://github.com/juliomalegria/django-chunked-upload-demo/blob/master/templates/chunked_upload_demo.html */
    $("#chunked_upload").fileupload({
        url: "/api/chunked_upload/",
        dataType: "json",
        replaceFileInput: false,
        maxChunkSize: 1000000, // 1 MB
        formData: [{"name": "csrfmiddlewaretoken", "value": csrf}],
        add: function (e, data) {
            $("#KILLMENOW").click(function () {
                data.submit();
                $(this).attr("disabled", "disabled");
            });
        },
        chunkdone: function (e, data) {
            if (first) {
                form_data = $("form").serializeArray();
                upload_id = data.result.upload_id;
                request_data = {"name": "upload_id", "value": data.result.upload_id};
                data.formData.push(request_data);
                form_data.push(request_data);
                $.ajax({
                    type: "POST",
                    data: form_data,
                    dataType: "json",
                    success: function(a) {
                        console.log(a);
                    }
                });
                first = false;
            }
            var progress = parseInt(data.loaded / data.total * 100.0, 10);
            $("#upload_progress").css("width", progress + "%");
        },
        done: function (e, data) { // Called when the file has completely uploaded
            $.ajax({
                type: "POST",
                url: "/api/chunked_upload_complete/",
                data: {
                    csrfmiddlewaretoken: csrf,
                    upload_id: data.result.upload_id,
                },
                dataType: "json",
                success: function(data) {
                    proSocket = new WebSocket(WEBSOCKET_PROTOCOL + window.location.host + "/ws/test/");
                    proSocket.onmessage = function(e){
                        console.log(e.data);
                        data = $.parseJSON(e.data);
                        $("#processing_progress").html("Encoded " + data.current + "s of " + data.total + "s");
                        $("#processing_progress").css("width", data.progress + "%");
                        if (data.progress >= 100 || proSocket.readyState != 1){
                            $("#processing_progress").html("Processing completed");
                            $("#processing_progress").css("width", "100%");
                            clearInterval(intervalID);
                        }
                    };
                    intervalID = setInterval(function(){
                        if (proSocket.readyState == 1){
                            proSocket.send(JSON.stringify({"upload_id": upload_id}));
                        }
                    }, 500);
                }
            });
        },
    });
    $("#chunked_upload").submit(function(e){
        e.preventDefault();
    });
});
