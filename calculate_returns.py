from typing import Any, List, Tuple, Iterator, Optional, Generic, TypeVar

# Internal Imports 
from grid_line_machine import GridLineManager, GridLine
# from exchanges.gateio import simulate_price_movment_in_markets
from exchanges.test import simulate_price_movment_in_markets


# @Dev do Test on Inj around 40 consolidation
TP = 0.1  # TP is % between 0-1 (i.e o == 0%, 1 == 100%)
UNITS = 50 # Total number of units traded per ticker
RETAIN_UNITS = .1 * UNITS # total units to retain after tp (don't sell all)
EXCHANGE_FEE = 0.001  # Exchnage fee in percentage 0.01% == 0.01


class Profit:  # Keeps Track of all the Trades pnl
    def __init__(self):
        """
        _init_price : price where bot was started or price where first entry should be
        """
        Profit.list_of_pending_tps = [] # Later could be used to keep track of all the grids with active orders and another list for pending order
        Profit.total_units_left = 0
        Profit.profit: float = 0.0
        Profit.fee = 0.0
        Profit.total_trades_executed = 0

    @classmethod
    def fill_order(cls, grid : GridLine) -> bool:

        # @Dev Make Units dynamic with a class lvl fixed that can be set during class instantiation
        grid.in_trade = True
        cls.total_units_left += UNITS
        cls.fee += grid.price * UNITS * EXCHANGE_FEE
        cls.total_trades_executed += 1
        if grid.last_grid_line is not None and grid.last_grid_line.in_trade:
            cls.fill_tp(grid.last_grid_line)

        return True

        # @Dev Update the _grid with it it has a pending order lots bought/sold at that grid lvl 

    @classmethod
    def fill_tp(cls, grid:GridLine):
        # Since this is only DCA bot profit can only be taken on buys hence grid.last_grid_line
        # is passed in as parameter
        grid.in_trade = False
        profit:float = (UNITS - RETAIN_UNITS) * (grid.next_grid_line.price - grid.price) * TP 
        Profit.profit += profit
        Profit.total_units_left -= UNITS - RETAIN_UNITS

        cls.p(grid.next_grid_line)

    @classmethod
    def p(cls, _grid :GridLine):
        print(f"""profit : {round(cls.profit,3)}\tfee : {round(cls.fee,3)}\tUnitsLeft : {cls.total_units_left}\ttotal trades : {cls.total_trades_executed}\tatGrid : {_grid.name}\tHoldingValue : {round(_grid.price * cls.total_units_left,3)}""")




def move_price(): # Price Tracker 
    # Create TEMP Variables for testing
    # grid start price is mid point for grid
    _grid_start_price = 0.21380

    # The smallest price movment underlaying asset is capable of / pip
    _decimals = 5

    # Total GridLines to lay on canvas
    number_of_grid_lines = 5

    # Get Price from csv for now
    price_movment = simulate_price_movment_in_markets()
    last_price = 0.1700# set this equal to market price

    # Create Grid Lines
    grid_lines = GridLineManager(_grid_start_price,TP,number_of_grid_lines, _decimals)
    for line in grid_lines:
        print(line.name, line.price )

    profit_counter = Profit()
    for current_price in price_movment:
        # Check when price croses a grid line then set last_price as current_price
        for _grid in grid_lines:
            if last_price > _grid.price > current_price and _grid.in_trade is False:
                print(f"last price: {last_price}\tgrid price: {_grid.price}\tcurrentPrice: {current_price}")
                # Price has crossed grid line from above (enter trade @ grid which was crossed)
                profit_counter.fill_order(_grid)

            elif last_price < _grid.price < current_price and _grid.in_trade is False:
                print(f"last price: {last_price}\tgrid price: {_grid.price}\tcurrentPrice: {current_price}")
                # Price has crossed grid line from below (look if there was a tp set)
                profit_counter.fill_order(_grid)

        last_price = current_price


move_price()
