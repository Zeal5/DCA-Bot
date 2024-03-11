# Gate.io connector to Manage Orders
import gate_api
from gate_api import Order, OpenOrders
from gate_api.exceptions import GateApiException, ApiException
from typing import Optional

# STD imports
from multiprocessing.pool import ApplyResult
from dataclasses import dataclass
import asyncio, aiohttp

# Internal Imports
from . import GATEIO_KEY, GATEIO_SECRET
from . import OrderToBePlaced, PlacedOrders
from grid_line_machine import GridLine, GridLineManager


@dataclass
class PriceUpdate:
    ticker: str
    market_price: Optional[float] = None


class GateIO:
    def __init__(self):
        configuration = gate_api.Configuration(
            host="https://api.gateio.ws/api/v4",
            key=GATEIO_KEY,
            secret=GATEIO_SECRET,
        )
        self.api_client = gate_api.ApiClient(configuration)
        self.api_instance = gate_api.SpotApi(self.api_client)

    async def prices(self) -> dict[str, str]:
        host = "https://api.gateio.ws"
        prefix = "/api/v4"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        url = "/spot/tickers"
        async with aiohttp.ClientSession() as session:
            async with session.get(host + prefix + url, headers=headers) as r:
                x = await r.json()
                return {data["currency_pair"]: data["highest_bid"] for data in x}

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
            await asyncio.sleep(0.1)
            response = api_response.get()
            orders_list = []
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
            return [PlacedOrders(0, 0, 0, 0, _ticker, "buy", False, "ApiException")]

    async def get_all_open_orders(self) -> OpenOrders:
        """Returns All Open Order, Placed Limit Orders"""

        # @DEV Page and Limit are hardcoded bcz no way i will place more then 100 trades at a time
        page = 1
        limit = 100
        try:
            api_response: ApplyResult = self.api_instance.list_all_open_orders(
                page=page, limit=limit, async_req=True
            )
            #     await asyncio.sleep(1)
            return api_response.get()

        except GateApiException as ex:
            print(
                "Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message)
            )
        except ApiException as e:
            print("Exception when calling SpotApi->list_all_open_orders: %s\n" % e)

    async def get_price(self):
        # @DEEV check what exactly this returns and take argument of ticker
        return self.api_instance.list_tickers(currency_pair="VANRY_USDT")

    async def check_filled_order_status(self, _order_id: int, _ticker: str):
        api_response = self.api_instance.get_order(_order_id, _ticker, async_req=True)
        await asyncio.sleep(0.1)
        return api_response.get()


class GateIOManager:
    """A Stand Alone Instance representing each grid line for  each ticker
    buy, sell, buy batch, get price for ticker"""

    def __init__(self):
        self.gateio_instance = GateIO()

    async def buy(
        self, _order: GridLine, _currency_pair: str, _usd_amount_to_spend: float
    ) -> PlacedOrders:
        """Convert from GridLine to OrderToBePlaced type"""
        new_order = OrderToBePlaced(
            currency_pair=_currency_pair,
            price=_order.price,
            amount=_usd_amount_to_spend / _order.price,
            side="buy",
        )

        order_status = await self.gateio_instance.place_batch_orders(new_order)

        return order_status[0]

    async def sell(
        self, _order: GridLine, _currency_pair: str, _usd_amount_to_spend: float
    ) -> PlacedOrders:
        """Convert from GridLine to OrderToBePlaced type"""
        new_order = OrderToBePlaced(
            currency_pair=_currency_pair,
            price=_order.price,
            amount=_usd_amount_to_spend / _order.price,
            side="sell",
        )
        order_status = await self.gateio_instance.place_batch_orders(new_order)
        return order_status[0]

    async def batch_buy(
        self,
        _grid_lines: list[GridLine],
        _currency_pair: str,
        _usd_amount_to_spend: float,
    ):
        _orders_list = []
        for _each_grid in _grid_lines:
            _orders_list.append(
                OrderToBePlaced(
                    currency_pair=_currency_pair,
                    price=_each_grid.price,
                    amount=_usd_amount_to_spend / _each_grid.price,
                    side="buy",
                )
            )

        if len(_orders_list) < 1:
            print(f"No grid lines avaialble for {_currency_pair}")
            return
        _orders_status = await self.gateio_instance.place_batch_orders(_orders_list)
        return _orders_status

    async def get_order_status(self, _order_id: int, _ticker: str):
        orders_statuses = await self.gateio_instance.check_filled_order_status(
            _order_id, _ticker
        )
        return orders_statuses

    async def get_all_open_orders(self) -> OpenOrders:
        return await self.gateio_instance.get_all_open_orders()


class GateIOConnector:
    """Takes in multiple lists of GridLIne objects then runs in loop to keep track
    of prices for each ticker and place orders using GateIOManager class"""

    prices_objects: dict[str, PriceUpdate] = {}

    def __init__(self, *grid_lines_objects: GridLineManager):
        self.grid_line_managers = grid_lines_objects

        # create prices_objects from grid_lines_objects.tickers
        for grid_line_manager in self.grid_line_managers:
            _ticker = grid_line_manager.ticker
            GateIOConnector.prices_objects[_ticker] = PriceUpdate(_ticker)

    async def check_order_status(
        self, _grid_line: GridLine, _ticker: str, _giom: GateIOManager
    ) -> bool:
        order_status = await _giom.get_order_status(_grid_line.order_id, _ticker)
        # @DEV If order was cancled by user(or due to some unforseen reason) handle .finish_as "closed/cancled"?
        if order_status.finish_as == "filled":
            if order_status.side == "buy":
                _grid_line.buy_order_triggerd(order_status.amount)
                return True
            else:
                _grid_line.sell_order_triggerd(order_status.amount)
                return True
        else:
            return False

    async def buy(
        self,
        _grid_line: GridLine,
        _grid_line_manager: GridLineManager,
        _giom: GateIOManager,
    ):
        # @DEV check if _grid_line exeeds do_not_buy price
        if (
            _grid_line.price > _grid_line_manager.do_not_buy_above_price
            or _grid_line.price < _grid_line_manager.do_not_buy_below_price
        ):
            # print("Restricted buy region")
            return
        gateio_manager = _giom
        status = await gateio_manager.buy(
            _order=_grid_line,
            _currency_pair=_grid_line_manager.ticker,
            _usd_amount_to_spend=_grid_line_manager.usd_to_buy_with,
        )

        if status.success:
            _grid_line.buy_order_success(status.order_id)

        elif status.label:
            print(f"Failed to place Buy Order for ticker {_grid_line_manager.ticker}")
        else:
            print("Line 207 code should never reach here")

    async def sell(
        self,
        _grid_line: GridLine,
        _grid_line_manager: GridLineManager,
        _giom: GateIOManager,
    ):
        # @DEV check if _grid_line exeeds do_not_buy price
        if _grid_line is None:
            return
        if (
            _grid_line.price > _grid_line_manager.do_not_buy_above_price
            or _grid_line.price < _grid_line_manager.do_not_buy_below_price
        ):
            # print("Restricted buy region")
            return
        gateio_manager = _giom
        status = await gateio_manager.sell(
            _order=_grid_line,
            _currency_pair=_grid_line_manager.ticker,
            _usd_amount_to_spend=_grid_line_manager.usd_to_buy_with,
        )

        if status.success:
            _grid_line.sell_order_success(status.order_id)

        elif status.label:
            print(
                f"Failed to place an Sell Order for ticker {_grid_line_manager.ticker}"
            )
        else:
            print("Line 207 code should never reach here")

    async def remove_duplicate_orders(
        self, _grid_line_manager: GridLineManager, _giom: GateIOManager
    ) -> list[GridLine]:
        _grids = []
        orders_list: OpenOrders = await _giom.get_all_open_orders()

        for orders in orders_list:
            if orders.currency_pair == _grid_line_manager.ticker:
                for order in orders.orders:
                    for grid in _grid_line_manager:
                        if round(float(order.price), 5) == round(float(grid.price), 5):
                            if order.side == "buy":
                                grid.buy_order_placed = True
                                grid.order_id = order.id
                                _grids.append(grid)

                            elif order.side == "sell":
                                # Last grid where buy was placed
                                grid.last_grid_line.buy_order_filled = True
                                grid.last_grid_line.total_buy_orders += 1
                                # Current grid where sell order is placed
                                grid.sell_order_placed = True
                                grid.order_id = order.id
                                _grids.append(grid)
                                _grids.append(grid.last_grid_line)

        return _grids

    async def buy_batch_order(
        self, _mp: float, _grid_line_manager: GridLineManager, _giom: GateIOManager
    ):
        orders_already_placed = await self.remove_duplicate_orders(
            _grid_line_manager, _giom
        )
        _grids_where_order_are_to_be_placed = []
        for _each_grid in _grid_line_manager:
            if (
                _mp > _each_grid.price
                and _grid_line_manager.do_not_buy_below_price
                < _each_grid.price
                < _grid_line_manager.do_not_buy_above_price
            ) and _each_grid not in orders_already_placed:
                _grids_where_order_are_to_be_placed.append(_each_grid)

        _statuses = await _giom.batch_buy(
            _grid_lines=_grids_where_order_are_to_be_placed,
            _currency_pair=_grid_line_manager.ticker,
            _usd_amount_to_spend=_grid_line_manager.usd_to_buy_with,
        )
        if _statuses is None:
            return
        for status in _statuses:
            if status.label is None and status.success:
                grid = _grid_line_manager.grid_line_obj_map_price(status.price)
                grid.buy_order_success(status.order_id)

            else:
                print(
                    f"Placing Batch order failed {status.label=} : ticker : {_grid_line_manager.ticker}"
                )
                # @Dev for testing

    async def entry_point(self):
        """Start Loop to track prices for each class
        Seperate Each ticker tracking create a worker using asyncio.get_loop"""
        _tasks = []
        # Task 1 global_price_updater
        # * each GridLineManager watcher i.e : ticker_watcher
        loop = asyncio.get_event_loop()
        _tasks.append(
            loop.create_task(self.global_price_updater())
        )  # each task is grid for unique ticker
        for _grid_line_manager in self.grid_line_managers:
            _tasks.append(self.ticker_watcher(_grid_line_manager))
        await asyncio.gather(*_tasks)

    async def ticker_watcher(self, _grid_line_manager: GridLineManager):
        """Called with GridLineManager as param and places order on Gateio"""
        # gateio manager
        giom = GateIOManager()
        _ticker = _grid_line_manager.ticker
        print(_ticker, _grid_line_manager.grid_lines)
        _decimals = _grid_line_manager.round_price_to

        last_price = GateIOConnector.prices_objects[_ticker].market_price or 0

        while last_price == 0:
            await asyncio.sleep(0.1)
            last_price = GateIOConnector.prices_objects[_ticker].market_price or 0

        await self.buy_batch_order(last_price, _grid_line_manager, giom)
        last_lower_grid, last_higher_grid = last_price, last_price
        while True:
            market_price: float = GateIOConnector.prices_objects[_ticker].market_price
            lower_grid, higher_grid = _grid_line_manager.get_region(market_price)

            # DEV check if price is within 1% of any grid
            price_in_lower_grid_range = False
            price_in_higher_grid_range = False
            if round(market_price - (0.005 * market_price), _decimals) < lower_grid:
                price_in_lower_grid_range = True

            if round(market_price + (0.005 * market_price), _decimals) > higher_grid:
                price_in_higher_grid_range = True

            # if market_price != last_price:
            print(f"{_ticker}  mp: {round(market_price,_decimals)}\t\t REGION : {lower_grid} : {higher_grid}")
            if (
                (last_lower_grid != lower_grid and last_higher_grid != higher_grid)
                or price_in_lower_grid_range
                or price_in_higher_grid_range
            ):
                await self.manage_trades(market_price, _grid_line_manager, giom)

                # last_price = market_price
            await asyncio.sleep(0.5)
            last_lower_grid, last_higher_grid = lower_grid, higher_grid

    async def manage_trades(
        self, _mp: float, _grid_line_manager: GridLineManager, _giom: GateIOManager
    ):
        for _grid_line in _grid_line_manager:
            # Handle if limit order is still there
            # for lines below mp
            if _grid_line.buy_order_placed:
                # check if buy order placed got filled
                if await self.check_order_status(
                    _grid_line, _grid_line_manager.ticker, _giom
                ):
                    await self.sell(
                        _grid_line.next_grid_line, _grid_line_manager, _giom
                    )

            # for gridlines below mp with active sell order
            # check if sell order was triggerd to place buy order
            elif _grid_line.sell_order_placed:
                if await self.check_order_status(
                    _grid_line, _grid_line_manager.ticker, _giom
                ):
                    await self.buy(_grid_line.last_grid_line, _grid_line_manager, _giom)

            # for gridlines below mp with no active sell order nor buy order
            # place buy order
            elif _grid_line.price < _mp and not (
                _grid_line.buy_order_filled or _grid_line.buy_order_placed
            ):
                await self.buy(_grid_line, _grid_line_manager, _giom)

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
        for k, v in cls.prices_objects.items():  # k == ticker, v == price
            cls.prices_objects[k].market_price = float(gate_prices[k])
