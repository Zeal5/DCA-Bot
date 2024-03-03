# Standard Library Imports
from __future__ import annotations
from dataclasses import dataclass

# Third Party Imports
from typing import Any, List, Tuple, Iterator, Optional, Generic, TypeVar

# Internal Imports


T = TypeVar("T")


@dataclass
class GridLine(Generic[T]):
    name: str
    price: float
    tp: Optional[float] = None
    last_grid_line: Optional[GridLine[T]] = None
    next_grid_line: Optional[GridLine[T]] = None
    in_trade: Optional[bool] = False

    def __repr__(self):

        if self.next_grid_line is None and self.last_grid_line is not None:
            return f"name: {self.name}\nprice: {self.price}\ntp: {self.tp}\nlast_grid_line: {self.last_grid_line.name}\nnext_grid_line: {None}\n"

        elif self.last_grid_line is None and self.next_grid_line is not None:
            return f"name: {self.name}\nprice: {self.price}\ntp: {self.tp}\nlast_grid_line: {None}\nnext_grid_line: {self.next_grid_line.name}\n"

        elif self.last_grid_line is not None and self.next_grid_line is not None:
            return f"name: {self.name}\nprice: {self.price}\ntp: {self.tp}\nlast_grid_line: {self.last_grid_line.name}\nnext_grid_line: {self.next_grid_line.name}\n"
        else:
            return f"Something Went Wrong"


class GridLineManager:  # Calculate Grid Lines and keeps track of between which grids price currently is
    def __init__(
        self,
        _central_grid_price: float,
        _distance_between_grids: float,
        _number_of_grids_on_each_side_of_grid_start_price: int,
        _round_prices_to: int = 4,
    ):
        """Given a _grid_start_price (x) will generate grids with (_number_of_grids_on_each_side_of_grid_start_price) on both sides of grid start price

        _grid_start_price: price where to center grid around
        _distance_between_grids: Distance between each grid in percentage i.e (0.1 == 10%)
        _round_prices_to: how many decimals the price of ticker is"""


        self.in_region = (
            tuple()
        )  # Points to which region price(0.104) currently is Region.region(0.103, 0.106) @Dev not used anywhere yet

        self.round_price_to = _round_prices_to
        self.tp = _distance_between_grids
        self.grids_on_each_side_of_grid_start_price = _number_of_grids_on_each_side_of_grid_start_price
        self.central_grid_price = round(_central_grid_price, _round_prices_to)

        # First calculate grid lines list bcz it is used by create grid line objects
        self.grid_lines = self.calculate_grid_lines()


        self.grid_lines_as_objects = self.create_grid_line_objects()
        self.current_grid_line_number = 0
        # self.max_number_of_grid_lines = 11

    def __iter__(self):
        self.current_grid_line_number = -1
        return self

    def __next__(self):
        self.current_grid_line_number += 1
        if self.current_grid_line_number < len(self.grid_lines_as_objects):
            return self.grid_lines_as_objects[self.current_grid_line_number]

        raise StopIteration

    def calculate_grid_lines(self) -> List[float]:
        """
        _grid_start_price : First price where grid should start spanning above and below as in mid point for grid i.e central_grid_price
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

        # add next/last properties to grid line objects making them a linked list with referances to last and next grid lines
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

    def get_region(self, market_price: float) -> Tuple[float, float]:
        """
        For Later Use when Implement Dynamic Grids Which have Ability to Move with prices @@Dev not used anywhere for now
        Returns (lower grid, upper grid)
        market_price : current mp

        """

        grid_lines = self.grid_lines
        distances = list(
            zip(
                grid_lines,
                map(
                    lambda _x: round(abs(market_price - _x), self.round_price_to),
                    grid_lines,
                ),
            )
        )  # generates a list[(grid_lines, disctance)]
        # Sort list based on distances @Dev lines are sorted based on distances, lower distance to mp doesn't equate to grid lines is lower then mp
        distances.sort(key=lambda _x: _x[1])
        lower_grid = distances[0][0]
        upper_grid = distances[1][0]

        if lower_grid > upper_grid:
            return upper_grid, lower_grid

        return lower_grid, upper_grid
