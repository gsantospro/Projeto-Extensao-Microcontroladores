import json, os, time
import serial

ARQ_FUNC = "funcionarios.json"
PORTA_SERIAL = "COM8"   # <-- ajuste para sua porta
BAUDRATE = 9600

# ---------- Persistência ----------
def carregar_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def salvar_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

# ---------- Serial ----------
def conectar_serial(porta=PORTA_SERIAL, baudrate=BAUDRATE):
    try:
        ar = serial.Serial(porta, baudrate, timeout=1)
        time.sleep(2)  # dá tempo do Arduino resetar a serial
        print(f"[OK] Conectado em {porta} @ {baudrate}")
        return ar
    except Exception as e:
        print(f"[ERRO] Não conectou na serial: {e}")
        return None

def ler_proximo_uid(ar):
    """Bloqueia até ler uma linha não vazia da serial e retorna como UID."""
    print("Aproxime o cartão... (Escaneando UID)")
    while True:
        linha = ar.readline().decode("utf-8", errors="ignore").strip()
        if linha:
            print(f"[LIDO] UID: {linha}")
            return linha

# ---------- Cadastro ----------
def listar(funcs):
    if not funcs:
        print("Nenhum funcionário cadastrado.")
        return
    print("\n=== Funcionários cadastrados ===")
    for uid, nome in funcs.items():
        print(f"- {nome}  (UID: {uid})")

def adicionar_digitando(funcs):
    uid = input("Digite o UID (em HEX, igual aparece no teste): ").strip().upper()
    if not uid:
        print("UID vazio.")
        return
    if uid in funcs:
        print("UID já cadastrado.")
        return
    nome = input("Nome do funcionário: ").strip()
    if not nome:
        print("Nome vazio.")
        return
    funcs[uid] = nome
    salvar_json(ARQ_FUNC, funcs)
    print(f"[OK] Cadastrado: {nome} (UID {uid})")

def adicionar_lendo_serial(funcs):
    ar = conectar_serial()
    if not ar:
        return
    try:
        uid = ler_proximo_uid(ar).upper()
    finally:
        try: ar.close()
        except: pass
    if uid in funcs:
        print("UID já cadastrado.")
        return
    nome = input("Nome do funcionário: ").strip()
    if not nome:
        print("Nome vazio.")
        return
    funcs[uid] = nome
    salvar_json(ARQ_FUNC, funcs)
    print(f"[OK] Cadastrado: {nome} (UID {uid})")

def remover(funcs):
    uid = input("UID a remover: ").strip().upper()
    if uid in funcs:
        nome = funcs.pop(uid)
        salvar_json(ARQ_FUNC, funcs)
        print(f"[OK] Removido: {nome} (UID {uid})")
    else:
        print("UID não encontrado.")

# ---------- Menu ----------
def main():
    funcs = carregar_json(ARQ_FUNC, {})  # {UID: nome}
    while True:
        print("\n=== Cadastro de Funcionários ===")
        print("1) Listar cadastrados")
        print("2) Adicionar (digitando UID)")
        print("3) Adicionar (lendo próximo UID da serial)")
        print("4) Remover")
        print("5) Sair")
        op = input("Opção: ").strip()
        if op == "1":
            listar(funcs)
        elif op == "2":
            adicionar_digitando(funcs)
        elif op == "3":
            adicionar_lendo_serial(funcs)
        elif op == "4":
            remover(funcs)
        elif op == "5":
            print("Saindo...")
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()