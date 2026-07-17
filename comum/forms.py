from django import forms
from comum.models import Usuario
from django_select2.forms import Select2Widget


class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = '__all__'
        widgets={
            'status': Select2Widget
        }