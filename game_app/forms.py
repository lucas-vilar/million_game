from .models import Jogador
from django import forms

#Criação do Formulário de jogador
class JogadorCreateForm(forms.ModelForm):
    class Meta:
        model = Jogador
        fields = ('apelido',)
        
        error_messages = {
            'apelido' : {
                'unique' : 'Esse apelido já foi inserido, por favor escolha outro.'
            }
        }