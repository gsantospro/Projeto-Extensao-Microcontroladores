import json, os, time
from datetime import datetime
import serial

ARQ_FUNC = "funcionarios.json"  # {UID: nome}
ARQ_REG  = "registros.json"     # {UID: {YYYY-MM-DD: {evento: "HH:MM"}}}

PORTA_SERIAL = "COM8"           # <-- ajuste para sua porta
BAUDRATE = 9600
TIMEOUT = 1

EVENTOS = ["entrada", "saida_intervalo", "volta_intervalo", "saida"]
MIN_GAP_SECONDS = 60            # antiduplo-toque por UID

ultimas_batidas = {}            # {UID: timestamp}

# ---------- utilidades ----------
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

def agora():
    dt = datetime.now()
    return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")

def proximo_evento(dia_dict):
    for ev in EVENTOS:
        if ev not in dia_dict:
            return ev
    return None  # dia completo

# ---------- núcleo ----------
def registrar_batida(uid, funcionarios, registros):
    """Tenta registrar a batida e retorna (ok: bool, info: str)."""
    uid = uid.strip().upper()
    if not uid:
        return False, "UID vazio"

    # antiduplo-toque
    t = time.time()
    if uid in ultimas_batidas and (t - ultimas_batidas[uid]) < MIN_GAP_SECONDS:
        return False, f"Toque repetido em < {MIN_GAP_SECONDS}s"

    ultimas_batidas[uid] = t

    # precisa estar cadastrado
    if uid not in funcionarios:
        return False, "UID não cadastrado"

    data_str, hora_str = agora()
    if uid not in registros:
        registros[uid] = {}
    if data_str not in registros[uid]:
        registros[uid][data_str] = {}

    dia = registros[uid][data_str]
    ev = proximo_evento(dia)
    if ev is None:
        return False, "Dia já completo"

    dia[ev] = hora_str
    salvar_json(ARQ_REG, registros)
    print(f"[OK] {funcionarios[uid]}: {ev.replace('_',' ')} registrada às {hora_str} em {data_str}.")
    return True, ev  # sucesso

def conectar_serial():
    try:
        ar = serial.Serial(PORTA_SERIAL, BAUDRATE, timeout=TIMEOUT)
        time.sleep(2)  # dá tempo do Arduino resetar
        print(f"[SERIAL] Conectado em {PORTA_SERIAL} @ {BAUDRATE}")
        return ar
    except Exception as e:
        print(f"[ERRO] Serial: {e}")
        return None

def main():
    funcionarios = carregar_json(ARQ_FUNC, {})
    registros    = carregar_json(ARQ_REG,  {})

    if not funcionarios:
        print("[AVISO] Nenhum funcionário em funcionarios.json. Rode primeiro o cadastro (cadastro.py).")

    ar = conectar_serial()
    if not ar:
        print("Modo fallback: digite UIDs manualmente (ENTER vazio sai). (Sem LEDs)")
        while True:
            uid = input("UID: ").strip()
            if not uid:
                break
            ok, info = registrar_batida(uid, funcionarios, registros)
            print("OK" if ok else f"ERR: {info}")
        return

    print("Lendo cartões... (Ctrl+C para sair)")
    try:
        while True:
            try:
                linha = ar.readline().decode("utf-8", errors="ignore").strip()
                if not linha:
                    continue

                # tenta registrar
                ok, info = registrar_batida(linha, funcionarios, registros)

                # --- NOVO: responde ao Arduino para acionar LEDs ---
                try:
                    if ok:
                        ar.write(b"OK\n")
                    else:
                        ar.write(b"ERR\n")
                except Exception as ew:
                    print(f"[WARN] Nao consegui enviar ACK para Arduino: {ew}")

                if not ok:
                    # log claro de erro no console
                    print(f"[ERR] UID {linha}: {info}")

            except Exception as e:
                print(f"[WARN] Falha leitura: {e}")
                time.sleep(0.3)
    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        try: ar.close()
        except: pass

if __name__ == "__main__":
    main()
