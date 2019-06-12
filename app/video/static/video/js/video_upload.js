upload_id = null;
$(document).ready(function() {
    if (location.protocol === 'https:'){
        UPLOAD_RATE = 1000000
    } else {
        UPLOAD_RATE = 10000000
    }
    $('form :input').prop('disabled', true);
    $('form').hide();
    $('#upload_progress').hide();
    $('#processing_progress').hide();
    var first = true;
    var csrf = $("input[name='csrfmiddlewaretoken']")[0].value;
    /* https://github.com/juliomalegria/django-chunked-upload-demo/blob/master/templates/chunked_upload_demo.html */
    $('form').submit(function(e){
        e.preventDefault();
        if (upload_id){
            form_data = $("form").serializeArray();
            form_data.push({"name": "upload_id", "value": upload_id});
            $.ajax({
                type: "POST",
                data: form_data,
                dataType: "json",
                success: function(data){
                    $('#submit-alerts').html('');
                    $('#submit-alerts').html(`
                        <div class="col-md-12 alert alert-dismissible alert-success">
                            <button type="button" class="close" data-dismiss="alert">&times;</button>
                            <span id="submit-message">
                                <strong>Success!</strong> Video information saved.
                            </span>
                        </div>
                    `);
                },
                failure: function(data){
                    $('#submit-alerts').html('');
                    $('#submit-alerts').html(`
                        <div class="col-md-12 alert alert-dismissible alert-success">
                            <button type="button" class="close" data-dismiss="alert">&times;</button>
                            <span id="submit-message">
                                <strong>An error has occured.</strong>  Please try again later.
                            </span>
                        </div>
                    `);
                    $('#submit-messages').html("");
                }
            });
        }
    });
    $("#raw_video_file").fileupload({
        url: "/video_file_upload/",
        dataType: "json",
        replaceFileInput: false,
        maxChunkSize: UPLOAD_RATE,
        formData: [{"name": "csrfmiddlewaretoken", "value": csrf}],
        add: function (e, data) {
            data.submit();
            $('form').slideDown();
            $('form :input').prop('disabled', false);
        },
        chunkdone: function (e, data) {
            if (first) {
                $('#upload_progress').slideDown();
                first = false;
                upload_id = data.result.upload_id;
                request_data = {"name": "upload_id", "value": upload_id};
                form_data = $("form").serializeArray();
                data.formData.push(request_data);
                form_data.push(request_data);
            }
            var progress = parseInt(data.loaded / data.total * 100.0, 10);	
            if (progress < 100){
                $("#upload_progress_bar").html(`${progress}%`);
                $("#upload_progress_bar").css("width", `${progress}%`);
            } else {
                $("#upload_progress_bar").html(`Upload complete!`);
                $("#upload_progress_bar").css("width", `100%`);
            }
        },
        done: function (e, data) { // Called when the file has completely uploaded
            $.ajax({
                type: "POST",
                url: "/video_file_upload/complete/",
                data: {
                    csrfmiddlewaretoken: csrf,
                    upload_id: data.result.upload_id,
                },
                dataType: "json",
            });
            trackUploadProgress([upload_id], function(data){
                videoData = data.uploads.find(x => x.upload_id == upload_id);
                if (videoData){
                    if (!videoData.processed){
                        if (videoData.progress !== undefined){
                            $('#processing_progress').slideDown();
                            $("#processing_progress_bar").html(`Encoded ${videoData.current}s of ${videoData.total}s`);
                            $("#processing_progress_bar").css("width", `${videoData.progress}%`);
                        }
                    } else {
                        $("#processing_progress_bar").html(`Processing complete!`);
                        $("#processing_progress_bar").css("width", `100%`);
                    }
                }
            }, 500);
        },
    });
});
