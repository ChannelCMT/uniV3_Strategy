from univ3api.simulation import PoolSimiulation, PositionInstance, PoolFee
import univ3api.utils as utils
import numpy as np

class HoldStrategy(PoolSimiulation):
    def __init__(self, amount0: int, amount1: int, decimal0: int, decimal1: int, fee: PoolFee, price_reverse: bool=False) -> None:
        super().__init__(amount0, amount1, decimal0, decimal1, fee, price_reverse)
        self.position_id = None
        self.increased = False
        self.mint_price = 0
        self.mint_timestamp = 0
        self.duration = int(8*3600)
        self.factor0 = 10**self.decimal0
        self.factor1 = 10**self.decimal1
        self.pc = utils.PriceConverter(18, 6)

    def price_in_range(self, price):
        return self.lower_price < price < self.upper_price

    def cal_tick(self, upperTick, lowerTick):
        upper_tick = upperTick - upperTick % 60
        lower_tick = lowerTick - lowerTick % 60
        return upper_tick, lower_tick

    def on_time(self, data: dict):
        price = data["price"]
        ts = data["timestamp"]
        trend = data['trend']
        if trend and not self.position_id:
            self.upper_price = price*1.25
            self.lower_price = price*0.8
            self.swap(1, pct=0.5)
            tick = self.pc.price_to_tick(price)
            upperTick = self.pc.price_to_tick(self.upper_price)
            lowerTick = self.pc.price_to_tick(self.lower_price)
            # (1)
            print('$$$$$$$:', self.upper_price)
            print('$$$$$$$:', self.lower_price)
            
            if self.price_in_range(price):
                upper_tick, lower_tick = self.cal_tick(upperTick, lowerTick)
                # cal L
                L, amount0, amount1 = utils.PositionUtil.cal_liquidity(
                                    cprice=1.0001**tick,
                                    upper=1.0001**upper_tick,
                                    lower=1.0001**lower_tick,
                                    amt0=None,
                                    amt1=int(self.amount1)
                                )
                print('######:', L, amount0, amount1)
                pu = utils.PositionUtil(
                                        L,
                                        tick_lower=lower_tick,
                                        tick_upper=upper_tick,
                                        decimal0=18,
                                        decimal1=6
                                        )
                t0 = pu.amount0_t(tick)
                t1 = pu.amount1_t(tick)
                # self.amount0 = t0
                # self.amount1 = t1

                print('t0:', t0, 't1:', t1)

                position, amt0, amt1 = self.mint(
                    lower_tick, upper_tick,
                    int(t0), int(t1)
                )
                self.position_id = position.token_id
                print(f"{self.timestamp}, {self.block_number}")
                print(f"Mint position： {position}")
                print(f"Mint amount: token0={amt0/self.factor0}, token1={amt1/self.factor1}")
                print(f"Wallet amount: token0={self.amount0/self.factor0}, token1={self.amount1/self.factor1}")
                self.mint_price = price
                self.mint_timestamp = ts
        else: 
            if self.position_id and not self.price_in_range(price):
                print(f"Price({price}) out of range({self.lower_price}, {self.upper_price})")
                position, amt0, amt1 = self.decrease_liquidity(self.position_id, pct=1)
                print(f"{self.timestamp}, {self.block_number}")
                print(f"Decreased position： {position}")
                print(f"Decreased amount: token0={amt0/self.factor0}, token1={amt1/self.factor1}")
                print(f"Wallet amount: token0={self.amount0/self.factor0}, token1={self.amount1/self.factor1}")
                self.collect(self.position_id)
                self.position_id = None
                self.increased = False
                return
                