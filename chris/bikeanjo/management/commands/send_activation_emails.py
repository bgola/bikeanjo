# coding: utf-8

from django.core.mail import send_mail
from bikeanjo.models import RegistrationKey
import sys, time
from django.core.management.base import BaseCommand, CommandError

msg = u"""Olá {0},

Estamos te contatando para dizer que o novo sistema está saindo do forno!! 
Para quem não está sabendo do que estamos falando, no final do ano passado nós fizemos um financiamento colaborativo e conseguimos arrecadar recursos para tornar o nosso sistema de atendimento de pedidos de Bike Anjo mais eficiente e automatizado. Vejam aqui a campanha e o resultado: http://bit.ly/apoiebikeanjo

CADASTRAMENTO NO NOVO SISTEMA:
    
Agora, estamos iniciando uma fase de TESTE que envolve o recadastramento de todos os Bike Anjos no novo sistema. Algumas informações nós já conseguimos compilar com base no seu cadastro atual (veja no final deste e-mail), mas gostariamos que você clicasse no link a seguir e complementasse os seus dados para atendimento de pedidos de Bike Anjo.

CADASTRE-SE NO NOVO SISTEMA DO BIKE ANJO: http://sistema.bikeanjo.com.br/activate/{1}

IMPORTANTE: Este link só vale uma vez, portanto só acesse quando estiver com algum tempo disponivel para responder todos os campos do formulário.

Por favor, preencha com o máximo de detalhes possível para que o teste funcione. 
A ideia é que depois de termos todos os Bike Anjos recadastrados, nós comecemos a fazer alguns testes de "pedidos falsos" de Bike Anjo para ver se a tecnologia do sistema está funcionando bem.

Então bora fazer essa nova plataforma do Bike Anjo rodar???

Agradecemos imensamente o apoio de tod@s vocês e estamos felizes de contar com vocês nessa nova fase do Bike Anjo! 0=D

Equipe Bike Anjo
http://bikeanjo.com.br

--

Seus dados:

NOME: {2}
EMAIL: {3}
TELEFONE: {4}
CIDADE: {5}
ESTADO: {6}
"""

class Command(BaseCommand):
    args = ''
    help = 'Sends emails to all non-activated Keys'
    
    def handle(self, *args, **options):
        keys = RegistrationKey.objects.filter(activated=False)
        oks = 0
        falhas = 0
        for key in keys:
            ba = key.user
            sys.stdout.write("%s..." % ba.email)
            profile = ba.get_profile()
            try:
                if send_mail('Cadastro de Bike Anjo no novo sistema! 0=D', msg.format(ba.first_name, key.key, ba.get_full_name(), ba.email, profile.phone, profile.city, profile.state), 'sistema@bikeanjo.com.br', [ba.email]):
                    oks += 1
                    print "OK"
                    key.sent = True
                    key.save()
                else:
                    raise ValueError
            except Exception, e:
                falhas += 1
                print "FAIL: ", e
            if (oks+falhas) % 10 == 0:
                time.sleep(50)
            time.sleep(10)

        print """

        Total:\t %d
        OK:\t %d
        FAIL:\t %d""" % (oks+falhas, oks, falhas)

