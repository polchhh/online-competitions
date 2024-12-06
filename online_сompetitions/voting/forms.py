# voting/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .models import Competition, Participant
from django.utils.timezone import now

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

class CompetitionForm(forms.ModelForm):
    class Meta:
        model = Competition
        fields = ['title', 'description', 'start_date', 'end_date', 'voting_type']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'class': 'datetimepicker'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'datetimepicker'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        current_time = now()

        if start_date and start_date < current_time:
            self.add_error('start_date', 'Дата начала не может быть раньше сегодняшней даты.')

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'Дата окончания не может быть раньше даты начала.')

        if start_date and end_date and end_date == start_date:
            self.add_error('end_date', 'Дата окончания не может совпадать с датой начала.')
            self.add_error('start_date', 'Дата начала не может совпадать с датой окончания.')

        if end_date and end_date < current_time:
            self.add_error('end_date', 'Дата окончания не может быть раньше сегодняшней даты.')

        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super(CompetitionForm, self).__init__(*args, **kwargs)
        self.fields['voting_type'].help_text = "Выберите тип голосования: разрешить голосовать только за один вариант или за несколько."
        self.fields['start_date'].help_text = "Выберите дату в формате YYYY-MM-DD HH:MM:SS"
        self.fields['end_date'].help_text = "Выберите дату в формате YYYY-MM-DD HH:MM:SS"

class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['title', 'description']