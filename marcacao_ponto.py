# Importamos bibliotecas
from datetime import datetime, timedelta
import serial  # Para comunicação com Arduino
import time

# Dicionário de funcionários: chave = ID do cartão, valor = nome
funcionarios = {}  # Ex: {'a1b2c3d4': 'João Silva'}

# Dicionário para armazenar dados: {funcionario_id: {data: {horarios}}}
dados_funcionarios = {}  # Ex: {'a1b2c3d4': {'2023-10-15': {'entrada': '08:00', ...}}}

# Estados dos dias por funcionário: {funcionario_id: estado} (0=entrada, 1=saida_intervalo, etc.)
estados = {}  # Ex: {'a1b2c3d4': 0}

# Função para conectar ao Arduino
def conectar_arduino(porta='COM8', baudrate=9600):  # Ajuste a porta
    try:
        arduino = serial.Serial(porta, baudrate, timeout=1)
        time.sleep(2)
        print(f"Conectado ao Arduino na porta {porta}")
        return arduino
    except Exception as e:
        print(f"Erro ao conectar ao Arduino: {e}")
        return None

# Função para adicionar funcionário
def adicionar_funcionario():
    id_cartao = input("Digite o ID do cartão (aproxime o cartão no Arduino para ver o ID): ")
    nome = input("Digite o nome do funcionário: ")
    if id_cartao in funcionarios:
        print("Funcionário já cadastrado!")
        return
    funcionarios[id_cartao] = nome
    dados_funcionarios[id_cartao] = {}  # Inicializa dados vazios
    estados[id_cartao] = 0  # Estado inicial
    print(f"Funcionário {nome} cadastrado com ID {id_cartao}!")

# Função para registrar horário automaticamente (quando cartão é lido)
def registrar_horario_auto(id_cartao):
    if id_cartao not in funcionarios:
        print(f"ID {id_cartao} não cadastrado. Cadastre o funcionário primeiro.")
        return
    
    nome = funcionarios[id_cartao]
    estado = estados.get(id_cartao, 0)
    agora = datetime.now().strftime("%H:%M")
    data_atual = datetime.now().strftime("%Y-%m-%d")  # Usa data atual automaticamente
    
    # Inicializa dados do funcionário se necessário
    if id_cartao not in dados_funcionarios:
        dados_funcionarios[id_cartao] = {}
    if data_atual not in dados_funcionarios[id_cartao]:
        dados_funcionarios[id_cartao][data_atual] = {}
    
    if estado == 0:  # Entrada
        dados_funcionarios[id_cartao][data_atual]['entrada'] = agora
        print(f"Entrada de {nome} registrada: {agora}")
        estados[id_cartao] = 1
    elif estado == 1:  # Saída para intervalo
        dados_funcionarios[id_cartao][data_atual]['saida_intervalo'] = agora
        print(f"Saída para intervalo de {nome} registrada: {agora}")
        estados[id_cartao] = 2
    elif estado == 2:  # Volta do intervalo
        dados_funcionarios[id_cartao][data_atual]['volta_intervalo'] = agora
        print(f"Volta do intervalo de {nome} registrada: {agora}")
        estados[id_cartao] = 3
    elif estado == 3:  # Saída final
        dados_funcionarios[id_cartao][data_atual]['saida'] = agora
        print(f"Saída final de {nome} registrada: {agora}")
        estados[id_cartao] = 4  # Dia completo
        print(f"Dia {data_atual} de {nome} completo!")
    else:
        print(f"Dia de {nome} já completo. Passe o cartão amanhã para novo dia.")

# Função para calcular horas de um dia de um funcionário
def calcular_horas_dia(funcionario_id, data_str):
    if funcionario_id not in dados_funcionarios or data_str not in dados_funcionarios[funcionario_id]:
        return 0
    horarios = dados_funcionarios[funcionario_id][data_str]
    if 'saida' not in horarios:
        return 0
    formato = "%H:%M"
    try:
        entrada_dt = datetime.strptime(horarios['entrada'], formato)
        saida_intervalo_dt = datetime.strptime(horarios['saida_intervalo'], formato)
        volta_intervalo_dt = datetime.strptime(horarios['volta_intervalo'], formato)
        saida_dt = datetime.strptime(horarios['saida'], formato)
        tempo_total = (saida_dt - entrada_dt) - (volta_intervalo_dt - saida_intervalo_dt)
        horas = tempo_total.total_seconds() / 3600
        return max(0, horas)
    except:
        return 0

# Função para gerar relatório total de horas por funcionário
def gerar_relatorio():
    print("\n=== Relatório de Horas Totais ===")
    for id_cartao, nome in funcionarios.items():
        total_horas = 0
        dias = dados_funcionarios.get(id_cartao, {})
        for data in dias:
            total_horas += calcular_horas_dia(id_cartao, data)
        print(f"{nome} (ID: {id_cartao}): {total_horas:.2f} horas totais")
    if not funcionarios:
        print("Nenhum funcionário cadastrado.")

# Conecta ao Arduino
arduino = conectar_arduino()

# Loop principal
while True:
    print("\n=== Sistema de Marcação de Ponto com NFC (Múltiplos Funcionários) ===")
    print("1. Adicionar funcionário")
    print("2. Ver horas de um dia específico de um funcionário")
    print("3. Gerar relatório total de horas por funcionário")
    print("4. Listar funcionários e dados")
    print("5. Sair")
    
    # Verifica cartão lido
    if arduino:
        try:
            linha = arduino.readline().decode('utf-8').strip()
            if linha:
                print(f"Cartão detectado (ID: {linha}). Registrando horário...")
                registrar_horario_auto(linha)
        except:
            pass
    
    opcao = input("Escolha uma opção (1-5): ")
    
    if opcao == '1':
        adicionar_funcionario()
    elif opcao == '2':
        id_cartao = input("Digite o ID do funcionário: ")
        data = input("Digite a data (YYYY-MM-DD): ")
        if id_cartao in funcionarios:
            horas = calcular_horas_dia(id_cartao, data)
            nome = funcionarios[id_cartao]
            print(f"Horas de {nome} em {data}: {horas:.2f} horas")
        else:
            print("Funcionário não encontrado.")
    elif opcao == '3':
        gerar_relatorio()
    elif opcao == '4':
        print("Funcionários:")
        for id_cartao, nome in funcionarios.items():
            print(f"  {nome} (ID: {id_cartao})")
            if id_cartao in dados_funcionarios:
                for data, horarios in dados_funcionarios[id_cartao].items():
                    print(f"    {data}: {horarios}")
    elif opcao == '5':
        if arduino:
            arduino.close()
        print("Saindo...")
        break
    else:
        print("Opção inválida!")
