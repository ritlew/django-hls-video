from django import forms
from dal import autocomplete

from .models import Video


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # bootstrap css on all fields
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class VideoUploadForm(BootstrapModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['collections'].required = False
        self.fields['collections'].widget.attrs.update({
            'data-theme': 'bootstrap',
        })
        self.fields['tags'].required = False
        self.fields['tags'].widget.attrs.update({
            'data-theme': 'bootstrap',
        })

        self.fields['upload_id'].label = ''

    def save(self, commit=True):
        old_video_title = self.instance.title
        video = super().save(commit=False)

        # if the videos title was the default title
        if Video._meta.get_field('title').get_default() == old_video_title:
            # nullify the slug so it can autopopulate again
            video.slug = None

        if commit:
            video = super().save(commit=True)

        return video


    class Meta:
        model = Video
        fields = ['title', 'description', 'tags', 'collections', 'public', 'upload_id']
        widgets = {
            'tags': autocomplete.ModelSelect2Multiple(url='autocomplete_tag'),
            'collections': autocomplete.ModelSelect2Multiple(url='autocomplete_collection'),
            'upload_id': forms.HiddenInput(),
        }


