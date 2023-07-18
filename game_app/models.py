from django.db import models

# Create your models here.
#Criação da classe jogador
class Jogador(models.Model):
    apelido = models.CharField(max_length=25, unique=True)
    pontos = models.CharField(max_length=15)
    nivel = models.IntegerField()

    def get_absolute_url(self):
        return '/jogo/'
    
    class Meta:
        db_table = 'apelidos'