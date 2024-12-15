from django import forms
from .models import IndicadorMan
from .models import RelatorioPDF

class NSAForm(forms.ModelForm):
    NSA = forms.BooleanField(label="Aplicar NSA", required=False)

    class Meta:
        model = IndicadorMan
        fields = ['NSA']

class NivelSupostoForm(forms.ModelForm):
    nivel_suposto = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        label="Definir Nível Suposto (1 a 5)"
    )

    class Meta:
        model = IndicadorMan
        fields = ['nivel_suposto']

class RelatorioPDFForm(forms.ModelForm):
    class Meta:
        model = RelatorioPDF
        fields = ['arquivo', 'usuario_upload']
        widgets = {
            'arquivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'arquivo': 'Selecione o arquivo PDF',
        }

class DocumentoCompartilhadoForm(forms.ModelForm):
    class Meta:
        model = IndicadorMan
        fields = ['documento_tinymce']
        widgets = {
            'documento_tinymce': forms.Textarea(attrs={'class': 'form-control'}),
        }
        labels = {
            'documento_tinymce': 'Documento Compartilhado',
        }