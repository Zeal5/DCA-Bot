from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional

import os
load_dotenv()

GATEIO_KEY = os.environ.get("GATEIO_KEY")
GATEIO_SECRET = os.environ.get("GATEIO_SECRET")


@dataclass 
class Order:
    """Order to be passed to Exchanges

    `price :` price of asset `central grid price`
    `cost :`  units * `price` == cost 
    `do_not_buy_above_price` & `do_not_buy_below_price` 

    high and low ends of grids will be passed to
    GridLine:do_not_buy_below_price
    GridLine:do_not_buy_above_price and 
    """

    price: float
    cost : float
    do_not_buy_above_price: Optional[float] = None
    do_not_buy_below_price: Optional[float] = None






