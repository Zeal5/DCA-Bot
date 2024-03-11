import asyncio

# Internal Imports
from grid_line_machine import GridLineManager
from exchanges.gateio import GateIOConnector



async def move_price():  # Price Tracker
    cpool = GridLineManager(
        _central_grid_price=0.15350,
        _distance_between_grids=0.1,
        _ticker="CPOOL_USDT",
        _usd_amount_to_buy_with=11,
        _number_of_grids_on_each_side_of_grid_start_price=10,
        _do_not_buy_above_this_price = 0.25,
        _do_not_buy_below_this_price = 0.1,
        _round_prices_to=5,
    )
    vanry = GridLineManager(
        _central_grid_price=0.19700,
        _distance_between_grids=0.1,
        _ticker="VANRY_USDT",
        _usd_amount_to_buy_with=11,
        _number_of_grids_on_each_side_of_grid_start_price=10,
        _do_not_buy_above_this_price = 0.3,
        _do_not_buy_below_this_price = 0.13,
        _round_prices_to=5,
    )
    x = GateIOConnector(vanry,cpool)
    
    await x.entry_point()


if __name__ == "__main__":
    asyncio.run(move_price())
