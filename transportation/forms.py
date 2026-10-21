from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(max_length=120, widget=forms.TextInput(attrs={'autocomplete': 'name'}))
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={'autocomplete': 'email'}))
    phone = forms.CharField(max_length=40, required=False, widget=forms.TextInput(attrs={'type': 'tel', 'autocomplete': 'tel'}))
    organization = forms.CharField(max_length=160, required=False, widget=forms.TextInput(attrs={'autocomplete': 'organization'}))
    reason = forms.ChoiceField(choices=[
        ('', 'Please select'), ('general', 'General Inquiry'),
        ('facility', 'Facility or Organization'), ('partnership', 'Business Partnership'),
        ('employment', 'Employment'), ('other', 'Other'),
    ])
    message = forms.CharField(max_length=5000, widget=forms.Textarea(attrs={'rows': 6}))
    website = forms.CharField(required=False, max_length=200, widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}))
