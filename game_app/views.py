from django.forms.models import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView
from django.views.generic import ListView
from django.contrib import messages
from .models import Jogador
from .forms import JogadorCreateForm
from . import perguntas
import random

# Create your views here.
def home(request):
    #Sempre que a home é chamada, a lista de todas as perguntas é recriada e um apelido vazio é criado
    context = {}
    request.session['perguntas_faceis'] = perguntas.easy
    request.session['perguntas_medias'] = perguntas.medium
    request.session['perguntas_dificeis'] = perguntas.hard
    request.session['perguntas_milhao'] = perguntas.million
    request.session['apelido'] = None
    return render(request, 'game_app/home.html', context)

#Criação do objeto jogador
class JogadorCreateView(CreateView):
    model = Jogador
    template_name = "game_app/criar_apelido.html"
    form_class = JogadorCreateForm

    #Caso o form seja válido, cria todas as variáveis necessárias para o início do jogo
    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.pontos = 'R$0,00'
        form.instance.nivel = 0
        self.request.session['apelido'] = form.instance.apelido
        self.request.session['pergunta'] = None
        self.request.session['nivel'] = 1
        self.request.session['n_pulos'] = 3
        self.request.session['segunda_chance'] = True
        self.request.session['segunda_chance_ativada'] = False
        self.request.session['tira_dois'] = True
        return super().form_valid(form)

#Criação do ranking
def ranking_jogador(request):
    context = {}
    ranking = Jogador.objects.all().order_by('-nivel').values()
    context['jogador_list'] = ranking
    return render(request, 'game_app/ranking.html', context)

#Lógica do jogo
def jogo(request):
    #Se não houver nenhum apelido na sessão, o jogo não irá iniciar
    if request.session['apelido'] == None:
        return redirect('/')
    
    #Cria o context e define o nivel atual assim que a janela abre
    context = {}
    context['nivel'] = request.session['nivel']
    context['pontuacao'] = perguntas.pontuacao[request.session['nivel']][request.session['nivel']]
    context['n_pulos'] = request.session['n_pulos']
    context['segunda_chance'] = request.session['segunda_chance']
    context['tira_dois'] = request.session['tira_dois']

    #A cada rodada o nível de pontuação ao parar, perder ou acertar vai aumentando
    if request.session['nivel'] == 1:
        context['pontuacao_perder'] = 'R$0,00'
        context['pontuacao_parar'] = 'R$0,00'
        context['pontuacao_proximo'] = 'R$1.000,00'
    elif request.session['nivel'] == 16:
        context['pontuacao_perder'] = 'R$0,00'
        context['pontuacao_parar'] = 'R$500.000,00'
        context['pontuacao_proximo'] = 'R$1.000.000,00'
    else:
        context['pontuacao_perder'] = perguntas.pontuacao[request.session['nivel']-2][request.session['nivel']-2]
        context['pontuacao_parar'] = perguntas.pontuacao[request.session['nivel']-1][request.session['nivel']-1]
        context['pontuacao_proximo'] = perguntas.pontuacao[request.session['nivel']+1][request.session['nivel']+1]  

    #Mecanica de Parar
    if request.GET.get('parar'):
        jogador_atual = Jogador.objects.get(apelido=request.session['apelido'])
        jogador_atual.pontos = context['pontuacao_parar']
        jogador_atual.nivel = context['nivel']
        jogador_atual.save()
        request.session.flush()
        messages.success(request, "Fim de jogo, você escolheu parar!")
        return redirect('/')   

    #Mecanica de Pular
    #Checa se o usuário escolheu pula, se ele ainda tem pulos disponíveis e se não é a pergunta do milhão:
    if (request.GET.get('pular')) and (request.session['n_pulos'] > 0) and (request.session['nivel'] < 16) :
        #O número de pulos será diminuido e a pergunta será apagada para outra ser selecionada
        request.session['n_pulos'] -= 1
        request.session['pergunta'] = None
        request.session['opcao1'] = None
        request.session['opcao2'] = None
        request.session['opcao3'] = None
        request.session['opcao4'] = None
        request.session['tira1'] = None
        request.session['tira2'] = None
        request.session['resposta'] = None
        return redirect('/jogo')

    #Mecanica de Segunda chance
    #Checa se o usuário escolheu segunda chance, se ele ainda não utilizou antes e se não é a pergunta do milhão
    if (request.GET.get('segundachance')) and (request.session['segunda_chance'] == True) and (request.session['nivel'] < 16):
        #Segunda chance será colocada como False e, caso ele tenha errado a pergunda, aparecerá a mensagem dizendo que errou e a segunda chance utilizada
        request.session['segunda_chance_ativada'] = True
        request.session['segunda_chance'] = False
        return redirect('/jogo') 

    #Tira dois
    #Checa se o usuário escolheu a opção de tirar dois, se ele ainda não utilizou antes e se não é a pergunta do milhão
    if (request.GET.get('tiradois')) and (request.session['tira_dois'] == True) and (request.session['nivel'] < 16):
        #Tira dois será colocada como False e duas opções erradas serão removidas das opções
        request.session['tira_dois'] = False
        request.session[request.session['tira1']] = ''
        request.session[request.session['tira2']] = ''
        return redirect('/jogo')

    #Checa se o usuário respondeu a pergunta sorteada
    if request.GET.get('resposta'):
        #Se ele acertou, e não é a pergunta do milhão, todas as informações armazenadas na sessão são resetadas e ele passa de nível                   
        if (request.GET.get('resposta') == request.session['resposta']) and (request.session['nivel'] < 16):
            request.session['segunda_chance_ativada'] = False
            request.session['nivel'] += 1
            request.session['pergunta'] = None
            request.session['opcao1'] = None
            request.session['opcao2'] = None
            request.session['opcao3'] = None
            request.session['opcao4'] = None
            request.session['tira1'] = None
            request.session['tira2'] = None
            request.session['resposta'] = None
            return redirect('/jogo')
        #Se ele acertou e era a pergunta do milhão, o jogo acaba e uma mensagem de sucesso é enviada para a tela inicial
        if (request.GET.get('resposta') == request.session['resposta']) and (request.session['nivel'] == 16):
            jogador_atual = Jogador.objects.get(apelido=request.session['apelido'])
            jogador_atual.pontos = context['pontuacao_proximo']
            jogador_atual.nivel = context['nivel']
            jogador_atual.save()
            request.session.flush()
            messages.success(request, "Parabéns! Você é o mais novo milionário do Brasil!")
            return redirect('/')   
        #Se ele errou:   
        else:
            #Caso tenha segunda chance, aparecerá a mensagem que ela foi utilizada e o usuário poderá tentar outra opção
            if request.session['segunda_chance_ativada']:
                request.session['segunda_chance_ativada'] = False
                messages.success(request, "Resposta errada, você utilizou sua segunda chance!")
                return redirect('/jogo')
            
            #Caso não tenha segunda chance, acontece o fim de jogo, a pontuação é atribuída e ele volta para a tela inicial com a sessão finalizada  
            else:
                jogador_atual = Jogador.objects.get(apelido=request.session['apelido'])
                jogador_atual.pontos = context['pontuacao_perder']
                jogador_atual.nivel = context['nivel']
                jogador_atual.save()
                request.session.flush()
                messages.success(request, "Fim de jogo, você errou!")
                return redirect('/')   
    #Se não existir nenhuma pergunta salva na sessão (caso seja a primeira pergunta ou o usuário tenha respondido uma pergunta de maneira correta) será sorteada uma pergunta
    if request.session['pergunta'] is None:
        #Será checado em que nível o usuário está, para determinar se será sorteada uma pergunta fácil, média, difícil ou a do milhão
        if request.session['nivel'] <= 5:
            try:
                index = random.choice(range(0, len(request.session['perguntas_faceis']) +1))
                pergunta = request.session['perguntas_faceis'].pop(index)
            except IndexError:
                index -= 8
                pergunta = request.session['perguntas_faceis'].pop(index)
        elif request.session['nivel'] >5 and request.session['nivel'] <= 10:
            try:
                index = random.choice(range(0, len(request.session['perguntas_medias']) +1))
                pergunta = request.session['perguntas_medias'].pop(index)
            except IndexError:
                index -= 8
                pergunta = request.session['perguntas_medias'].pop(index)
        elif request.session['nivel'] > 10 and request.session['nivel'] <=15:
            try:
                index = random.choice(range(0, len(request.session['perguntas_dificeis']) +1))
                pergunta = request.session['perguntas_dificeis'].pop(index)
            except IndexError:
                index -= 8
                pergunta = request.session['perguntas_dificeis'].pop(index)
        else:
            try:
                index = random.choice(range(0, len(request.session['perguntas_milhao']) +1))
                pergunta = request.session['perguntas_milhao'].pop(index)
            except IndexError:
                pergunta = request.session['perguntas_milhao'].pop(index - 1)
        #Após selecionar uma pergunta, armazena a pergunta, cada uma das opções e a resposta na sessão atual
        for key, value in pergunta.items():
            request.session['pergunta'] = key
            request.session['index'] = index
            request.session['opcao1'] = value[0]
            request.session['opcao2'] = value[1]
            request.session['opcao3'] = value[2]
            request.session['opcao4'] = value[3]
            request.session['resposta'] = value[4]
            request.session['tira1'] = value[5]
            request.session['tira2'] = value[6]
        #Envia as informações da sessão para o usuário no template    
            context['pergunta'] = request.session['pergunta']
            context['opcao1'] = request.session['opcao1']
            context['opcao2'] = request.session['opcao2']
            context['opcao3'] = request.session['opcao3']
            context['opcao4'] = request.session['opcao4']
        return render(request, 'game_app/jogo.html', context)
    else:
        #Caso já exista uma pergunta na sessão, envia novamente para o usuário, assim ao atualizar a janela a pergunta não irá mudar
        context['pergunta'] = request.session['pergunta']
        context['opcao1'] = request.session['opcao1']
        context['opcao2'] = request.session['opcao2']
        context['opcao3'] = request.session['opcao3']
        context['opcao4'] = request.session['opcao4']
        context['resposta'] = request.session['resposta']
        return render(request, 'game_app/jogo.html', context)