from django import forms

from .models import VideoFile


class UploadModelForm(forms.ModelForm):
    class Meta:
        model = VideoFile
        exclude = ['processed', 'mpd_file']

