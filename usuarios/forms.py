from django import forms
from .models import Usuario
from cursos.models import Curso


class UsuarioForm(forms.ModelForm):
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Senha",
        required=False  # A senha não é obrigatória, a menos que seja alterada
    )
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirmar Senha",
        required=False  # A confirmação da senha também não é obrigatória
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
        }
        labels = {
            'funcao': 'Função',
            'titulacao': 'Titulação'
        }

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        # Realiza a validação apenas se o usuário tiver preenchido a senha
        if senha or confirmar_senha:
            if senha != confirmar_senha:
                self.add_error('confirmar_senha', "As senhas não coincidem.")

            # Verifica a força da senha (exemplo)
            if senha and len(senha) < 8:
                self.add_error('senha', "A senha deve ter pelo menos 8 caracteres.")
            if senha and (not any(char.isdigit() for char in senha) or
                          not any(char.isupper() for char in senha) or
                          not any(char.islower() for char in senha) or
                          not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in senha)):
                self.add_error('senha',
                               "A senha deve incluir letras maiúsculas, minúsculas, números e caracteres especiais.")

        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)

        # Se a senha for fornecida, atualiza a senha
        if self.cleaned_data.get('senha'):
            usuario.set_password(self.cleaned_data['senha'])

        if commit:
            usuario.save()

        return usuario


class CadastroVisitanteForm(forms.ModelForm):
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Senha",
        required=False
    )
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirmar Senha",
        required=False
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
        labels = {
            'instituicao': 'Instituição'
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

        # Verifica se o usuário é novo (não tem um ID) ou se é uma edição
        if not self.instance.pk and not senha:
            self.add_error('senha', "A senha é obrigatória para novos cadastros.")

        # Se a senha for fornecida (mesmo na edição), faça as verificações de força e coincidência
        if senha or confirmar_senha:
            if senha != confirmar_senha:
                self.add_error('confirmar_senha', "As senhas não coincidem.")
            # Verificação de força da senha (exemplo)
            if len(senha) < 8:
                self.add_error('senha', "A senha deve ter pelo menos 8 caracteres.")
            if (not any(char.isdigit() for char in senha) or
                    not any(char.isupper() for char in senha) or
                    not any(char.islower() for char in senha) or
                    not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in senha)):
                self.add_error('senha',
                               "A senha deve incluir letras maiúsculas, minúsculas, números e caracteres especiais.")

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