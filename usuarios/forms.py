from django import forms
from .models import Usuario
from cursos.models import Curso


class UsuarioForm(forms.ModelForm):
    senha = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Senha")

    class Meta:
        model = Usuario
        fields = ['nome', 'email', 'telefone', 'titulacao', 'instituicao', 'senha']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'titulacao': forms.TextInput(attrs={'class': 'form-control'}),
            'instituicao': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(UsuarioForm, self).__init__(*args, **kwargs)
        if self.instance.tipo == 'visitante':
            self.fields.pop('titulacao')
        else:
            self.fields.pop('instituicao')


class CadastroVisitanteForm(forms.ModelForm):
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Senha",
        required=False  # Tornar opcional para permitir a edição sem redefinir a senha
    )

    class Meta:
        model = Usuario
        fields = ['nome', 'instituicao', 'data_inicial', 'data_final', 'email']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'instituicao': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'data_inicial': forms.DateInput(attrs={'class': 'form-control w-100', 'type': 'date'}),
            'data_final': forms.DateInput(attrs={'class': 'form-control w-100', 'type': 'date'}),
            'email': forms.EmailInput(attrs={'class': 'form-control w-100'}),
        }



class AdicionarCursosForm(forms.ModelForm):
    cursos_acesso = forms.ModelMultipleChoiceField(
        queryset=Curso.objects.none(),  # Será configurado na view
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Cursos com Acesso"
    )

    class Meta:
        model = Usuario
        fields = ['cursos_acesso']