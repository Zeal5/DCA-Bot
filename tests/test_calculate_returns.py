import pytest
import random
from grid_line_machine import GridLineManager, GridLine

_grid_price = [random.uniform(0, 2) for _ in range(100)]
_distance_between_grids = [random.uniform(0, 1) for _ in range(100)]
_number_of_grids_on_each_side = [random.randint(1, 12) for _ in range(100)]
_decimals = [random.randint(1, 10) for _ in range(100)]

param = zip(
    _grid_price, _distance_between_grids, _number_of_grids_on_each_side, _decimals
)


@pytest.fixture(params=list(param))
def setup(request):
    _grid_price = request.param[0]
    _distance_between_grids = request.param[1]
    _number_of_grids_on_each_side = request.param[2]
    _decimals = request.param[3]

    param_dict = {
        "_grid_price": round(_grid_price, _decimals),
        "_distance_between_grids": round(_distance_between_grids, 3),
        "_number_of_grids_on_each_side": _number_of_grids_on_each_side,
        "_decimals": _decimals,
    }

    grid_line_manager = GridLineManager(
        _grid_price,
        _distance_between_grids,
        _number_of_grids_on_each_side,
        _decimals,
    )
    return grid_line_manager, param_dict


def test_grid_numbers(setup):
    print(setup[1]["_grid_price"])
    assert (
        setup[1]["_number_of_grids_on_each_side"]
        == setup[0].grids_on_each_side_of_grid_start_price
    )


def test_round_price_to(setup):
    assert setup[0].round_price_to == setup[1]["_decimals"]


def test_in_region(setup):  # @Dev To be implemented later
    assert setup[0].in_region == ()


# @Dev To be changed Later if distance between each grid is no longer eequal to
# tp for orders on each grid line
def test_tp(setup):
    assert setup[0].tp == setup[1]["_distance_between_grids"]


def test_central_grid_price(setup):
    assert setup[1]["_grid_price"] == setup[0].central_grid_price


### tests for methods of the class
def test_calculate_grid_lines(setup):
    # Check total grid lines created
    grid_lines = setup[0].grid_lines
    assert len(grid_lines) == setup[0].grids_on_each_side_of_grid_start_price * 2 + 1

    # Check grid lines is sorted
    assert sorted(grid_lines) == grid_lines

    # check Distance between each grid line
    # Since Distance is non linear i.e Geomatric the % differance becomes
    # wider as price tends to increase and distance tends to decrease as price
    # decreases i.e 10% of 100 is 110 and 10% of 1 is 1.1 hence Geomatric growth
    # ocurs for price above mid grid (grids are always odds in number
    central_grid_index = len(grid_lines) // 2
    central_grid_price = grid_lines[central_grid_index]

    grids_above_mid_point = grid_lines[central_grid_index:]
    # sort the grid prices below current grid for % percision
    starting_grid_price = grid_lines[central_grid_index]
    _decimal = 0.01

    for grid_price in grids_above_mid_point[1:]:
        assert round(
            (
                starting_grid_price * setup[1]["_distance_between_grids"]
                + starting_grid_price
            ),
            setup[1]["_decimals"],
        ) == pytest.approx(grid_price, _decimal)
        starting_grid_price = grid_price

    grids_below_mid_point = sorted(grid_lines[:central_grid_index], reverse=True)
    starting_grid_price = grids_below_mid_point[0]
    for grid_price in grids_below_mid_point[1:]:
        print(starting_grid_price)
        print(grids_below_mid_point)
        print(grid_price)
        assert round(
            (
                starting_grid_price
                - (starting_grid_price * setup[1]["_distance_between_grids"])
            ),
            setup[1]["_decimals"],
        ) == pytest.approx(grid_price, _decimal)
        starting_grid_price = grid_price

def test_grid_line_objects(setup):
    # Should always return GridLine object
    grid_line_obj_list = setup[0].grid_lines_as_objects

    for grid_obj in grid_line_obj_list:
        assert type(grid_obj) == GridLine





