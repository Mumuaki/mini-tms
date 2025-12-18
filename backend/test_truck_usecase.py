import pytest
from unittest.mock import MagicMock
from app.use_cases.truck_use_cases import TruckUseCase


def test_activate_truck_not_found():
    repo = MagicMock()
    repo.get_by_id.return_value = None
    use_case = TruckUseCase(repo)

    with pytest.raises(ValueError):
        use_case.activate_truck(5)


def test_update_truck_location_validates_coords():
    repo = MagicMock()
    truck = MagicMock()
    repo.get_by_id.return_value = truck
    repo.update_gps.return_value = truck
    use_case = TruckUseCase(repo)

    # invalid latitude
    with pytest.raises(ValueError):
        use_case.update_truck_location(1, 999, 10, "X")

    # invalid longitude
    with pytest.raises(ValueError):
        use_case.update_truck_location(1, 10, 999, "X")

    # valid
    result = use_case.update_truck_location(1, 10.0, 20.0, "Test")
    repo.update_gps.assert_called_once()
    assert result is truck
