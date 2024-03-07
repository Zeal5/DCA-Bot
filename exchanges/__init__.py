from dataclasses import dataclass
from typing import Optional



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






