# Passo 1: ler UIDs da porta serial e imprimir
import serial
import time

PORTA_SERIAL = "COM8"   # <-- ajuste aqui se necessário
BAUDRATE = 9600

def conectar(porta=PORTA_SERIAL, baudrate=BAUDRATE):
    try:
        ar = serial.Serial(porta, baudrate, timeout=1)
        time.sleep(2)  # tempo para o Arduino reiniciar a serial
        print(f"[OK] Conectado em {porta} @ {baudrate}")
        return ar
    except Exception as e:
        print(f"[ERRO] Não conectou: {e}")
        return None

def main():
    ar = conectar()
    if not ar:
        return
    print("Aproxime um cartão... (Ctrl+C para sair)")
    try:
        while True:
            try:
                linha = ar.readline().decode("utf-8", errors="ignore").strip()
                if linha:
                    print(f"UID lido: {linha}")
            except Exception as e:
                print(f"[WARN] Falha leitura: {e}")
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        try:
            ar.close()
        except:
            pass

if __name__ == "__main__":
    main()
