import pandas as pd
import Binance
import math
from talib import EMA, ATR, RSI, MFI
import tulipy as ti
import numpy as np 

def floatPrecision(f, n):
    n = int(math.log10(1 / float(n)))
    f = math.floor(float(f) * 10 ** n) / 10 ** n
    f = "{:0.0{}f}".format(float(f), n)
    return str(int(f)) if int(n) == 0 else f

class start:
    def __init__(self, symbol, quote, base, step_size, leverage, interval, roundQuant, position):
        self.symbol = symbol
        self.quote = quote
        self.base = base
        self.step_size = step_size
        self.leverage = leverage
        self.interval = interval
        self.roundQuant = roundQuant
        self.position = position
        self.df = self.getData()
        self.changeLeverage = self.changeLeverage()
        self.openPosition = float(Binance.client.futures_position_information()[self.position]['positionAmt'])
        self.quoteBalance = float(Binance.client.futures_account_balance(asset=self.quote)['balance'])
        self.baseBalance = float(Binance.client.futures_get_all_orders(symbol=self.symbol)[-1]['origQty'])
        self.Quant = self.checkQuant()
        self.fire = self.strategy()
        
    def getData(self):
        candles = Binance.client.futures_klines(symbol=self.symbol, interval=self.interval)

        #Sorting candlestick using Pandas
        df = pd.DataFrame(candles)
        df = df.drop(range(6, 12), axis=1)

        # put in dataframe and clean-up
        col_names = ['time', 'open', 'high', 'low', 'close', 'volume']
        df.columns = col_names
        # transform values from strings to floats
        for col in col_names:
            df[col] = df[col].astype(float)

        return df

    def changeLeverage(self):
        def change():
            change = Binance.client.futures_change_leverage(
                symbol=self.symbol, 
                leverage=self.leverage)
        return change()

    def checkQuant(self):
        df = self.df    
        canBuySell = (float(self.quoteBalance)/float(self.df['close'][499]))*0.04*self.leverage
        BuySellQuant = floatPrecision(canBuySell, self.roundQuant)
        return BuySellQuant

    def strategy(self):

        df = self.df

        mfi = MFI(df['high'], df['low'], df['close'], df['volume'], timeperiod=9)
        mfi = float(mfi[499])

        atr = ATR(df['high'], df['low'], df['close'], timeperiod=14)
        atr = float(atr[499])

        """STOCHRSI"""
        rsi = RSI(df['close'], timeperiod=5)
        rsinp = rsi.values
        rsinp = rsinp[np.logical_not(np.isnan(rsinp))]
        fastd, fastk = ti.stoch(rsinp, rsinp, rsinp, 14, 9, 3)
        """"""""""""""
        k = float(fastd[-1])
        d = float(fastk[-1])

        current = float(floatPrecision(df['close'][499], self.step_size))

        #longSL = float(floatPrecision((baseline - atr), self.step_size))
        #longTP = float(floatPrecision((current + atr*3), self.step_size))
        #shortSL = float(floatPrecision((baseline + atr), self.step_size))
        #shortTP = float(floatPrecision((current - atr*3), self.step_size))

        def clearOrders():
            order = Binance.client.futures_cancel_all_open_orders(
                symbol = self.symbol)
            
        def closeSellOrder():
            orderBuy = Binance.client.futures_create_order(
                symbol = self.symbol,
                side = 'BUY',
                type = 'MARKET',
                quantity = self.baseBalance,
                reduceOnly='true')
            
        def closeBuyOrder():
            orderSell = Binance.client.futures_create_order(
                symbol = self.symbol,
                side = 'SELL',
                type = 'MARKET',
                quantity = self.baseBalance,
                reduceOnly='true')
            
        def placeSellOrder():
            orderSell = Binance.client.futures_create_order(
                symbol = self.symbol,
                side = 'SELL',
                type = 'MARKET',
                quantity = self.Quant)

        def placeBuyOrder():
            orderBuy = Binance.client.futures_create_order(
                symbol = self.symbol,
                side = 'BUY',
                type = 'MARKET',
                quantity = self.Quant)
            
        def longStop():
            order = Binance.client.futures_create_order(
                symbol = self.symbol,
                side = 'SELL',
                type = 'STOP_MARKET',
                stopPrice = longSL,
                closePosition='true')
            
        def shortStop():
            order = Binance.client.futures_create_order(
                symbol = self.symbol,
                side = 'BUY',
                type = 'STOP_MARKET',
                stopPrice = shortSL,
                closePosition='true')
            
        def longProfit():
            order = Binance.client.futures_create_order(
                symbol = self.symbol,
                side = 'SELL',
                type = 'TAKE_PROFIT_MARKET',
                stopPrice = longTP,
                closePosition='true')
            
        def shortProfit():
            order = Binance.client.futures_create_order(
                symbol = self.symbol,
                side = 'BUY',
                type = 'TAKE_PROFIT_MARKET',
                stopPrice = shortTP,
                closePosition='true')

        """Conditions for trading"""

        longCond = k > d and mfi < 30 and self.openPosition == 0
        closeLongCond = k < d and self.openPosition > 0
        shortCond = k < d and mfi > 70 and self.openPosition == 0
        closeShortCond = k > d and self.openPosition < 0

        while longCond == True:
            #placeBuyOrder()
            print('BUY ORDER PLACED on', self.base)
            break
            
        while closeLongCond == True:
            #closeBuyOrder()
            print('Closed BUY ORDER on', self.base)
            break

        while shortCond == True:
            #placeSellOrder()
            print('SELL ORDER PLACED on', self.base)
            break
            
        while closeShortCond == True:
            #closeSellOrder()
            print('Closed SELL ORDER on', self.base)
            break
            
def run(pair, q, b, step, levr, t, r, p):
    symbol = pair
    quote = q
    base = b
    step_size = step
    leverage = levr
    interval = t
    roundQuant = r
    position = p
    step1 = start(symbol, quote, base, step_size, leverage, interval, roundQuant, position)
