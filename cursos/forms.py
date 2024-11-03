from django import forms
from .models import Curso

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nome', 'inscricao', 'detalhes', 'capa']  # Retirado 'informacoes_complementares'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'inscricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'detalhes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'capa': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }
        labels = {
            'nome': 'Nome do Curso',
            'inscricao': 'Inscrição',
            'capa': 'Capa do Curso (PDF)',
        }


class CapaCursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['capa']
        labels = {
            'capa': 'Enviar Capa do Curso',
        }

# Formulário para editar as informações complementares
class InformacoesComplementaresForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['informacoes_complementares']
        widgets = {
            'informacoes_complementares': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        labels = {
            'informacoes_complementares': 'Informações Complementares',
        }
