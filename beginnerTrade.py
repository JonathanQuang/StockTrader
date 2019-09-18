import time
import alpaca_trade_api as tradeapi

maxPL = {}
exit_loop = False
is_sold = False

key_id = "REPLACE ME"
secret_key = "REPLACE ME"

api = tradeapi.REST(key_id, secret_key, base_url = "https://api.alpaca.markets", api_version='v2')
account = api.get_account()
print(account)
print("====")



def simple_buy(symbol, qty):
    if float(api.get_account().cash) >= api.get_barset(symbol, "1Min",1)[symbol][0].c + 1:
        api.submit_order(symbol = symbol, qty = qty, side = "buy", type = "market", time_in_force = "day")

def update_MaxPL_And_Decide_Sell(symbol):
    global maxPL
    if not(symbol in maxPL.keys()):
        maxPL[symbol] = -999
    currentPL = 0
    try:
        currentPL = float(api.get_position(symbol).unrealized_pl)
    except:
        return
    if maxPL[symbol] == -999:
        maxPL[symbol] = currentPL
        return
    if currentPL > maxPL[symbol]:
        maxPL[symbol] = currentPL
    elif currentPL < maxPL[symbol] - 0.10 or currentPL < -0.25:
        api.submit_order(symbol = symbol, qty = "1", side = "sell", type = "market", time_in_force = "day")
        print("sell request sent of " + symbol)


def GetBestSymbol(symbols):
    symbolRankDict = CalculateMetrics(symbols)
    bestSymbol = ""
    bestVal = 0
    for symbol in symbolRankDict:
        if symbolRankDict[symbol] > bestVal:
            bestVal = symbolRankDict[symbol]
            bestSymbol = symbol
    return bestSymbol

def CalculateMetrics(symbols):
    movingAverageDict = SMA_EMA(symbols)
    intermediate_dict = {}
    barsetData = api.get_barset(symbols, "5Min", 1)
    pointRankDict = {}
    for symbol in movingAverageDict:
        closingPrice = barsetData[symbol][0].c
        intermediate_dict[symbol] = {"SMA_momentum" : (movingAverageDict[symbol]["tenSMA"] - movingAverageDict[symbol]["twentySMA"]) / closingPrice, "EMA10_momentum" : (movingAverageDict[symbol]["tenEMA"] - movingAverageDict[symbol]["twentyEMA"]) / closingPrice}
        intermediate_dict[symbol]["10SMA_close_diff"] = (-1 * (movingAverageDict[symbol]["tenSMA"] - barsetData[symbol][0].c) / closingPrice)
        intermediate_dict[symbol]["10EMA_close_diff"] = (-1 * (movingAverageDict[symbol]["tenEMA"] - barsetData[symbol][0].c) / closingPrice)
        pointRankDict[symbol] = 0
    print(intermediate_dict)
    for metric in intermediate_dict[symbols[0]]:
        print(metric)
        rank1 = ""
        rank1val = -99999
        rank2 = ""
        rank2val = -99999
        for symbol in intermediate_dict:
            metricData = intermediate_dict[symbol][metric]
            if metricData < 0:
                pointRankDict[symbol] += -3
            if metricData > rank1val and metricData > rank2val:
                rank2val = rank1val
                rank2 = rank1
                rank1val = metricData
                rank1 = symbol
            elif metricData > rank2val and metricData < rank1val:
                rank2 = symbol
                rank2val = metricData
        pointRankDict[rank1] += 2
        pointRankDict[rank2] += 1
        #print("for " + metric + "rank 1 is " + rank1 + " and rank 2 is " + rank2)
    #print(pointRankDict)
    return pointRankDict
            

def SMA_EMA(symbols):
    printDict = {}
    barsetData = api.get_barset(symbols, "5Min",20)
    #print("barsetData")
    #print(barsetData)
    for symbol in barsetData:
        twentySum = 0
        tenSum = 0
        for x in range(20):
            if x > 9:
                tenSum += barsetData[symbol][x].c
            twentySum += barsetData[symbol][x].c
        printDict[symbol] = {"tenSMA" : tenSum / 10, "twentySMA" : twentySum / 20}
    twentyDayMultiplier = 2 / (20 + 1)
    tenDayMultiplier = 2 / (10 + 1)
    twentyEMA = {}
    tenEMA = {}
    EMA_return_dict = {}
    for symbol in barsetData:
        twentyEMA[symbol] = 0
        tenEMA[symbol] = 0
        for x in range(20):
            if x > 9:
                tenEMA[symbol] = barsetData[symbol][x].c * tenDayMultiplier + (tenEMA[symbol] * (1 - tenDayMultiplier))
            twentyEMA[symbol] = barsetData[symbol][x].c * twentyDayMultiplier + (twentyEMA[symbol] * (1 - twentyDayMultiplier))
        EMA_return_dict[symbol] = [tenEMA[symbol], twentyEMA[symbol]]
        printDict[symbol]["tenEMA"] = tenEMA[symbol]
        printDict[symbol]["twentyEMA"] = twentyEMA[symbol]
    return printDict
      

def calculate_EMA(symbols):
    printDict = {}
    barsetData = api.get_barset(symbols, "1D",20)
    for symbol in barsetData:
        twentySum = 0
        tenSum = 0
        for x in range(20):
            if x > 9:
                tenSum += barsetData[symbol][x].c
            twentySum += barsetData[symbol][x].c
        printDict[symbol] = {"tenSMA" : tenSum / 10, "twentySMA" : twentySum / 20}
    twentyDayMultiplier = 2 / (20 + 1)
    tenDayMultiplier = 2 / (10 + 1)
    twentyEMA = {}
    tenEMA = {}
    EMA_return_dict = {}
    for symbol in barsetData:
        twentyEMA[symbol] = 0
        tenEMA[symbol] = 0
        for x in range(20):
            if x > 9:
                tenEMA[symbol] = barsetData[symbol][x].c * tenDayMultiplier + (tenEMA[symbol] * (1 - tenDayMultiplier))
            twentyEMA[symbol] = barsetData[symbol][x].c * twentyDayMultiplier + (twentyEMA[symbol] * (1 - twentyDayMultiplier))
        EMA_return_dict[symbol] = [tenEMA[symbol], twentyEMA[symbol]]
        printDict[symbol]["tenEMA"] = tenEMA[symbol]
        printDict[symbol]["twentyEMA"] = twentyEMA[symbol]
    print(printDict)
    return EMA_return_dict

def calculate_SMA_diff(symbols):
    returnDict = {}
    printDict = {}
    barsetData = api.get_barset(symbols, "1D",20)
    for symbol in barsetData:
        twentySum = 0
        tenSum = 0
        for x in range(20):
            if x > 9:
                tenSum += barsetData[symbol][x].c
            twentySum += barsetData[symbol][x].c
        returnDict[symbol] = (tenSum / 10) - (twentySum / 20)
    return returnDict

def pick_strongest_SMA(symbols):
    maxVal = 0
    maxSymbol = ""
    calculated_data = calculate_SMA_diff(symbols)
    #print(calculated_data)
    for symbol in calculated_data:        
        if calculated_data[symbol] > maxVal:
            maxVal = calculated_data[symbol]
            maxSymbol = symbol
    return maxSymbol

firstWaitPeriod = True

while (True): 
    symbols = ["SNAP", "IGC", "TWTR", "BAC", "ON","INTC","SPWR","APPS","ZYXI","SH"]
    bannedSymbol = None
    print(GetBestSymbol(symbols))
    print(api.get_account().cash)
    print(api.get_account().daytrade_count < 3)

    exit_loop = False

    print("begin waiting for market open")

    while (exit_loop == False):
        clock_entity = api.get_clock()
        if clock_entity.is_open == True:
            exit_loop = True
        else:
            time.sleep(1)
            #print(clock_entity)
            #time.sleep(1)
        time.sleep(1)

    print("market open")

    if firstWaitPeriod == True:
        #time.sleep(3600)
        for x in range(180):
            position_list = api.list_positions()
            if not(position_list == []):
                for p in position_list:
                    update_MaxPL_And_Decide_Sell(p.symbol)
            time.sleep(60)
        firstWaitPeriod = False
    else:
        time.sleep(60)

    print("should be around 12:30")

    bestSymbol = GetBestSymbol(symbols)
    print("attempt to buy " + bestSymbol)

    simple_buy(bestSymbol, 2)
    bannedSymbol = bestSymbol
    

    #maxPL = -999


    end_sell_loop = False
    while (end_sell_loop == False):
        position_list = api.list_positions()
        for p in position_list:
            if not(p.symbol == bannedSymbol) or api.get_account().daytrade_count < 3:
                update_MaxPL_And_Decide_Sell(p.symbol)
        if (api.list_positions() == [] or api.get_clock().is_open == False):
            end_sell_loop = True
            firstWaitPeriod = True
        time.sleep(15)

    time.sleep(43200)
