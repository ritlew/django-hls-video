$(document).ready(function() {
    var first = true;
    /* https://github.com/juliomalegria/django-chunked-upload-demo/blob/master/templates/chunked_upload_demo.html */
    $("#chunked_upload").fileupload({
        url: "/video/api/chunked_upload/",
        dataType: "json",
        replaceFileInput: false,
        maxChunkSize: 1000000, // 1 MB
        add: function (e, data) {
            $("#KILLMENOW").click(function () {
                data.formData = $("form").serializeArray();
                data.submit();
            });
        },
        chunkdone: function (e, data) {
            console.log(data);
            if (first) {
                data.formData.push(
                    {"name": "upload_id", "value": data.result.upload_id}
                );
                first = false;
            }
            var progress = parseInt(data.loaded / data.total * 100.0, 10);
            $("#upload_progress").css("width", progress + "%");
        },
    });
    $("#chunked_upload").submit(function(e){
        e.preventDefault();
    });
});
