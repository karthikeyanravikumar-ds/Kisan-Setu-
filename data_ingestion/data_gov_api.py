"""
data.gov.in API Client | Kisan Setu
Connects to both Government of India Open Government Data (OGD) Mandi APIs:
1. Current Daily Price of Various Commodities from Various Markets (Mandi)
   Resource ID: 9ef84268-d588-465a-a308-a864a43d0070
2. Variety-wise Daily Market Prices Data of Commodity
   Resource ID: 35985678-0d79-46b4-9ed6-6f13308a1d24
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import requests
import pandas as pd
from dotenv import load_dotenv, find_dotenv

# Ensure environment variables are loaded
load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)

# Resource IDs
RESOURCE_CURRENT_DAILY = "9ef84268-d588-465a-a308-a864a43d0070"
RESOURCE_VARIETY_WISE = "35985678-0d79-46b4-9ed6-6f13308a1d24"

URL_CURRENT_DAILY = f"https://api.data.gov.in/resource/{RESOURCE_CURRENT_DAILY}"
URL_VARIETY_WISE = f"https://api.data.gov.in/resource/{RESOURCE_VARIETY_WISE}"

DEFAULT_TIMEOUT = 25  # seconds
RAW_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


class DataGovAPIClient:
    """
    Client for Government of India data.gov.in Mandi APIs.
    Reads API key securely from environment variable 'DATA_GOV_API_KEY'.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        if api_key is not None:
            self._api_key = api_key
        else:
            self._api_key = os.getenv("DATA_GOV_API_KEY")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Kisan-Setu-Platform/2.0 (Agri-Market-Telemetry)",
            "Accept": "application/json",
        })

    @property
    def has_api_key(self) -> bool:
        """Check if an API key is configured."""
        return bool(self._api_key and str(self._api_key).strip())

    def get_api_key_masked(self) -> str:
        """Return masked API key for diagnostic logging without exposing secret."""
        if not self.has_api_key:
            return "<NOT CONFIGURED>"
        key = str(self._api_key).strip()
        if len(key) <= 8:
            return "***"
        return f"{key[:4]}...{key[-4:]}"

    def _execute_query(
        self,
        endpoint_url: str,
        resource_label: str,
        params: Dict[str, Any],
        save_raw: bool = True,
        raw_slug: str = "general",
    ) -> Dict[str, Any]:
        """Internal executor handling HTTP errors, timeouts, and logging safely."""
        if not self.has_api_key:
            return {
                "status": "error",
                "total": 0,
                "count": 0,
                "records": [],
                "error_message": "DATA_GOV_API_KEY environment variable is missing or empty.",
                "retrieval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        # Secure copy of parameters including API key
        query_params = dict(params)
        query_params["api-key"] = self._api_key
        query_params["format"] = "json"

        try:
            response = self.session.get(endpoint_url, params=query_params, timeout=self.timeout)

            if response.status_code == 400:
                logger.warning(f"data.gov.in {resource_label} returned HTTP 400 (Bad Request).")
                return {
                    "status": "error",
                    "total": 0,
                    "count": 0,
                    "records": [],
                    "error_message": f"Bad request query on {resource_label} (HTTP 400).",
                    "retrieval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

            if response.status_code == 403:
                logger.warning(f"data.gov.in {resource_label} returned HTTP 403 (Forbidden).")
                return {
                    "status": "error",
                    "total": 0,
                    "count": 0,
                    "records": [],
                    "error_message": f"Access forbidden on {resource_label} (HTTP 403). Check API key.",
                    "retrieval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

            if response.status_code == 429:
                logger.warning(f"data.gov.in {resource_label} rate limit reached (HTTP 429).")
                return {
                    "status": "error",
                    "total": 0,
                    "count": 0,
                    "records": [],
                    "error_message": "data.gov.in rate limit reached. Using local cache.",
                    "retrieval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

            if response.status_code >= 500:
                logger.warning(f"data.gov.in server error (HTTP {response.status_code}).")
                return {
                    "status": "error",
                    "total": 0,
                    "count": 0,
                    "records": [],
                    "error_message": f"data.gov.in server error (HTTP {response.status_code}).",
                    "retrieval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

            response.raise_for_status()
            data = response.json()
            records = data.get("records", [])
            total = int(data.get("total", len(records)))
            count = int(data.get("count", len(records)))

            result = {
                "status": "success",
                "total": total,
                "count": count,
                "limit": params.get("limit", 100),
                "offset": params.get("offset", 0),
                "records": records,
                "error_message": None,
                "retrieval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            if save_raw and records:
                self._save_raw_response(result, f"{resource_label}_{raw_slug}")

            return result

        except requests.exceptions.Timeout:
            logger.warning(f"data.gov.in {resource_label} timed out after {self.timeout}s.")
            return {
                "status": "error",
                "total": 0,
                "count": 0,
                "records": [],
                "error_message": f"Connection to data.gov.in timed out after {self.timeout}s.",
                "retrieval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except requests.exceptions.ConnectionError:
            logger.warning(f"data.gov.in {resource_label} connection failed.")
            return {
                "status": "error",
                "total": 0,
                "count": 0,
                "records": [],
                "error_message": "Network connection error reaching data.gov.in.",
                "retrieval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except Exception as e:
            logger.error(f"Unexpected error querying {resource_label}: {type(e).__name__}")
            return {
                "status": "error",
                "total": 0,
                "count": 0,
                "records": [],
                "error_message": f"Unexpected error: {type(e).__name__}",
                "retrieval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

    def fetch_current_daily_prices(
        self,
        state: Optional[str] = "Maharashtra",
        district: Optional[str] = None,
        market: Optional[str] = None,
        commodity: Optional[str] = None,
        variety: Optional[str] = None,
        grade: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        API #1: Current Daily Price of Various Commodities from Various Markets (Mandi).
        Endpoint: https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070
        """
        params: Dict[str, Any] = {
            "limit": max(1, min(int(limit), 10000)),
            "offset": max(0, int(offset)),
        }

        if state:
            params["filters[state.keyword]"] = str(state).strip()
        if district:
            params["filters[district]"] = str(district).strip()
        if market:
            params["filters[market]"] = str(market).strip()
        if commodity:
            params["filters[commodity]"] = str(commodity).strip()
        if variety:
            params["filters[variety]"] = str(variety).strip()
        if grade:
            params["filters[grade]"] = str(grade).strip()

        slug = "_".join(s.lower().replace(" ", "_") for s in [state, district, commodity] if s) or "all"
        return self._execute_query(URL_CURRENT_DAILY, "current_daily", params, save_raw=True, raw_slug=slug)

    def fetch_variety_wise_prices(
        self,
        state: Optional[str] = "Maharashtra",
        district: Optional[str] = None,
        commodity: Optional[str] = None,
        arrival_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        API #2: Variety-wise Daily Market Prices Data of Commodity.
        Endpoint: https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24
        """
        params: Dict[str, Any] = {
            "limit": max(1, min(int(limit), 10000)),
            "offset": max(0, int(offset)),
        }

        if state:
            params["filters[State]"] = str(state).strip()
        if district:
            params["filters[District]"] = str(district).strip()
        if commodity:
            params["filters[Commodity]"] = str(commodity).strip()
        if arrival_date:
            params["filters[Arrival_Date]"] = str(arrival_date).strip()

        slug = "_".join(s.lower().replace(" ", "_") for s in [state, district, commodity] if s) or "all"
        return self._execute_query(URL_VARIETY_WISE, "variety_wise", params, save_raw=True, raw_slug=slug)

    def _save_raw_response(self, data: Dict[str, Any], slug: str) -> None:
        """Save raw JSON payload to data/raw/ without API credentials."""
        try:
            RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
            target_file = RAW_DATA_DIR / f"raw_{slug}.json"
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Could not write raw API cache: {e}")


# ------------------------------------------------------------
# STREAMLIT-COMPATIBLE CACHED FUNCTION WRAPPERS (TTL = 15 MIN)
# ------------------------------------------------------------

try:
    import streamlit as st

    @st.cache_data(ttl=900, show_spinner=False)
    def get_current_daily_prices(
        state: Optional[str] = "Maharashtra",
        district: Optional[str] = None,
        market: Optional[str] = None,
        commodity: Optional[str] = None,
        variety: Optional[str] = None,
        grade: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Streamlit-cached getter for API #1 (Current Daily Price)."""
        client = DataGovAPIClient()
        return client.fetch_current_daily_prices(
            state=state,
            district=district,
            market=market,
            commodity=commodity,
            variety=variety,
            grade=grade,
            limit=limit,
            offset=offset,
        )

    @st.cache_data(ttl=900, show_spinner=False)
    def get_variety_wise_prices(
        state: Optional[str] = "Maharashtra",
        district: Optional[str] = None,
        commodity: Optional[str] = None,
        arrival_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Streamlit-cached getter for API #2 (Variety-wise Daily Market Prices)."""
        client = DataGovAPIClient()
        return client.fetch_variety_wise_prices(
            state=state,
            district=district,
            commodity=commodity,
            arrival_date=arrival_date,
            limit=limit,
            offset=offset,
        )

except ImportError:
    # Standalone execution fallback
    def get_current_daily_prices(
        state: Optional[str] = "Maharashtra",
        district: Optional[str] = None,
        market: Optional[str] = None,
        commodity: Optional[str] = None,
        variety: Optional[str] = None,
        grade: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        client = DataGovAPIClient()
        return client.fetch_current_daily_prices(
            state=state,
            district=district,
            market=market,
            commodity=commodity,
            variety=variety,
            grade=grade,
            limit=limit,
            offset=offset,
        )

    def get_variety_wise_prices(
        state: Optional[str] = "Maharashtra",
        district: Optional[str] = None,
        commodity: Optional[str] = None,
        arrival_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        client = DataGovAPIClient()
        return client.fetch_variety_wise_prices(
            state=state,
            district=district,
            commodity=commodity,
            arrival_date=arrival_date,
            limit=limit,
            offset=offset,
        )
