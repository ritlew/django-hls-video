from django import forms
from dal import autocomplete

from .models import Video

TRUE_FALSE_CHOICES = (
    (False, "No"),
    (True, "Yes"),
)

class VideoUploadForm(forms.ModelForm):
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

        self.fields['collections'].widget.attrs.update({
            'data-theme': 'bootstrap',
        })

        self.fields['upload_id'].label = ''


    class Meta:
        model = Video
        fields = ['title', 'description', 'collections', 'public', 'upload_id']
        widgets = {
            'collections': autocomplete.ModelSelect2Multiple(url='api_collection_autocomplete'),
            'upload_id': forms.HiddenInput()
        }


