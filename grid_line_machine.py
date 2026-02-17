# Standard Library Imports
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
import logging

logging.basicConfig(
    filename='DCALOGS.log',
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
# Third Party Imports
from typing import List, Tuple, Optional, Generic, TypeVar


T = TypeVar("T")
@dataclass
class GridLine(Generic[T]):
    # Grid Info
    name: str
    price: float
    order_id : int = 0
    last_grid_line: Optional[GridLine[T]] = None
    next_grid_line: Optional[GridLine[T]] = None
    # Grid stats
    total_buy_orders: int = 0
    total_sell_orders: int = 0
    total_cost : float = 0
    total_tokens : float = 0
    total_fee : float = 0
    # Grid order status
    buy_order_placed : Optional[bool] = False
    sell_order_placed : Optional[bool] = False
    buy_order_filled: Optional[bool] = False
    sell_order_filled: Optional[bool] = False

    def buy_order_success(self, _order_id:int):
        self.buy_order_placed = True
        self.order_id = _order_id
        self.ppp("Buy Order Placed")

    def sell_order_success(self, _order_id:int):
        self.sell_order_placed = True
        self.order_id = _order_id
        self.ppp("Sell Order Placed")
    
    def buy_order_triggerd(self,_amount:float):
        self.buy_order_filled = True
        self.buy_order_placed = False
        self.total_buy_orders += 1
        self.total_tokens += float(_amount)
        self.total_cost = self.price * self.total_tokens
        self.order_id = 0
        self.ppp("Buy Order Triggerd")

    def sell_order_triggerd(self,_amount: float):
        self.sell_order_filled = True
        self.sell_order_placed = False
        self.total_sell_orders += 1
        self.total_tokens -= float(_amount)
        self.total_cost = self.price * self.total_tokens
        self.last_grid_line.buy_order_filled = False
        self.order_id = 0
        self.ppp("Sell Order Triggerd")

    def ppp(self,_action:str):
        logging.info(f"{self.name} {_action}")
        print(f"{self.name} {_action}")
        logging.info(self.__repr__())

    def __str__(self):
        return f"""
    {self.name:>10} {self.price:>10} {self.order_id:>10} 
    cost:{self.total_cost:>10} tokens:{self.total_tokens:>10} fee:{self.total_fee:>10}
    buy:{self.total_buy_orders} sells:{self.total_sell_orders:>10}
    BOP:{self.buy_order_placed} BOF:{self.buy_order_filled}
    SOP:{self.sell_order_placed} SOF:{self.sell_order_filled}"""

    def __repr__(self):

        if self.next_grid_line is None and self.last_grid_line is not None:
            return f"name: {self.name}\nprice: {self.price}\nlast_grid_line: {self.last_grid_line.name}\nnext_grid_line: {None}\nbuyOrder :{self.buy_order_placed}\nOrderID : {self.order_id}\n"

        elif self.last_grid_line is None and self.next_grid_line is not None:
            return f"name: {self.name}\nprice: {self.price}\nlast_grid_line: {None}\nnext_grid_line: {self.next_grid_line.name}\nbuyOrder :{self.buy_order_placed}\nOrderID : {self.order_id}\n"

        elif self.last_grid_line is not None and self.next_grid_line is not None:
            return f"""
    {self.last_grid_line.__str__()} 
    {self.__str__()}
    {self.next_grid_line.__str__()}
    """


            # return f"name: {self.name}\nprice: {self.price}\nlast_grid_line: {self.last_grid_line.name}\nnext_grid_line: {self.next_grid_line.name}\nbuyOrder :{self.buy_order_placed}\nOrderID : {self.order_id}\n"
        else:
            return f"Something Went Wrong"

class GridLineManager:  # Calculate Grid Lines and keeps track of between which grids price currently is
    def __init__(
        self,
        _central_grid_price: float,
        _distance_between_grids: float,
        _ticker:str,
        _usd_amount_to_buy_with:float,
        _number_of_grids_on_each_side_of_grid_start_price: int,
        _do_not_buy_above_this_price,
        _do_not_buy_below_this_price,
        _round_prices_to: int  ,
    ):
        """Given a _grid_start_price (x) will generate grids with
        (_number_of_grids_on_each_side_of_grid_start_price)
        on both sides of grid start price

        _grid_start_price: price where to center grid around
        _distance_between_grids: Distance between each grid in percentage i.e (0.1 == 10%)
        _round_prices_to: how many decimals the price of ticker is"""

        # Total usd to spend per grid
        self.usd_to_buy_with = _usd_amount_to_buy_with
        self.in_region = (
            tuple()
        )  # Points to which region price(0.104) currently is Region.region(0.103, 0.106) @Dev not used anywhere yet

        self.ticker = _ticker
        self.round_price_to = _round_prices_to
        self.tp = round(_distance_between_grids, 3)
        self.grids_on_each_side_of_grid_start_price = (
            _number_of_grids_on_each_side_of_grid_start_price
        )
        self.central_grid_price = round(_central_grid_price, _round_prices_to)

        # First calculate grid lines list bcz it is used by create grid line objects
        self.grid_lines = self.calculate_grid_lines()

        self.grid_lines_as_objects = self.create_grid_line_objects()
        self.current_grid_line_number = 0
        # self.max_number_of_grid_lines = 11
        self.do_not_buy_above_price: float = _do_not_buy_above_this_price
        self.do_not_buy_below_price: float = _do_not_buy_below_this_price
        if _do_not_buy_below_this_price >= _do_not_buy_above_this_price:
            raise ValueError("do not buy below this price is > do not buy above this price")

    def __iter__(self):
        self.current_grid_line_number = -1
        return self

    def __next__(self):
        self.current_grid_line_number += 1
        if self.current_grid_line_number < len(self.grid_lines_as_objects):
            return self.grid_lines_as_objects[self.current_grid_line_number]

        raise StopIteration

    def __getitem__(self, index):
        if index < len(self.grid_lines_as_objects):
            return self.grid_lines_as_objects[index]
        raise IndexError("Index out of range")
        
    # @DEV for testing now
    def grid_line_obj_map_price(self,_price:float)->GridLine:
        for _grid in self.grid_lines_as_objects:
            if _grid.price == float(_price) :
                return _grid


    def calculate_grid_lines(self) -> List[float]:
        """
        _grid_start_price : First price where grid should start spanning above
                            and below as in mid point for grid i.e central_grid_price
        """

        _grid_start_price = self.central_grid_price
        grid_lines: List[float] = [_grid_start_price]
        _number_of_gridlines_on_each_side = self.grids_on_each_side_of_grid_start_price

        # Grid line above mp
        _next_line_price = _grid_start_price
        # Grid line below mp
        _last_line_price = _grid_start_price

        # 5 grid lines above current mp
        for _ in range(_number_of_gridlines_on_each_side):
            _next_line_price = round(
                _next_line_price + (_next_line_price * self.tp), self.round_price_to
            )
            grid_lines.append(_next_line_price)

        # 5 grid lines below current mp
        for _ in range(_number_of_gridlines_on_each_side):
            _last_line_price = round(
                _last_line_price - (_last_line_price * self.tp), self.round_price_to
            )
            grid_lines.append(_last_line_price)

        grid_lines.sort()
        return grid_lines

    def create_grid_line_objects(self) -> List[GridLine]:
        grid_lines = self.grid_lines
        grid_lines_obj_list: List[GridLine] = []

        for index, grid_line in enumerate(grid_lines, start=1):
            current_grid_line = GridLine(
                name=f"grid_line_{index}",  # here last grid line is first grid line
                price=grid_line,
            )
            grid_lines_obj_list.append(current_grid_line)

        # next Grid Line above current grid line  3
        # current Grid Line current grid line     2
        # last Grid Line below current grid line  1

        # add next/last properties to grid line objects making them a linked list with referances
        # to last and next grid lines
        for index, grid_line_obj in enumerate(grid_lines_obj_list):

            try:
                next_grid_line = grid_lines_obj_list[index + 1]
            except IndexError as e:
                next_grid_line = None

            current_grid_line = grid_line_obj
            last_grid_line = grid_lines_obj_list[index - 1] if index > 0 else None

            current_grid_line.next_grid_line = next_grid_line
            current_grid_line.last_grid_line = last_grid_line

        return grid_lines_obj_list

    @lru_cache
    def get_region(self, market_price: float) -> Tuple[float, float]:
        """
        For Later Use when Implement Dynamic Grids Which have Ability to Move with
        prices @Dev not used anywhere for now
        Returns (lower grid, upper grid)
        market_price : current mp
        """

        grid_lines = self.grid_lines
        # generates a list[(grid_lines, disctance)]
        distances = list(
            zip(
                grid_lines,
                map(
                    lambda _x: round(abs(market_price - _x), self.round_price_to),
                    grid_lines,
                ),
            )
        )
        # Sort list based on distances @Dev lines are sorted based on distances,
        # lower distance to mp doesn't
        # equate to grid lines is lower then mp
        distances.sort(key=lambda _x: _x[1])
        lower_grid = distances[0][0]
        upper_grid = distances[1][0]

        if lower_grid > upper_grid:
            return upper_grid, lower_grid

        return lower_grid, upper_grid
