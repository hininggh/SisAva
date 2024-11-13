from django import forms
from .models import Usuario
from cursos.models import Curso


class UsuarioForm(forms.ModelForm):
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Senha",
        required=False  # Torna a senha opcional para edições
    )
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirmar Senha",
        required=False  # Torna a confirmação da senha opcional para edições
    )

    class Meta:
        model = Usuario
        fields = ['nome', 'email', 'telefone', 'titulacao', 'funcao', 'senha', 'confirmar_senha']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'titulacao': forms.TextInput(attrs={'class': 'form-control'}),
            'funcao': forms.TextInput(attrs={'class': 'form-control'}),
            'data_inicial': forms.DateInput(attrs={
                'class': 'form-control w-100',
                'type': 'date',  # Certifique-se de que este 'type' seja 'date'
                'format': '%Y-%m-%d'  # Adicione o formato explicitamente
            }),
            'data_final': forms.DateInput(attrs={
                'class': 'form-control w-100',
                'type': 'date',
                'format': '%Y-%m-%d'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        # Só valide se as senhas não estiverem vazias
        if senha or confirmar_senha:
            if senha != confirmar_senha:
                self.add_error('confirmar_senha', "As senhas não coincidem.")

        return cleaned_data




class CadastroVisitanteForm(forms.ModelForm):
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Senha",
        required=True
    )
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirmar Senha",
        required=True
    )

    class Meta:
        model = Usuario
        fields = ['nome', 'instituicao', 'data_inicial', 'data_final', 'email']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'instituicao': forms.TextInput(attrs={'class': 'form-control w-100'}),
            'data_inicial': forms.DateInput(attrs={
                'class': 'form-control w-100',
                'type': 'date'
            }),
            'data_final': forms.DateInput(attrs={
                'class': 'form-control w-100',
                'type': 'date'
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control w-100'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Verifique se a data não é None antes de formatar
        if self.instance and self.instance.data_inicial:
            self.fields['data_inicial'].initial = self.instance.data_inicial.strftime('%Y-%m-%d')
        if self.instance and self.instance.data_final:
            self.fields['data_final'].initial = self.instance.data_final.strftime('%Y-%m-%d')


    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        if senha and confirmar_senha and senha != confirmar_senha:
            self.add_error('confirmar_senha', "As senhas não coincidem.")

        return cleaned_data



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