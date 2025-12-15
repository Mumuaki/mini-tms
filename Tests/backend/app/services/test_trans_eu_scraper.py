
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.trans_eu import TransEuScraper

@pytest.mark.asyncio
async def test_scraper_search_flow():
    # Mock Page object
    mock_page = AsyncMock()
    mock_page.url = "https://platform.trans.eu/exchange/offers"
    
    # Initialize scraper
    scraper = TransEuScraper(mock_page)
    
    # Mock data parsing result
    mock_page.evaluate.return_value = [
        {"trans_id": "123", "loading_place": "Berlin", "price_original": "100 EUR"}
    ]
    
    # Run search with filters
    filters = {"origin": "Berlin", "destination": "Paris"}
    results = await scraper.search_freights(filters)
    
    # Verifications
    mock_page.get_by_text.assert_any_call("Загрузка", exact=True)
    assert len(results) == 1
    assert results[0]["trans_id"] == "123"

@pytest.mark.asyncio
async def test_set_location_logic():
    mock_page = AsyncMock()
    scraper = TransEuScraper(mock_page)
    
    # Setup mocks for location setting flow
    mock_label = MagicMock()
    mock_page.get_by_text.return_value.first = mock_label
    
    mock_input = AsyncMock()
    mock_label.locator.return_value.locator.return_value.locator.return_value.first = mock_input
    mock_input.count.return_value = 1
    
    # Execute
    await scraper._set_location("Загрузка", "Berlin")
    
    # Prepare checking call args
    mock_page.get_by_text.assert_called_with("Загрузка", exact=True)
    # Ensure input was clicked
    assert mock_input.click.called
