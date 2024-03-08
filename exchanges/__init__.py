from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional

from typing import Literal
from enum import Enum
import os

load_dotenv()

GATEIO_KEY = os.environ.get("GATEIO_KEY")
GATEIO_SECRET = os.environ.get("GATEIO_SECRET")


@dataclass
class OrderToBePlaced:
    """Order to be passed to Exchanges

    `price :` price of asset `central grid price`
    `cost :`  units * `price` == cost
    `do_not_buy_above_price` & `do_not_buy_below_price`

    high and low ends of grids will be passed to
    GridLine:do_not_buy_below_price
    GridLine:do_not_buy_above_price and
    """

    currency_pair:str
    price: float
    amount:float
    side: Literal["buy", "sell"]
    do_not_buy_above_price: Optional[float] = None
    do_not_buy_below_price: Optional[float] = None


@dataclass
class PlacedOrders:
    """Order to be returned From Exchanges"""
    price: float
    tokens: float
    order_id: int
    create_time: int
    currency_pair: str
    side: Literal["buy", "sell"]
    success: bool
    label : Optional[str] = None
