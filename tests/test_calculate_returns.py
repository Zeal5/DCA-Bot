import pytest
import random

from grid_line_machine import GridLineManager, GridLine

param = zip(list(range(100)),[random.uniform(0, 10) for _ in range(100)],[random.randint(5,15) for i in range(100)])

@pytest.fixture(params=list(range(2)))
def setup(request):
    _grid_price = 5
    _distance_between_grids = 0.1  # 10%
    _number_of_grids_on_each_side = 11
    _decimals = 3
    return GridLineManager(
        _grid_price,
        _distance_between_grids,
        _number_of_grids_on_each_side,
        _decimals,
    )

def test_grid_numbers(setup):
    print(setup._grid_price)
    assert (
    11
    == setup.grids_on_each_side_of_grid_start_price
    )
def test_round_price_to(setup):
    assert setup.round_price_to == 3

def test_in_region(setup):  # @Dev To be implemented later
    assert setup.in_region == ()

def test_tp(setup):  # @Dev To be changed Later if distance between each grid is no longer eequal to tp for orders on each grid line
    assert setup.tp == 0.1

def test_central_grid_price(setup):
    assert 5== setup.central_grid_price

### tests for methods of the class
def test_calculate_grid_lines(setup):
    #Check total grid lines created
    grid_lines = setup.grid_lines
    assert len(grid_lines) == setup.grids_on_each_side_of_grid_start_price * 2 + 1

    # Check grid lines is sorted
    assert(sorted(grid_lines) == grid_lines)

    # check Distance between each grid line






"""
setup.grid_lines = self.calculate_grid_lines()
setup.grid_lines_as_objects = self.create_grid_line_objects()
"""











