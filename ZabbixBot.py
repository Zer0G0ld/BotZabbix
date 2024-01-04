import discord
import requests
import easysnmp
import subprocess

from discord.ext import commands
from discord import Intents

# Configurações do bot
TOKEN = '<SEU_TOKEN_DO_DISCORD>'
ZABBIX_API_TOKEN = 'SEU_TOKEN_DO_ZABBIX'
ZABBIX_API_BASE_URL = 'SUA_URL_DO_ZABBIX'
ZABBIX_API_URL = f'{ZABBIX_API_BASE_URL}?{ZABBIX_API_TOKEN}'
ZABBIX_USERNAME = 'SEU_NOME_DE_USUARIO_ZABBIX'
ZABBIX_PASSWORD = 'SUA_SENHA_ZABBIX'

intents = Intents.default()
intents.messages = True
description = "Um bot para auxiliar no monitoriamento do zabbix. \n\nQuero mostrar os incidentes, hosts e tudo mais, basta me chamar com o prefixo '!' junto do comando para eu te reponder. \n\nExemplo : '!incidentes'"


bot = commands.Bot(command_prefix="!", intents=intents, description=description)

@bot.event
async def on_ready():
    print(f'Tô dentro! Me chamo {bot.user.name}')

@bot.event
async def on_message(message):
    print(f"Menssagem Recebida: {message.content} ") # Depuração

    if message.author == bot.user:
        return

    await bot.process_commands(message)

@bot.command(name='incidentes', help='Mostra os ultimos 5 incidentes.\nCom o comando "!incidentes"')
async def show_incidents(ctx, *args):
    if '-h' in args or '--help' in args:
        await ctx.send('Modo de usar: `!incidentes`')
    incidents = get_zabbix_incidents()
    await ctx.send(f'Incidentes:\n{incidents}')

def get_zabbix_incidents():
    # Autenticação na API do Zabbix
    auth_data = {
        'jsonrpc': '2.0',
        'method': 'user.login',
        'params': {
            'user': ZABBIX_USERNAME,
            'password': ZABBIX_PASSWORD
        },
        'id': 1
    }
    auth_response = requests.post(ZABBIX_API_URL, json=auth_data).json()
    print(auth_response)
    auth_token = auth_response.get('result')

    if not auth_token:
        return 'Falha na autenticação no Zabbix.'

    # Chamada para obter incidentes
    incidents_data = {
        'jsonrpc': '2.0',
        'method': 'event.get',
        'params': {
            'output': 'extend',
            'select_acknowledges': 'extend',
            'sortfield': 'clock',
            'sortorder': 'DESC',
            'limit': 5,  # Ajuste conforme necessário
            'filter': {
                'value': 1
            }
        },
        'auth': auth_token,
        'id': 2
    }

    incidents_response = requests.post(ZABBIX_API_BASE_URL, json=incidents_data).json()
    incidents_list = [f"{incident['name']} ({incident['acknowledges'][0]['message'] if incident['acknowledges'] else 'No acknowledges'})" for incident in incidents_response.get('result', [])]


    return '\n'.join(incidents_list)

#@bot.command(name='snmpwalk')
#async def snmpwalk(ctx, ip: str, oid: str):
#    try:
#       result = perform_snmpwalk(ip, oid)
#       await ctx.send(f'SNMP Walk Result:\n{result}')
#    except Exception as e:
#        await ctx.send(f'Error during SNMP Walk:\n{str(e)}')

#def perform_snmpwalk(ip, oid):Ad
#    try:
#        session = easysnmp.Session(hostname=ip, community='public', version=2)
#        result = session.walk(oid)
#        return "\n".join([f'{var.oid}: {var.value}' for var in result])
#    except Exception as e:
#        raise Exception(f"Error in SNMP Walk: {str(e)}")

#@bot.command(name='snmpwalk')
#async def snmpwalk(ctx, ip: str, oid: str = '.1', *args):
#    try:
#        full_oid = oid + ' '.join(args)
#        result = subprocess.check_output(['snmpwalk', '-v', '2c', '-c', 'public', ip, full_oid], text=True)
#        await ctx.send(f'SNMP Walk Result:\n{result}')
#    except subprocess.CalledProcessError as e:
#        await ctx.send(f'Error during SNMP Walk:\n{e.output}')
#    except Exception as e:
#        await ctx.send(f'Error during SNMP Walk:\n{str(e)}')


def authenticate_zabbix():
    try:
        auth_data = {
            'jsonrpc': '2.0',
            'method': 'user.login',
            'params': {
                'user': ZABBIX_USERNAME,
                'password': ZABBIX_PASSWORD
            },
            'id': 1
        }
        auth_response = requests.post(ZABBIX_API_URL, json=auth_data).json()
        auth_token = auth_response.get('result')
        return auth_token

    except Exception as e:
        print(f'Falha na autenticação no Zabbix:\n{str(e)}')
        return None

@bot.command(name='snmpwalk', help='Comando para buscar OIDs.\nCom o comando "!snmpwalk <ip> <OID_OPCIONAL>"')
async def snmpwalk(ctx, ip: str, oid: str = '.1', *args):
    if '-h' in args or '--help' in args:
        await ctx.send('Modo de usar: `!snmpwalk <IP> <OID_OPCIONAL>`')
        return

    try:
        full_oid = oid + ' '.join(args)
        result = perform_snmpwalk(ip, full_oid)
        await ctx.send(f'SNMP Walk Result:\n{result}')

    except Exception as e:
        await ctx.send(f'Erro durante SNMP Walk:\n{str(e)}')

def perform_snmpwalk(ip, oid):
    try:
        session = easysnmp.Session(hostname=ip, community='public', version=2)
        result = session.walk(oid)
        return "\n".join([f'{var.oid}: {var.value}' for var in result])

    except Exception as e:
        raise Exception(f"Erro durante SNMP Walk: {str(e)}")

@bot.command(name='hosts', help='Mostra o total de hosts, os hosts disponíveis e os indisponíveis.\nCom o comando "!hosts"')
async def hosts(ctx, *args):
    if '-h' in args or '--help'in args:
        await ctx.send('Modo de usar: `!hosts`')
        return

    try:
        auth_token = authenticate_zabbix()
        if not auth_token:
            await ctx.send('Falha na autenticação no Zabbix.')
            return

        hosts_data = {
            'jsonrpc': '2.0',
            'method': 'host.get',
            'params': {
                'output': 'extend',
                'selectGroups': 'extend',
                'selectInterfaces': 'extend'
            },
            'auth': auth_token,
            'id': 2
        }

        hosts_response = requests.post(ZABBIX_API_URL, json=hosts_data).json()
        print(f"Hosts Response: {hosts_response}")
        hosts_total = len(hosts_response.get('result', []))
        hosts_available = sum(1 for host in hosts_response.get('result', []) if host['status'] == '0')
        hosts_unavailable = hosts_total - hosts_available

        await ctx.send(f'Número total de hosts: {hosts_total}\nNúmero de hosts disponíveis: {hosts_available}\nNúmero de hosts indisponíveis: {hosts_unavailable}')

    except Exception as e:
        await ctx.send(f'Erro ao obter informações dos hosts:\n{str(e)}')

@bot.command(name='clear', help='Limpa o chat do apagando todas as conversas ( SEM EXCEÇÃO ).\nCom o comando "!clear"')
async def clear(ctx, *args):
    if '-h' in args or '--help' in args:
        await ctx.send('Modo de usar: `!clear`')
        return

    await ctx.send(f"Limpando mensagens...")
    try:
        async for message in ctx.channel.history(limit=100):
            await message.delete()
    except discord.errors.NotFound:
        await ctx.send(f"Não consigo limpar o chat!")
        pass
    await ctx.send(f"Feito! Chat Limpo!")

@bot.command(name='ping', help='Pinga o IP para saber se está sendo usado ou não.\nCom o comando "!ping <IP>"')
async def ping(ctx, ip: str, *args):
    if '-h' in args or '--help' in args:
        await ctx.send('Modo de usar: `!ping <IP>`')
        return

    try:
        result = subprocess.check_output(['ping', '-c', '5', ip], text=True)
        await ctx.send(f'O resultado do ping para {ip}:\n{result}')
    except subprocess.CalledProcessError as e:
        await ctx.send(f'Erro durente ping:\n{e.output}')

    except Exception as e:
        await ctx.send(f'Erro durente o ping:\n{str(e)}')

@bot.command(name='trigger', help='Comando para criar uma nova trigger')
async def new_trigger(ctx, name_trigger: str, expression: str):
    try:
        auth_token = authenticate_zabbix()
        if not auth_token:
            await ctx.send('Falha na autenticação no Zabbix.')
            return

        # Criar trigger
        trigger_data = {
            'jsonrpc': '2.0',
            'method': 'trigger.create',
            'params': {
                'description': name_trigger,
                'expression': expression,
                'priority': 3,  # Ajuste conforme necessário
                'status': 0,  # 0 para ativar, 1 para desativar
                'type': 0,  # 0 para disparar sempre, 1 para disparar uma vez
            },
            'auth': auth_token,
            'id': 3
        }

        trigger_response = requests.post(ZABBIX_API_URL, json=trigger_data).json()
        print(f"Trigger Response: {trigger_response}")

        await ctx.send(f'Trigger "{name_trigger}" criada com sucesso!')

    except Exception as e:
        await ctx.send(f'Erro ao criar trigger:\n{str(e)}')

@bot.command(name='sobre', help='Uma pequena explicação do é o bot.\nCom o comando "!sobre"')
async def about(ctx):
    await ctx.send("Um bot para auxiliar no monitoramento do Zabbix. \n\nUse os comandos: 'incidentes', 'hosts', 'sobre', 'snmpwalk'. Prefixo: '/'.")


bot.run(TOKEN)

