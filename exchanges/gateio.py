# Gate.io connector to Manage Orders
import aiohttp
import gate_api

# STD imports
import time
import hashlib
import hmac
import json
from dataclasses import dataclass
from enum import Enum
import asyncio

# Internal Imports
from . import GATEIO_KEY, GATEIO_SECRET


class EndPoints(Enum):
    """`url` endpoint url in host + prefix + url"""
    my_trades: str = "/spot/my_trades"


class HttpMethod(Enum):
    """HTTP methods for signature verification"""
    get: str = "GET"
    post: str = "POST"


class GateIO:
    def __init__(self):
        self.key = GATEIO_KEY
        self.secret = GATEIO_SECRET
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.host = "https://api.gateio.ws"
        self.prefix = "/api/v4"

        # @DEV Make it such that each property is added to
        # call automatically when required

    def update_headers(self, headers: dict[str, str]):
        self.headers.update(headers)

    def gen_sign(self, method, url :EndPoints, query_string=None, payload_string=None):
        """generate authentication headers

        :param method: http request method
        :param url: http resource path
        :param query_string: query string
        :param body: request body
        :return: signature headers
        """
        key = self.key  # api_key
        secret = self.secret  # api_secret
        #@DEV chanhged here
        url = self.prefix + url.value

        t = time.time()
        m = hashlib.sha512()
        m.update((payload_string or "").encode("utf-8"))
        hashed_payload = m.hexdigest()
        s = "%s\n%s\n%s\n%s\n%s" % (method, url, query_string or "", hashed_payload, t)
        sign = hmac.new(
            secret.encode("utf-8"), s.encode("utf-8"), hashlib.sha512
        ).hexdigest()
        return {"KEY": key, "Timestamp": str(t), "SIGN": sign}


    async def open_orders(self):
        url = EndPoints.my_trades
        method = HttpMethod.get.value
        sig = self.gen_sign(method,url)
        self.update_headers(sig)
        return await self.send_req(url)

    async def send_req(self, _end_point : EndPoints):
        print(self.headers)
        url = self.host + self.prefix + _end_point.value
        print(url)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers = self.headers) as response:
                print(response.status)
                return await response.json()


async def main():
    x = await GateIO().open_orders()
    print(x)


    """
    # Get Fee for Pair
    # https://github.com/gateio/gateapi-python/blob/master/docs/SpotApi.md#get_fee



    # Get All orders Placed (in case bot restarts) to avoid duplicate orders
    # https://github.com/gateio/gateapi-python/blob/master/docs/SpotApi.md#list_all_open_orders



    # Place Batch Orders When Bot Starts
    # https://github.com/gateio/gateapi-python/blob/master/docs/SpotApi.md#create_batch_orders 



    # Place an Order If tp is hit On one or more orders 
    # https://github.com/gateio/gateapi-python/blob/master/docs/SpotApi.md#create_order



    # Place TP for an order as soon as Order is hit 
    # https://github.com/gateio/gateapi-python/blob/master/docs/SpotApi.md#create_order



    # Spot Account Boot get histry of ticker balances
    # https://github.com/gateio/gateapi-python/blob/master/docs/SpotAccountBook.md

    """
