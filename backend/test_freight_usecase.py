import pytest
from unittest.mock import MagicMock
from app.use_cases.freight_use_cases import FreightUseCase


def test_mark_as_deal_missing_raises():
    repo = MagicMock()
    repo.get_by_id.return_value = None
    use_case = FreightUseCase(repo)

    with pytest.raises(ValueError):
        use_case.mark_as_deal(123)


def test_mark_as_deal_success_calls_update():
    freight = MagicMock()
    freight.is_deal = False
    repo = MagicMock()
    repo.get_by_id.return_value = freight
    repo.update.return_value = freight
    use_case = FreightUseCase(repo)

    result = use_case.mark_as_deal(1)
    repo.update.assert_called_once()
    assert result is freight
