import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def forecast_demand(
    demand_df,
    district,
    crop,
    forecast_days=3
):
    """
    Forecast upcoming demand using historical demand and order activity
    for a selected district and crop.

    Uses LinearRegression as a baseline time-series trend model with order
    momentum features when valid order variance is available.

    Parameters:
        demand_df (pd.DataFrame): Historical demand dataframe containing
                                  date, district, crop, demand_quantity_kg,
                                  and optionally orders.
        district (str): Target district name.
        crop (str): Target crop name.
        forecast_days (int): Number of days to forecast (e.g. 3, 7).

    Returns:
        dict or None: Structured forecast intelligence or None if insufficient data.
    """
    # ---------------------------------------------------------
    # 1. INPUT VALIDATION & SAFE GUARDS
    # ---------------------------------------------------------
    if demand_df is None or not isinstance(demand_df, pd.DataFrame) or demand_df.empty:
        return None

    if not district or not isinstance(district, str) or not district.strip():
        return None

    if not crop or not isinstance(crop, str) or not crop.strip():
        return None

    try:
        forecast_days = int(forecast_days)
        if forecast_days <= 0:
            forecast_days = 3
    except (ValueError, TypeError):
        forecast_days = 3

    # Required columns check
    required_cols = {"date", "district", "crop", "demand_quantity_kg"}
    if not required_cols.issubset(set(demand_df.columns)):
        return None

    # Filter by district and crop (case-insensitive and trimmed)
    clean_df = demand_df.dropna(subset=["district", "crop"]).copy()
    target_district = district.strip().lower()
    target_crop = crop.strip().lower()

    district_mask = clean_df["district"].astype(str).str.strip().str.lower() == target_district
    crop_mask = clean_df["crop"].astype(str).str.strip().str.lower() == target_crop

    data = clean_df[district_mask & crop_mask].copy()
    if data.empty:
        return None

    # Parse and validate dates
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["date"])

    # Parse and validate demand quantity
    data["demand_quantity_kg"] = pd.to_numeric(data["demand_quantity_kg"], errors="coerce")
    data = data.dropna(subset=["demand_quantity_kg"])

    # Ensure minimum 3 valid historical observations
    if len(data) < 3:
        return None

    # ---------------------------------------------------------
    # 2. DATA SORTING & TIME INDEX
    # ---------------------------------------------------------
    data = data.sort_values("date").reset_index(drop=True)
    data["day_index"] = range(len(data))

    # ---------------------------------------------------------
    # 3. FEATURE ENGINEERING & ORDER MOMENTUM
    # ---------------------------------------------------------
    has_valid_orders = False
    order_model = None

    if "orders" in data.columns:
        data["orders"] = pd.to_numeric(data["orders"], errors="coerce")
        # Check if orders column has at least 3 non-null values and meaningful variation
        valid_orders = data["orders"].dropna()
        if len(valid_orders) >= 3 and valid_orders.std() > 0:
            # Impute any single missing order with median if necessary
            data["orders"] = data["orders"].fillna(valid_orders.median())
            has_valid_orders = True

            # Fit order trajectory model over time
            order_model = LinearRegression()
            order_model.fit(data[["day_index"]], data["orders"])

    # ---------------------------------------------------------
    # 4. MODEL TRAINING (LinearRegression Baseline)
    # ---------------------------------------------------------
    y = data["demand_quantity_kg"]
    last_index = int(data["day_index"].max())
    future_indices = [last_index + i for i in range(1, forecast_days + 1)]
    future_day_df = pd.DataFrame({"day_index": future_indices})

    if has_valid_orders and order_model is not None:
        # Predict projected order counts for future days (bounded >= 0)
        proj_orders = np.maximum(0.0, order_model.predict(future_day_df))
        future_X = pd.DataFrame({
            "day_index": future_indices,
            "orders": proj_orders
        })

        X_train = data[["day_index", "orders"]]
        demand_model = LinearRegression()
        demand_model.fit(X_train, y)

        raw_predictions = demand_model.predict(future_X)
        # Calculate fitted slope across the projection horizon
        fitted_slope = float(demand_model.coef_[0] + demand_model.coef_[1] * float(order_model.coef_[0]))
    else:
        X_train = data[["day_index"]]
        demand_model = LinearRegression()
        demand_model.fit(X_train, y)

        future_X = future_day_df
        raw_predictions = demand_model.predict(future_X)
        fitted_slope = float(demand_model.coef_[0])

    # Prevent negative demand and round
    predictions = [max(0.0, round(float(val), 0)) for val in raw_predictions]

    # ---------------------------------------------------------
    # 5. CURRENT DEMAND & FORECAST METRICS
    # ---------------------------------------------------------
    current_demand = float(data.iloc[-1]["demand_quantity_kg"])
    average_forecast = round(float(sum(predictions) / len(predictions)), 0) if predictions else 0.0

    if current_demand > 0:
        percentage_change = round(((average_forecast - current_demand) / current_demand) * 100.0, 1)
    else:
        percentage_change = 0.0

    # ---------------------------------------------------------
    # 6. ADAPTIVE TREND CLASSIFICATION (Scale-Relative)
    # ---------------------------------------------------------
    # Compute baseline scale from mean historical demand
    mean_historical_demand = float(data["demand_quantity_kg"].mean())
    demand_scale = mean_historical_demand if mean_historical_demand > 0 else (current_demand if current_demand > 0 else 1.0)
    relative_slope = fitted_slope / demand_scale

    # A relative slope of +/- 2% daily rate defines meaningful trend direction
    if relative_slope > 0.02:
        trend = "Increasing"
    elif relative_slope < -0.02:
        trend = "Decreasing"
    else:
        trend = "Stable"

    # ---------------------------------------------------------
    # 7. DATA QUALITY & RELIABILITY INDICATOR
    # ---------------------------------------------------------
    history_days = int(data["date"].dt.date.nunique())
    if history_days < 5:
        data_quality = "Limited"
    elif history_days <= 14:
        data_quality = "Moderate"
    else:
        data_quality = "Good"

    # ---------------------------------------------------------
    # 8. EXPLANATION GENERATION
    # ---------------------------------------------------------
    if trend == "Increasing":
        if has_valid_orders:
            explanation = (
                f"Demand is increasing by {percentage_change:+0.1f}% over the next {forecast_days} days "
                f"based on recent historical demand and order activity ({history_days} days history, {data_quality} quality)."
            )
        else:
            explanation = (
                f"Demand is increasing by {percentage_change:+0.1f}% over the next {forecast_days} days "
                f"based on upward historical demand trend ({history_days} days history, {data_quality} quality)."
            )
    elif trend == "Decreasing":
        if has_valid_orders:
            explanation = (
                f"Demand is decreasing by {abs(percentage_change):0.1f}% over the next {forecast_days} days "
                f"reflecting recent downward demand and order activity ({history_days} days history, {data_quality} quality)."
            )
        else:
            explanation = (
                f"Demand is decreasing by {abs(percentage_change):0.1f}% over the next {forecast_days} days "
                f"based on downward historical demand trend ({history_days} days history, {data_quality} quality)."
            )
    else:
        explanation = (
            f"Demand remains stable with a {percentage_change:+0.1f}% variance across the next {forecast_days} days "
            f"({history_days} days history, {data_quality} quality)."
        )

    # ---------------------------------------------------------
    # 9. RESULT COMPOSITION
    # ---------------------------------------------------------
    return {
        "district": district,
        "crop": crop,
        "current_demand_kg": round(current_demand, 0),
        "forecast_demand_kg": average_forecast,
        "forecast_values": predictions,
        "trend": trend,
        "percentage_change": percentage_change,
        "historical_data": data,
        "history_days": history_days,
        "data_quality": data_quality,
        "explanation": explanation
    }


def forecast_demand_with_market_context(
    demand_df,
    district,
    crop,
    forecast_days=3,
    market_prices_df=None
):
    """
    Forecast demand with optional market price context integration.
    Preserves model independence while enriching the intelligence payload
    with live or historical APMC Mandi price context when available.

    Parameters:
        demand_df (pd.DataFrame): Historical demand dataframe.
        district (str): Target district name.
        crop (str): Target crop name.
        forecast_days (int): Number of days to forecast.
        market_prices_df (pd.DataFrame, optional): Mandi market prices dataset.

    Returns:
        dict or None: Forecast result enriched with market_price_context.
    """
    result = forecast_demand(
        demand_df=demand_df,
        district=district,
        crop=crop,
        forecast_days=forecast_days
    )

    if result is None:
        return None

    # Attach market price context if available
    if market_prices_df is not None and isinstance(market_prices_df, pd.DataFrame) and not market_prices_df.empty:
        # Detect commodity column name
        m_col = None
        for candidate in ["commodity", "crop", "Commodity", "Crop"]:
            if candidate in market_prices_df.columns:
                m_col = candidate
                break

        if m_col is not None:
            target_crop_clean = crop.strip().lower()
            crop_prices = market_prices_df[
                market_prices_df[m_col].astype(str).str.strip().str.lower() == target_crop_clean
            ]

            if not crop_prices.empty:
                latest_row = crop_prices.iloc[-1]
                modal_val = None

                # 1. Prioritize normalized modal_price_per_kg (already ₹/kg, DO NOT divide by 100)
                if "modal_price_per_kg" in latest_row.index and pd.notna(latest_row["modal_price_per_kg"]):
                    try:
                        modal_val = float(latest_row["modal_price_per_kg"])
                    except (ValueError, TypeError):
                        pass
                elif "Modal_Price_Per_Kg" in latest_row.index and pd.notna(latest_row["Modal_Price_Per_Kg"]):
                    try:
                        modal_val = float(latest_row["Modal_Price_Per_Kg"])
                    except (ValueError, TypeError):
                        pass

                # 2. Fallback to modal_price / Modal_Price
                if modal_val is None:
                    for p_key in ["modal_price", "Modal_Price", "Modal_x0020_Price"]:
                        if p_key in latest_row.index and pd.notna(latest_row[p_key]):
                            try:
                                raw_p = float(latest_row[p_key])
                                # If raw price is from unnormalized quintal source (>100), convert to ₹/kg
                                modal_val = (raw_p / 100.0) if raw_p > 100.0 else raw_p
                                break
                            except (ValueError, TypeError):
                                pass

                result["market_price_context"] = {
                    "latest_modal_price_per_kg": round(modal_val, 2) if modal_val is not None else None,
                    "latest_modal_price": round(modal_val, 2) if modal_val is not None else None,
                    "mandi_records_count": int(len(crop_prices))
                }

    return result