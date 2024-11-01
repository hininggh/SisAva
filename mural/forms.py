from django import forms
from .models import Mural

class MuralForm(forms.ModelForm):
    class Meta:
        model = Mural
        fields = ['mensagem']
        widgets = {
            'mensagem': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '400', 'placeholder': 'Escreva sua mensagem aqui...'}),
        }

    def clean_mensagem(self):
        mensagem = self.cleaned_data.get('mensagem')
        if len(mensagem) > 400:
            raise forms.ValidationError('A mensagem não pode ter mais de 400 caracteres.')
        return mensagem
