# Gate.io connector to Manage Orders
import gate_api
from gate_api import Order
from gate_api.exceptions import GateApiException, ApiException

# STD imports
import time
import json
from multiprocessing.pool import ApplyResult

# Internal Imports
from . import GATEIO_KEY, GATEIO_SECRET
from . import OrderToBePlaced, PlacedOrders


class GateIO:
    def __init__(self):
        configuration = gate_api.Configuration(
            host="https://api.gateio.ws/api/v4",
            key=GATEIO_KEY,
            secret=GATEIO_SECRET,
        )
        api_client = gate_api.ApiClient(configuration)
        self.api_instance = gate_api.SpotApi(api_client)

    async def place_batch_orders(self, orders: list[OrderToBePlaced] | OrderToBePlaced) -> list[PlacedOrders]:
        """Place Batch of Orders For tickers Max 10 Orders/Ticker and Max 3 Tickers

        `@param orders:` a list of gate-io.Order objects (required param for order price & amount
        """
        if not isinstance(orders, list):
            orders = [orders]


        try:
            # Create a batch of orders
            api_response:ApplyResult = self.api_instance.create_batch_orders(orders, async_req=True)
            response = api_response.get()
            orders_list = []
            for order_placed in response:
                response = PlacedOrders(
                    price = order_placed.price,
                    tokens = order_placed.amount,
                    create_time = order_placed.create_time,
                    currency_pair = order_placed.currency_pair,
                    order_id= order_placed.id,
                    side = order_placed.side.upper(),
                    success = order_placed.succeeded)
                orders_list.append(response)
            return orders_list
        except GateApiException as ex:
            print(
                "Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message)
            )
            return [PlacedOrders(0,0,0,0,'NotPlaced','BUY',False)]
        except ApiException as e:
            print("Exception when calling SpotApi->list_all_open_orders: %s\n" % e)
            return [PlacedOrders(0,0,0,0,'NotPlaced','BUY',False)]


    async def get_all_open_orders(self):
        """Returns All Open Order, Placed Limit Orders"""

        # @DEV Page and Limit are hardcoded bcz no way i will place more then 100 trades at a time
        page = 1
        limit = 100
        account = ""
        try:
            api_response:ApplyResult = self.api_instance.list_all_open_orders(
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



async def main():
    x = await GateIO().place_batch_orders('x')
    for i in x:
        print(i)

    """
    # Place an Order If tp is hit On one or more orders 
    # https://github.com/gateio/gateapi-python/blob/master/docs/SpotApi.md#create_order



    # Place TP for an order as soon as Order is hit 
    # https://github.com/gateio/gateapi-python/blob/master/docs/SpotApi.md#create_order



    # Spot Account Boot get histry of ticker balances
    # https://github.com/gateio/gateapi-python/blob/master/docs/SpotAccountBook.md

    """
