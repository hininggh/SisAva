from django import forms
from .models import IndicadorMan

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

class RelatorioForm(forms.ModelForm):
    class Meta:
        model = IndicadorMan
        fields = ['conteudo']
        widgets = {
            'conteudo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'conteudo': 'Arquivo PDF do Relatório',
        }

