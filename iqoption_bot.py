
import time
from iqoptionapi.stable_api import IQ_Option
import threading
import talib
import numpy as np

# Indicadores
def indicadores_confluencia(candles):
    close = np.array([c['close'] for c in candles])
    high = np.array([c['max'] for c in candles])
    low = np.array([c['min'] for c in candles])
    open_ = np.array([c['open'] for c in candles])
    volume = np.array([c['volume'] for c in candles])

    sinais = []

    if len(close) < 20:
        return sinais

    if talib.MA(close, timeperiod=10)[-1] > talib.MA(close, timeperiod=20)[-1]:
        sinais.append("MA")

    if talib.RSI(close, timeperiod=14)[-1] < 30:
        sinais.append("RSI")

    macd, macdsignal, macdhist = talib.MACD(close)
    if macd[-1] > macdsignal[-1]:
        sinais.append("MACD")

    slowk, slowd = talib.STOCH(high, low, close)
    if slowk[-1] > slowd[-1]:
        sinais.append("STOCH")

    if talib.CCI(high, low, close, timeperiod=14)[-1] < -100:
        sinais.append("CCI")

    if talib.ATR(high, low, close, timeperiod=14)[-1] > 0:
        sinais.append("ATR")

    if talib.WILLR(high, low, close, timeperiod=14)[-1] < -80:
        sinais.append("WILLR")

    if talib.ADX(high, low, close, timeperiod=14)[-1] > 20:
        sinais.append("ADX")

    if talib.ROC(close, timeperiod=10)[-1] > 0:
        sinais.append("ROC")

    if talib.MOM(close, timeperiod=10)[-1] > 0:
        sinais.append("MOM")

    return sinais

# Bot principal
def iniciar_bot(email, senha, conta_real, valor_entrada):
    print("Conectando...")
    Iq = IQ_Option(email, senha)
    Iq.connect()

    if not Iq.check_connect():
        print("Erro ao conectar")
        return

    print("Conectado com sucesso!")
    tipo_conta = "REAL" if conta_real else "PRACTICE"
    Iq.change_balance(tipo_conta)

    while True:
        pares = Iq.get_all_open_time()["digital"]
        pares_abertos = [p for p, status in pares.items() if status["open"]]

        for par in pares_abertos:
            if "-OTC" in par and not conta_real:
                continue

            Iq.start_candles_stream(par, 60, 60)
            time.sleep(2)
            candles = Iq.get_realtime_candles(par, 60)

            if not candles:
                Iq.stop_candles_stream(par)
                continue

            candles_lista = list(candles.values())
            sinais = indicadores_confluencia(candles_lista)

            if len(sinais) >= 7:
                print(f"Confluência em {par}: {sinais}")
                status, id = Iq.buy_digital_spot(par, valor_entrada, "call", 1)
                if status:
                    print("Entrada realizada. Aguardando resultado...")
                    while True:
                        resultado, lucro = Iq.check_win_digital_v2(id)
                        if resultado:
                            print(f"Resultado: {'Ganho' if lucro > 0 else 'Perda'} | Lucro: {lucro}")
                            break
                    Iq.stop_candles_stream(par)
                    break  # Apenas uma entrada por vez
            Iq.stop_candles_stream(par)

        time.sleep(2)
