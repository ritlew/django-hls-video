from django import forms

from .models import VideoFile


class UploadModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # bootstrap css on all fields
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                "class": "form-control"
            })
        self.fields["raw_video_file"].widget.attrs.update({
            "class": "form-control-file"
        })
        self.fields["raw_video_file"].required = False

    class Meta:
        model = VideoFile
        exclude = ['task_id', 'thumbnail', 'upload_id', 'processed', 'mpd_file']
        labels = {
            "raw_video_file": "Video File"
        }

