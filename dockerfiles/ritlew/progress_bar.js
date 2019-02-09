$(document).ready(function(){
    uuid = $('#progressBar').data('progress_bar_uuid');
    // form submission
    $('form').submit(function(e){
        // Prevent multiple submits
        if ($.data(this, 'submitted')) return false;
        // Append X-Progress-ID uuid form action
        this.action += (this.action.indexOf('?') == -1 ? '?' : '&') + 'X-Progress-ID=' + uuid;
        // Update progress bar
        function update_progress_info() {
            $.getJSON(upload_progress_url, {'X-Progress-ID': uuid}, function(data, status){
                console.log(data);
                if(data){
                    if (data.state != "done"){
                        $('#progressBar').removeAttr('hidden');  // show progress bar if there are datas
                        var progress = parseInt(data.received, 10)/parseInt(data.size, 10)*100;
                        $('#progressBar').attr('value', progress);
                        window.setTimeout(update_progress_info, 200);
                    }
                }
                else {
                    $('#progressBar').attr('hidden', '');  // hide progress bar if no datas
                }
            });
        }
        window.setTimeout(update_progress_info, 200);
        var form = new FormData($("form")[0]);
        $.ajax({
            url: this.action,
            processData: false,
            contentType: false,
            method: "POST",
            data: form,
            success: function(data) {}
        });
        console.log(this.action);
        $.data(this, 'submitted', true); // mark form as submitted.
        e.preventDefault();
    });
});

