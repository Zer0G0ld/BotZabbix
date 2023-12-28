import discord
import requests
import easysnmp

from discord.ext import commands
from discord import Intents

# Configurações do bot
TOKEN = '<SEU_TOKEN_DO_DISCORD>'
ZABBIX_API_TOKEN = '<SEU_TOKEN_DO_ZABBIX>'
ZABBIX_API_BASE_URL = '<SUA_URL_DO_ZABBIX>'
ZABBIX_API_URL = f'{ZABBIX_API_BASE_URL}?{ZABBIX_API_TOKEN}'
ZABBIX_USERNAME = '<SEU_NOME_DE_USUARIO_ZABBIX>'
ZABBIX_PASSWORD = '<SUA_SENHA_ZABBIX>'

intents = Intents.default()
intents.messages = True
intents.message_content = True
description = "Um bot para auxiliar no monitoriamento do zabbix. \n\nQuero mostrar os incidentes, hosts e tudo mais, basta me chamar com o prefixo '!' junto do comando para eu te reponder. \n\nExemplo : '!incidentes'"


bot = commands.Bot(command_prefix="!", intents=intents, description=description)

@bot.event
async def on_ready():
    print(f'Entrei! Me chamo {bot.user.name}')

@bot.event
async def on_message(message):
    print(f"Menssagem Recebida: {message.content} ") # Depuração

    if message.author == bot.user:
        return

    await bot.process_commands(message)

@bot.command(name='incidentes')
async def show_incidents(ctx):
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
    incidents_list = [f"{incident['name']} ({incident['acknowledges'][0]['message']})" for incident in incidents_response.get('result', [])]

    return '\n'.join(incidents_list)

@bot.command(name='snmpwalk')
async def snmpwalk(ctx, ip: str, oid: str):
    try:
        result = perform_snmpwalk(ip, oid)
        await ctx.send(f'SNMP Walk Result:\n{result}')
    except Exception as e:
        await ctx.send(f'Error during SNMP Walk:\n{str(e)}')

def perform_snmpwalk(ip, oid):
    try:
        session = easysnmp.Session(hostname=ip, community='public', version=2)
        result = session.walk(oid)
        return "\n".join([f'{var.oid}: {var.value}' for var in result])
    except Exception as e:
        raise Exception(f"Error in SNMP Walk: {str(e)}")


@bot.command(name='sobre')
async def about(ctx):
    await ctx.send(f"Um bot para auxiliar no monitoriamento do zabbix. \n\nQuero mostra os incidentes, hosts e tudo mais, basta apenas você digitar o prefixo '!' junto do comando para eu te responder.")

bot.run(TOKEN)

