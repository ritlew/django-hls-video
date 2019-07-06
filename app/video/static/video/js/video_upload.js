function display_message(text, alert_class){
    $('#submit-alerts').html('');
    $('#submit-alerts').html(`
        <div class="col-md-12 alert alert-dismissible alert-${alert_class}">
            <button type="button" class="close" data-dismiss="alert">&times;</button>
            <span id="submit-message">
                ${text}
            </span>
        </div>
    `);
}

$(document).ready(function() {
    /* flag to express whether the first chunk has been uploaded or not */
    var first_chunk_uploaded = false;
    var csrf = $("input[name='csrfmiddlewaretoken']")[0].value;
    var upload_id = null;

    /* hide elements */
    $('form').hide();
    $('form :input').prop('disabled', true);
    $('#upload_progress').hide();
    $('#processing_progress').hide();

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
                    display_message(
                        '<strong>Success!</strong> Video information saved.',
                        'success'
                    );
                },
                failure: function(data){
                    display_message(
                        '<strong>An error has occured.</strong>  Please try again later.',
                        'danger'
                    );
                }
            });
        } else {
            display_message(
                '<strong>An error has occured.</strong>  Please try again later.',
                'danger'
            );
        }
    });

    /* https://github.com/juliomalegria/django-chunked-upload-demo/blob/master/templates/chunked_upload_demo.html */
    $("#raw_video_file").fileupload({
        url: "/video_file_upload/",
        dataType: "json",
        replaceFileInput: false,
        maxChunkSize: 5000000, // 5 MB
        formData: [{"name": "csrfmiddlewaretoken", "value": csrf}],
        add: function (e, data) {
            data.submit();

            /* enable navigation warning */
            $(window).on('beforeunload', function() {
                return "A video upload is in progress. Navigating away will cause the upload to abort.\n\nAre you sure you want to stop uploading?";
            });
        },
        chunkdone: function (e, data) {
            /* update progress bar */
            var progress = parseInt(data.loaded / data.total * 100.0, 10);	
            if (progress < 100){
                $("#upload_progress_bar").html(`${progress}%`);
                $("#upload_progress_bar").css("width", `${progress}%`);
            } else {
                $("#upload_progress_bar").html(`Upload complete!`);
                $("#upload_progress_bar").css("width", `100%`);
            }

            if (!first_chunk_uploaded) {
                first_chunk_uploaded = true;

                /* display form once first chunk is uploaded */
                $('form').slideDown();
                $('form :input').prop('disabled', false);

                /* display upload progress bar */
                $('#upload_progress').slideDown();

                /* save upload_id */
                upload_id = data.result.upload_id;
                /* include upload_id for future chunks (required by django_chunked_upload) */
                data.formData.push({"name": "upload_id", "value": upload_id});
            }
        },
        done: function (e, data) { // Called when the file has completely uploaded
            /* call api for upload done */
            $.ajax({
                type: "POST",
                url: "/video_file_upload/complete/",
                data: {
                    csrfmiddlewaretoken: csrf,
                    upload_id: data.result.upload_id,
                },
                dataType: "json",
            });

            /* disable navigation warning */
            $(window).off('beforeunload');

            /* begin tracking processing progress */
            trackVideoProcessing([upload_id], function(data){
                /* get data for this page's upload */
                video_data = data.uploads.find(x => x.upload_id == upload_id);
                if (video_data){
                    if (!video_data.processed){
                        if (video_data.progress !== undefined){
                            $('#processing_progress').slideDown();
                            $("#processing_progress_bar").html(`Transcoded ${video_data.current}s of ${video_data.total}s`);
                            $("#processing_progress_bar").css("width", `${video_data.progress}%`);
                        }
                        else if (video_data.state === "PENDING"){
                            $('#processing_progress').slideDown();
                            $("#processing_progress_bar").html(`In queue`);
                            $("#processing_progress_bar").css("width", `0%`);
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
