"""
Data Ingestion Module for Kisan Setu.
Provides integration with Government of India data.gov.in APIs:
- API #1: Current Daily Price (Resource ID: 9ef84268-d588-465a-a308-a864a43d0070)
- API #2: Variety-wise Daily Market Prices (Resource ID: 35985678-0d79-46b4-9ed6-6f13308a1d24)
"""

from data_ingestion.data_gov_api import (
    DataGovAPIClient,
    get_current_daily_prices,
    get_variety_wise_prices,
)
from data_ingestion.market_data import (
    clean_market_data,
    get_latest_market_price,
    get_market_prices,
    get_live_mandi_pulse_items,
    get_live_price_chits,
    get_market_floor_telemetry,
    calculate_demand_signal,
    generate_setu_intelligence_signal,
    get_mandi_data_status,
    clear_mandi_cache,
)

# Alias for compatibility
fetch_market_data = get_market_prices

__all__ = [
    "DataGovAPIClient",
    "get_current_daily_prices",
    "get_variety_wise_prices",
    "clean_market_data",
    "get_latest_market_price",
    "get_market_prices",
    "fetch_market_data",
    "get_live_mandi_pulse_items",
    "get_live_price_chits",
    "get_market_floor_telemetry",
    "calculate_demand_signal",
    "generate_setu_intelligence_signal",
    "get_mandi_data_status",
    "clear_mandi_cache",
]
