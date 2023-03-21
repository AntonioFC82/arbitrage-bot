import pyRofex
import pandas as pd
from math import floor
import time
import config_veta

"""
Estrategia de arbitraje (por niveles):
    * IDA: Corresponde a la operación de Venta del Bono1 y la Compra del Bono2.
    * VUELTA: Corresponde a la operación de Venta del Bono2 y la Compra del Bono1.
Las operaciones de IDA se ejecutan cuando el ratio medio está por encima de un determinado valor (Nivel 2, Nivel Ratio, Nivel 3 y Nivel 4),
el cual se setea a elección en puntos porcentuales (variable 'std').
Las operaciones de VUELTA se ejecutan cuando se haya cumplido la operación de IDA y el ratio medio está por debajo
de un determinado valor (Nivel 3, Nivel Ratio, Nivel 2, Nivel 1), los cualea quedan determinados al setear la variable 'std'.
"""

# Set environment:
pyRofex._set_environment_parameter("url", "https://api.veta.xoms.com.ar/", pyRofex.Environment.LIVE)
pyRofex._set_environment_parameter("ws", "wss://api.veta.xoms.com.ar/", pyRofex.Environment.LIVE)


# Defines variables.
### ******** PRUEBAS ******** ###
# bono1 = "MERV - XMEV - AL30 - 48hs"
# bono2 = "MERV - XMEV - AY24 - 48hs"
#     # Ratio medio del par elegido (bono1/bono2)
# ratio = 1.012
#     # Distancia entre niveles (expresado en %):
# std = 0.25
#     # Cantidad de nominales para la venta inicial
# sell_size = 50

#---------------------------------------------------------------------------------

### ******** AL30 vs GD30 ******** ###
    # Par de bonos a arbitrar:
bono1 = "MERV - XMEV - AL30 - 48hs"
bono2 = "MERV - XMEV - GD30 - 48hs"
    # Ratio medio del par elegido (bono1/bono2)
ratio = 0.925
    # Desvío desde el ratio medio a partir del cual se inician las operaciones:
std = 0.15 # expresado en %
    # Cantidad de nominales para la venta inicial
sell_size = 4000

#---------------------------------------------------------------------------------
# ### ******** GD35 vs AL35 ******** ###
#     # Par de bonos a arbitrar:
# bono1 = "MERV - XMEV - GD35 - 48hs"
# bono2 = "MERV - XMEV - AL35 - 48hs"
#     # Ratio medio del par elegido (bono1/bono2)
# ratio = 1.03
#     # Desvío desde el ratio medio a partir del cual se inician las operaciones:
# std = 0.2 # expresado en %
#     # Cantidad de niveles o etapas en los que se desarrollará la estrategia:
# #niveles = 4 # (2 por encima del ratio medio y 2 por debajo)
#     # Cantidad de nominales para la venta inicial
# sell_size = 100


    # Definir si se acumulan nominales (acumNom=True) o no:
acumNom = True
    # Otras variables del código (no modificar)
data = [(0, 0, 0, 0), (0, 0, 0, 0)]
tickers = [bono1, bono2]
bid_offers = pd.DataFrame(data, columns=["bidSize", "Bid", "Offer", "offerSize"], index=tickers)
my_order = dict()
order_rep = dict()
last_md = None


# Initialize the environment.
    # Entorno de prueba:
# pyRofex.initialize(user="******",
#                    password="****",
#                    account="******",
#                    environment=pyRofex.Environment.REMARKET)

    # Entorno real:
pyRofex.initialize(config_veta.user,
                   config_veta.password,
                   config_veta.account,
                   environment=pyRofex.Environment.LIVE)


# Defines the handlers that will process the messages:
def market_data_handler(message):
    #global bid_offers
    #print(f"\nProcessing Market Data Message Received: \n {message} \n")
    bid_offers.loc[bid_offers.index == message["instrumentId"]["symbol"], 'Offer'] = message["marketData"]["OF"][0]["price"]
    bid_offers.loc[bid_offers.index == message["instrumentId"]["symbol"],'offerSize'] = message ["marketData"]["OF"][0]["size"]
    bid_offers.loc[bid_offers.index == message["instrumentId"]["symbol"], 'Bid'] = message["marketData"]["BI"][0]["price"]
    bid_offers.loc[bid_offers.index == message["instrumentId"]["symbol"],'bidSize'] = message ["marketData"]["BI"][0]["size"]
    print("\n", bid_offers, "\n")


# Defines the handlers that will process the Order Reports:
def order_report_handler(order_report):
    global order_rep
    order_rep = order_report#['orderReport']
    #order_rep = order_report#['orderReport']
    #print(f"Order Report Message Received: \n{order_report}")


# Initialize Websocket Connection with the handler:
pyRofex.init_websocket_connection(market_data_handler=market_data_handler,
                                  order_report_handler=order_report_handler)


# Subscribes for Market Data:
pyRofex.market_data_subscription(tickers=[bono1, bono2],
                                 entries=[pyRofex.MarketDataEntry.BIDS,
                                          pyRofex.MarketDataEntry.OFFERS])


# Subscribes to receive order report for the default account:
pyRofex.order_report_subscription()


# Defines order to send to Market:
def send_order(bono, side, px, size):
    order = pyRofex.send_order(
                                ticker=bono,
                                side=side,
                                size=size,
                                price=px,
                                order_type=pyRofex.OrderType.LIMIT,
                                cancel_previous=True
    )
    my_order[order["order"]["clientId"]] = None
    print("\n***Sending %s order %s@%s@%s - id: %s \n" % (bono, side, size, px, order["order"]["clientId"]))


def opeIda():
    print(f"\nPaso1---------VENTA {bono1}----------")
    send_order(bono1, pyRofex.Side.SELL, bid1_px, sell_size)
    venta1 = 0
    time.sleep(0.1)
    if order_rep["orderReport"]["clOrdId"] in my_order.keys():
        while True:
            if order_rep["orderReport"]["status"] in ("NEW", "PARTIALLY_FILLED"):
                print("***Processing New Order - PASO1*** \n")
                my_order[order_rep["orderReport"]["clOrdId"]] = order_rep
            if order_rep["orderReport"]["status"] == "FILLED":
                print("***Operation 1/4 Filled - Initiating Operation 2/4***")
                venta1 = 1
                del my_order[order_rep["orderReport"]["clOrdId"]]
            if venta1 == 1:
                print(f"\nPaso2---------COMPRA {bono2}----------")
                send_order(bono2, pyRofex.Side.BUY, offer2_px, offer2_size_i)
                
                time.sleep(0.1) ### por el key error del 2do if de abajo...
                while True:
                    if order_rep["orderReport"]["status"] in ("NEW", "PARTIALLY_FILLED"):
                        print("\n*** Processing New Order --- PASO2 *** \n")
                        my_order[order_rep["orderReport"]["clOrdId"]] = order_rep
                    if order_rep["orderReport"]["status"] == "FILLED":
                        print("***Operation 2/4 Filled***\n\t\t\t*****IDA COMPLETED*****")
                        del my_order[order_rep["orderReport"]["clOrdId"]] #####**** keyError
                        #ida = 'OK'
                        break
                break


def opeVuelta():
    print(f"\nPaso3---------VENTA {bono2}----------")
    send_order(bono2, pyRofex.Side.SELL, bid2_px, offer2_size_i)
    time.sleep(0.1)

    if order_rep["orderReport"]["clOrdId"] in my_order.keys():
        while True:
            venta2 = 0
            if order_rep["orderReport"]["status"] in ("NEW", "PARTIALLY_FILLED"):
                print("***Processing New Order --- PASO3***\n")
                my_order[order_rep["orderReport"]["clOrdId"]] = order_rep
            if order_rep["orderReport"]["status"] == "FILLED":
                print("***Operation 3/4 Filled - Initiating Operation 4/4***")                
                print(order_rep["orderReport"]["status"], "...orderReportStatus...antes del TIME.SLEEP")
                print(my_order[order_rep["orderReport"]["clOrdId"]], "...keyError...antes del TIME.SLEEP")
                time.sleep(0.1) ####
                print(my_order[order_rep["orderReport"]["clOrdId"]], "...keyError...")
                del my_order[order_rep["orderReport"]["clOrdId"]] #####**** keyError
                venta2 = 1
            
            offer1_size_i = floor(bid2_px*offer2_size_i/offer1_px)
            if venta2==1 and offer1_size_i < offer2_size:
                print(f"\nPaso4---------COMPRA {bono1}----------")
                if acumNom == True:
                    send_order(bono1, pyRofex.Side.BUY, offer1_px, offer1_size_i)
                else:
                    send_order(bono1, pyRofex.Side.BUY, offer1_px, sell_size)
                time.sleep(0.1)

                while True:
                    if order_rep["orderReport"]["status"] in ("NEW", "PARTIALLY_FILLED"):
                        print("*** Processing New Order --- PASO4*** \n")
                        my_order[order_rep["orderReport"]["clOrdId"]] = order_rep
                    if order_rep["orderReport"]["status"] == "FILLED":
                        print("***Operation 4/4 Filled***\n\t\t*****VUELTA COMPLETED*****\n\t\t\tFINISHED")
                        del my_order[order_rep["orderReport"]["clOrdId"]]
                        #vuelta = 'OK'
                        break
                break
        time.sleep(20)
    else:
        time.sleep(20)
        # if ratio_vuelta > bInf:
        #     print(f"\nCondición faltante --> ratio_vuelta ({ratio_vuelta}) debe ser menor que bInf ({bInf}).")
        # elif offer1_size < offer2_size_i:
        #     print(f"Condición faltante --> offer1_size ({offer1_size}) debe ser mayor que offer2_size_i ({offer2_size_i}).")
        print(f"\n--------En espera para iniciar VUELTA----------")


def opeIdaVuelta():
    global bid1_px, offer2_px, offer2_size_i, bid2_px, offer2_size, offer1_px
    paso1, paso2, paso3, paso4 = 0, 0, 0, 0
    #size_niv2 = 2
    print(f'\npasos1-2-3-4 antes del while: {paso1, paso2, paso3, paso4}\n')
    while True:
        bid1_px = bid_offers.loc[bono1, 'Bid']
        bid1_size = bid_offers.loc[bono1, 'bidSize']
        offer1_px = bid_offers.loc[bono1, 'Offer']
        bid2_px = bid_offers.loc[bono2, 'Bid']
        offer2_px = bid_offers.loc[bono2, 'Offer']
        offer2_size = bid_offers.loc[bono2, 'offerSize']
        ratio_ida = round(bid1_px/offer2_px, 4) ### (pxCpa_b1 / pxVta_b2)

        niv1 = round(ratio - ratio*2*std/100, 4)
        niv2 = round(ratio - ratio*std/100, 4)
        niv3 = round(ratio + ratio*std/100, 4)
        niv4 = round(ratio + ratio*2*std/100, 4)
        offer2_size_i = floor(bid1_px*sell_size/offer2_px)

        # Inicio IDA: Venta b1 y Compra b2:
        if paso1==0 and (ratio_ida>=niv2 and ratio_ida<=ratio)\
            and offer2_size_i<offer2_size and bid1_size>=sell_size:
            opeIda()
            size_niv2 = offer2_size_i ##### guarda la cantidad comprada del b2, p/vender la misma en la opeVuelta correspondiente
            paso1=1
            print(f"Ida en Nivel 2 ---> OK, con ratio = {ratio_ida}")
        if paso2==0 and (ratio_ida>=ratio and ratio_ida<=niv3)\
            and offer2_size_i<offer2_size and bid1_size>=sell_size :
            opeIda()
            size_niv_ratio = offer2_size_i
            paso2=1
            print(f"Ida en Nivel 'ratio medio' ---> OK, con ratio = {ratio_ida}")
        if paso3==0 and (ratio_ida>=niv3 and ratio_ida<=niv4)\
            and offer2_size_i<offer2_size and bid1_size>=sell_size :
            opeIda()
            size_niv3 = offer2_size_i
            paso3=1
            print(f"Ida en Nivel 3 ---> OK, con ratio = {ratio_ida}")
        if paso4==0 and ratio_ida>=niv4 and offer2_size_i<offer2_size\
            and bid1_size>=sell_size :
            opeIda()
            size_niv4 = offer2_size_i
            paso4=1
            print(f"Ida en Nivel 4 ---> OK, con ratio = {ratio_ida}")

        print(f'\npasos1-2-3-4 después del 1er while: {paso1, paso2, paso3, paso4}\n')   
        print(f'\nRatio IDA: {ratio_ida}\n')
        print(f"\nNivel 1: {niv1}\nNivel 2: {niv2}\nRatio: {ratio}\nNivel 3: {niv3}\nNivel 4:  {niv4}")
        
        # Inicio VUELTA: Venta b2 y Compra b1:
        if paso1==1 or paso2==1 or paso3==1 or paso4==1:
            offer1_px = bid_offers.loc[bono1, 'Offer']
            bid2_px = bid_offers.loc[bono2, 'Bid']
            ratio_vuelta = round(offer1_px/bid2_px, 4) # pxVta_b1 / pxCpa_b2
            #offer1_size = bid_offers.loc[bono1, 'offerSize']
            bid2_size = bid_offers.loc[bono2, 'bidSize']
            print(f"\nRatio VUELTA: {ratio_vuelta}")
            if paso1==1 and ratio_vuelta < niv1 and bid2_size > size_niv2:
                offer2_size_i = size_niv2 ##### vende la cantidad comprada en la operación 2 de la IDA
                opeVuelta()
                paso1=0
                print(f"Vuelta en Nivel 1 ---> OK, con ratio = {ratio_vuelta}")
            if paso2==1 and ratio_vuelta < niv2 and bid2_size > offer2_size_i:
                offer2_size_i = size_niv_ratio
                opeVuelta()
                paso2=0
                print(f"Vuelta en Nivel 2 ---> OK, con ratio = {ratio_vuelta}")
            if paso3==1 and ratio_vuelta < ratio and bid2_size > offer2_size_i:
                offer2_size_i = size_niv3
                opeVuelta()
                paso3=0
                print(f"Vuelta en Nivel 'ratio medio' ---> OK, con ratio = {ratio_vuelta}")
            if paso4==1 and ratio_vuelta < niv3 and bid2_size > offer2_size_i:
                offer2_size_i = size_niv4
                opeVuelta()
                paso4=0
                print(f"Vuelta en Nivel 3 ---> OK, con ratio = {ratio_vuelta}") 

        
        #print(f"\nNivel 1: {niv1}/nNivel 2: {niv2}/nRatio: {ratio}/nNivel 3: {niv3}/nNivel 4:  {niv4}")
        else:
            #if offer2_size_i > offer2_size:
            print('...pasando por el else...')
            #print(f'\npasos1-2-3-4 en el else: {paso1, paso2, paso3, paso4}\n')
            #print(f"\nNivel 1: {niv1}\nNivel 2: {niv2}\nRatio: {ratio}\nNivel 3: {niv3}\nNivel 4:  {niv4}")
            # elif ratio_ida < bSup:
            #     print(f"Condición faltante --> ratio_ida ({ratio_ida}) debe ser mayor que bSup ({bSup}).")
            # elif bid1_size < sell_size:
            #     print(f"Condición faltante --> bid1_size ({bid1_size}) debe ser mayor que sell_size ({sell_size}).")
        time.sleep(10)

# Defines operations for strategy:
def strategy(data, sell_size, ratio, std, acumNom): #data --> df con bid&offers de los tickers.
    print(bid_offers)

    if (0 in bid_offers.values) == False:
        print(bid_offers)
        opeIdaVuelta()
    else:
        print("\n\t\t******** IDA sin iniciar ********\nreiniciando ------------")   
        time.sleep(10)

    strategy(data, sell_size, ratio, std, True)
        

strategy(bid_offers, sell_size, ratio, std, acumNom=True)





