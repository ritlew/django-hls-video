from django import forms
from dal import autocomplete

from .models import VideoUpload

TRUE_FALSE_CHOICES = (
    (False, "No"),
    (True, "Yes"),
)

class UploadModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['public'] = forms.ChoiceField(
            choices=TRUE_FALSE_CHOICES
        )

        # bootstrap css on all fields
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

        self.fields['raw_video_file'].widget.attrs.update({
            'class': 'form-control-file'
        })
        self.fields['collections'].widget.attrs.update({
            'data-theme': 'bootstrap',
        })
        self.fields['raw_video_file'].required = False


    class Meta:
        model = VideoUpload
        exclude = ['upload_id']
        labels = {
            'raw_video_file': 'Video File'
        }
        widgets = {
            'collections': autocomplete.ModelSelect2Multiple(url='api_collection_autocomplete')
        }


