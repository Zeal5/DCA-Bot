# Gate.io connector to Manage Orders
import gate_api
from gate_api import Order
from gate_api.exceptions import GateApiException, ApiException
from typing import Literal, Optional

# STD imports
import time
import json
from multiprocessing.pool import ApplyResult
from dataclasses import dataclass
import asyncio
from pprint import pprint

# Internal Imports
from . import GATEIO_KEY, GATEIO_SECRET
from . import OrderToBePlaced, PlacedOrders
from grid_line_machine import GridLine, GridLineManager

@dataclass
class PriceUpdate:
    ticker:str
    market_price : Optional[float] =None


class GateIO:
    def __init__(self):
        configuration = gate_api.Configuration(
            host="https://api.gateio.ws/api/v4",
            key=GATEIO_KEY,
            secret=GATEIO_SECRET,
        )
        api_client = gate_api.ApiClient(configuration)
        self.api_instance = gate_api.SpotApi(api_client)

    async def prices(self) -> list[dict[str,str]]:
        prices_list = self.api_instance.list_tickers(async_req=True)
        await asyncio.sleep(1)
        prices_list = prices_list.get()
        x = {prices.currency_pair : prices.highest_bid for prices in prices_list}
        return x 

    async def place_batch_orders(
        self, orders: list[OrderToBePlaced] | OrderToBePlaced
    ) -> list[PlacedOrders]:
        """Place Batch of Orders For tickers Max 10 Orders/Ticker and Max 3 Tickers

        `@param orders:` a list of OrderToBePlaced objects (required param for order price & amount,currency_pair
        order = [OrderToBePlaced("VANRY_USDT",0.02,600,'buy')]
        """
        _ticker = ""
        if not isinstance(orders, list):
            orders = [orders]

        _ticker = orders[0].currency_pair
        list_of_gateio_order_type = []
        for order in orders:
            list_of_gateio_order_type.append(
                Order(
                    currency_pair=order.currency_pair,
                    amount=f"{order.amount}",
                    price=f"{order.price}",
                    side=order.side,
                    text="t-apiv4",
                )
            )

        try:
            # Create a batch of orders
            api_response: ApplyResult = self.api_instance.create_batch_orders(
                list_of_gateio_order_type, async_req=True
            )
            await asyncio.sleep(.1)
            response = api_response.get()
            orders_list = []
            print(response)
            for order_placed in response:
                response = PlacedOrders(
                    price=order_placed.price,
                    tokens=order_placed.amount,
                    create_time=order_placed.create_time,
                    currency_pair=order_placed.currency_pair,
                    order_id=order_placed.id,
                    side=order_placed.side,
                    success=order_placed.succeeded,
                    label=order_placed.label,
                )
                orders_list.append(response)
            return orders_list
        except GateApiException as ex:
            print(
                "Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message)
            )
            return [PlacedOrders(0, 0, 0, 0, _ticker, "buy", False, "GateApiException")]
        except ApiException as e:
            print("Exception when calling SpotApi->list_all_open_orders: %s\n" % e)
            return [PlacedOrders(0, 0, 0, 0,_ticker, "buy", False, "ApiException")]

    async def get_all_open_orders(self):
        """Returns All Open Order, Placed Limit Orders"""

        # @DEV Page and Limit are hardcoded bcz no way i will place more then 100 trades at a time
        page = 1
        limit = 100
        try:
            api_response: ApplyResult = self.api_instance.list_all_open_orders(
                page=page, limit=limit, async_req=True
            )
            # while not api_response.ready():
            #     await asyncio.sleep(1)
            return api_response.get()

        except GateApiException as ex:
            print(
                "Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message)
            )
        except ApiException as e:
            print("Exception when calling SpotApi->list_all_open_orders: %s\n" % e)

    async def get_price(self):
        # currency_pair=currency_pair, timezone=timezone
        return self.api_instance.list_tickers(currency_pair="VANRY_USDT")


class GateIOManage:
    """A Stand Alone Instance representing each grid line for  each ticker
        buy, sell, buy batch, get price for ticker"""
    def __init__(
        self,
        _ticker: str,
        _token_amount: float,
        _price : str
    ):
        self.ticker = _ticker
        self.amount = _token_amount
        self.price  = _price

    async def buy(self) -> list[PlacedOrders]:
        order = OrderToBePlaced(
            currency_pair=self.ticker, price=self.price, amount=self.amount, side="buy"
        )

        return await GateIO().place_batch_orders(order)



class GateIOConnector:
    """Takes in multiple lists of GridLIne objects then runs in loop to keep track 
    of prices for each ticker and place orders usin GateIOManage class"""
    prices_objects: dict[str,PriceUpdate] = {}
    def __init__(self,*grid_lines_objects:GridLineManager):
        self.grid_line_managers = grid_lines_objects

        # create prices_objects from grid_lines_objects.tickers
        for grid_line_manager in self.grid_line_managers:
            _ticker = grid_line_manager.ticker
            GateIOConnector.prices_objects[_ticker] = PriceUpdate(_ticker)


    async def entry_point(self):
        """Start Loop to track prices for each class
        Seperate Each ticker tracking create a worker using asyncio.get_loop"""
        _tasks = []
        # Task 1 global_price_updater 
        # * each GridLineManager watcher i.e : ticker_watcher
        loop = asyncio.get_event_loop()
        _tasks.append(loop.create_task(self.global_price_updater()))# each task is grid for unique ticker
        for _grid_line_manager in self.grid_line_managers:
            _tasks.append(self.ticker_watcher(_grid_line_manager))
        await asyncio.gather(*_tasks)
        

    async def ticker_watcher(self, _grid_line_manager:GridLineManager):
        """Called with GridLineManager as param and places order on Gateio"""
        # @DEV testing 
        print(_grid_line_manager.grid_lines)
        _ticker = _grid_line_manager.ticker

        old_market_price = 0
        last_price = GateIOConnector.prices_objects[_ticker].market_price or 0 

        while True:
            market_price = GateIOConnector.prices_objects[_ticker].market_price

            # @DEV carefull here as last price is 0 grids between mp and 0 are get triggerd 
            if market_price is not None and market_price != old_market_price:
                print(f"{_ticker}  {market_price =}\t{last_price=}")
                for _grid_line in _grid_line_manager:
                    # Crosed grid line from above
                    if last_price >= _grid_line.price > market_price and _grid_line.in_trade is False:
                        print(f"Bought @ {_grid_line.price} {_ticker} mp > lp {market_price > last_price}")

                    # Crosed grid line from below
                    elif last_price <= _grid_line.price < market_price and _grid_line.in_trade is False:
                        print(f"Sold @ {_grid_line.price}   {_ticker} mp > lp {market_price > last_price}")


                old_market_price = market_price
                last_price = market_price
            await asyncio.sleep(2)

        
    async def global_price_updater(self):
        gate = GateIO()
        while True:
            await GateIOConnector.update_prices(gate)

    @classmethod
    async def update_prices(cls, _gate_io: GateIO):
        """Call spot/ticker endpoint to fetch all prices and then get prices of
        tickers in tickers_list
        @DEVOnly update last price"""

        gate_prices = await _gate_io.prices()
        for k,v in cls.prices_objects.items(): # k == ticker, v == price
            cls.prices_objects[k].market_price = float(gate_prices[k])

        



"""
@dataclass
class PriceUpdate:
    ticker:str
    last_price : float
    market_price : float
"""
