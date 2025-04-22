from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import (
    PredsDaily,
    PredsWeekly,
    PredsMonthly,
    DailyAcc,
    WeeklyAcc,
    MonthlyAcc,
    MonthlyGrade,
)
from .serializers import (
    PredsDailySerializer,
    PredsWeeklySerializer,
    PredsMonthlySerializer,
    DailyAccSerializer,
    WeeklyAccSerializer,
    MonthlyAccSerializer,
    MonthlyGradeSerializer,
)
from django.db.models import Max, F, FloatField, ExpressionWrapper
import requests
import traceback
from datetime import datetime, timedelta

POLYGON_API_KEY = "6ZgD13I3BYziPRbvkkjrA6GogAnJrKDR"
POLYGON_HOST = "https://api.polygon.io"

# Helper utilities
def _get_last_two_closes(ticker: str):
    """
    Return (latest_close, previous_close) for the given ticker using Polygon.
    """
    end = datetime.utcnow().date()
    start = end - timedelta(days=7)  

    url = (
        f"{POLYGON_HOST}/v2/aggs/ticker/{ticker}/range/1/day/"
        f"{start}/{end}?adjusted=true&sort=desc&limit=2&apiKey={POLYGON_API_KEY}"
    )
    resp = requests.get(url).json()
    results = resp.get("results", [])
    if not results:
        return None, None

    latest_close = results[0]["c"]
    prev_close = results[1]["c"] if len(results) > 1 else latest_close
    return latest_close, prev_close


def _format_change(last_close: float, prev_close: float):
    diff = last_close - prev_close
    pct = (diff / prev_close * 100) if prev_close else 0
    sign = "+" if diff >= 0 else ""
    return f"{sign}{diff:.2f} ({sign}{pct:.2f}%)"


# Index prices (Dow, S&P, Nasdaq via ETFs)
@api_view(["GET"])
def get_index_prices(request):
    try:
        etf_map = {"dow": "DIA", "snp": "SPY", "nasdaq": "QQQ"}

        results = {}
        for label, symbol in etf_map.items():
            latest_close, prev_close = _get_last_two_closes(symbol)
            if latest_close is None:
                results[label] = {"price": None, "change": "Data error"}
                continue

            results[label] = {
                "price": f"{latest_close:.2f}",
                "change": _format_change(latest_close, prev_close),
            }

        return Response(results, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Hot stocks snapshot
@api_view(["GET"])
def get_hot_stocks(request):
    try:
        symbols = ["AAPL", "NVDA", "TSLA", "AMZN", "GOOGL", "MSFT", "META", "NFLX"]
        tickers_param = ",".join(symbols)
        url = (
            f"{POLYGON_HOST}/v2/snapshot/locale/us/markets/stocks/tickers"
            f"?tickers={tickers_param}&apiKey={POLYGON_API_KEY}"
        )
        data = requests.get(url).json()
        tickers = data.get("tickers", [])

        hot_list = []
        for item in tickers:
            sym = item["ticker"]
            price = item["lastTrade"]["p"]
            change = item["todaysChange"]
            change_pct = item["todaysChangePerc"]
            sign = "+" if change >= 0 else ""

            hot_list.append(
                {
                    "symbol": sym,
                    "company": sym,
                    "ai_score": "—",
                    "change": f"{sign}{change:.2f} ({sign}{change_pct:.2f}%)",
                    "price": f"{price:.2f}",
                    "avg_volume": item["day"]["v"],
                    "sector": "N/A",
                }
            )

        hot_list.sort(
            key=lambda x: float(x["change"].split("(")[-1].rstrip("%)")), reverse=True
        )
        for i, itm in enumerate(hot_list, 1):
            itm["rank"] = i

        return Response(hot_list, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# Sector ETF performance
@api_view(["GET"])
def get_sector_performance(request):
    try:
        etf_map = {
            "Technology": "XLK",
            "Financials": "XLF",
            "Energy": "XLE",
            "Healthcare": "XLV",
            "Consumer Discretionary": "XLY",
            "Industrials": "XLI",
            "Utilities": "XLU",
            "Consumer Staples": "XLP",
            "Materials": "XLB",
            "Real Estate": "XLRE",
        }

        results = []
        for sector_name, symbol in etf_map.items():
            latest_close, prev_close = _get_last_two_closes(symbol)
            if latest_close is None:
                results.append(
                    {
                        "sector": sector_name,
                        "ticker": symbol,
                        "price": "N/A",
                        "day_change": "Data error",
                    }
                )
                continue

            results.append(
                {
                    "sector": sector_name,
                    "ticker": symbol,
                    "price": f"{latest_close:.2f}",
                    "day_change": _format_change(latest_close, prev_close),
                }
            )

        return Response(results, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# Predictions
@api_view(["GET"])
def prediction_detail(request, symbol):
    try:
        time_frame = request.GET.get("timeFrame", "daily").lower()

        if time_frame == "daily":
            PredictionModel = PredsDaily
            PredictionSerializer = PredsDailySerializer
            AccModel = DailyAcc
            AccSerializer = DailyAccSerializer
        elif time_frame == "weekly":
            PredictionModel = PredsWeekly
            PredictionSerializer = PredsWeeklySerializer
            AccModel = WeeklyAcc
            AccSerializer = WeeklyAccSerializer
        elif time_frame == "monthly":
            PredictionModel = PredsMonthly
            PredictionSerializer = PredsMonthlySerializer
            AccModel = MonthlyAcc
            AccSerializer = MonthlyAccSerializer
        else:
            return Response({"error": "Invalid time frame"}, status=400)

        latest_date = (
            PredictionModel.objects.filter(symbol__iexact=symbol).aggregate(Max("date"))[
                "date__max"
            ]
        )
        if not latest_date:
            return Response({"error": "Prediction not found"}, status=404)

        prediction = PredictionModel.objects.get(
            symbol__iexact=symbol, date=latest_date
        )
        prediction_serializer = PredictionSerializer(prediction)

        acc_data = AccModel.objects.get(symbol__iexact=symbol)
        acc_serializer = AccSerializer(acc_data)

        data = prediction_serializer.data
        data.update(acc_serializer.data)
        return Response(data)
    except PredictionModel.DoesNotExist:
        return Response({"error": "Prediction not found"}, status=404)
    except AccModel.DoesNotExist:
        return Response({"error": "Confidence interval data not found"}, status=404)
    except Exception as e:
        return Response({"error": "An error occurred"}, status=500)


@api_view(["GET"])
def top_predictions(request):
    try:
        time_frame = request.GET.get("timeFrame", "daily").lower()
        count = int(request.GET.get("count", 20))

        if time_frame == "daily":
            PredictionModel = PredsDaily
            PredictionSerializer = PredsDailySerializer
        elif time_frame == "weekly":
            PredictionModel = PredsWeekly
            PredictionSerializer = PredsWeeklySerializer
        elif time_frame == "monthly":
            PredictionModel = PredsMonthly
            PredictionSerializer = PredsMonthlySerializer
        else:
            return Response({"error": "Invalid time frame"}, status=400)

        latest_date = PredictionModel.objects.aggregate(Max("date"))["date__max"]
        if not latest_date:
            return Response({"error": "No predictions available"}, status=404)

        predictions = PredictionModel.objects.filter(date=latest_date).annotate(
            predicted_change_percentage=ExpressionWrapper(
                F("pred_close") * 100, output_field=FloatField()
            )
        )

        top_stocks = predictions.order_by("-predicted_change_percentage")[:count]
        serializer = PredictionSerializer(top_stocks, many=True)
        return Response(serializer.data)
    except Exception:
        return Response({"error": "Error fetching top predictions"}, status=500)


@api_view(["GET"])
def all_predictions(request):
    try:
        time_frame = request.GET.get("timeFrame", "daily").lower()

        if time_frame == "daily":
            PredictionModel = PredsDaily
            PredictionSerializer = PredsDailySerializer
        elif time_frame == "weekly":
            PredictionModel = PredsWeekly
            PredictionSerializer = PredsWeeklySerializer
        elif time_frame == "monthly":
            PredictionModel = PredsMonthly
            PredictionSerializer = PredsMonthlySerializer
        else:
            return Response({"error": "Invalid time frame"}, status=400)

        latest_date = PredictionModel.objects.aggregate(Max("date"))["date__max"]
        if not latest_date:
            return Response({"error": "No predictions available"}, status=404)

        predictions = (
            PredictionModel.objects.filter(date=latest_date)
            .annotate(
                predicted_change_percentage=ExpressionWrapper(
                    F("pred_close") * 100, output_field=FloatField()
                )
            )
            .order_by("symbol")
        )

        serializer = PredictionSerializer(predictions, many=True)
        return Response(serializer.data)
    except Exception:
        return Response({"error": "Error fetching all predictions"}, status=500)



# Stock detail 
@api_view(["GET"])
def stock_detail(request, symbol):
    """
    Returns:
      - current_price, day_change, day_change_percent
      - chart_data: last 365 daily bars
      - fundamentals: name, market_cap, sector, industry
      - financials: income_statement, balance_sheet, cash_flow, ratios
      - monthly_grade: open_grade_sign, open_grade_class
    """
    try:
        # 1) Real time quote & change
        snap_url = (
            f"{POLYGON_HOST}/v2/snapshot/locale/us/markets/stocks/tickers/"
            f"{symbol}?apiKey={POLYGON_API_KEY}"
        )
        snap = requests.get(snap_url).json().get("ticker", {})
        current_price      = snap.get("lastTrade", {}).get("p", 0.0)
        day_change         = snap.get("todaysChange",  0.0)
        day_change_pct     = snap.get("todaysChangePerc", 0.0)
        sign               = "+" if day_change >= 0 else ""
        day_change_str     = f"{sign}{day_change:.2f}"
        day_change_pct_str = f"{sign}{day_change_pct:.2f}%"

        # 2) Historical chart (Currently 1‑year daily)
        end   = datetime.utcnow().date()
        start = end - timedelta(days=365)
        hist_url = (
            f"{POLYGON_HOST}/v2/aggs/ticker/{symbol}/range/1/day/"
            f"{start}/{end}?adjusted=true&sort=asc&limit=500&apiKey={POLYGON_API_KEY}"
        )
        bars = requests.get(hist_url).json().get("results", [])
        chart_data = [
            {
                "date":   datetime.utcfromtimestamp(b["t"] / 1000).strftime("%Y-%m-%d"),
                "open":   b["o"],
                "high":   b["h"],
                "low":    b["l"],
                "close":  b["c"],
                "volume": b["v"],
            }
            for b in bars
        ]

        # 3) Company metadata
        meta_url = (
            f"{POLYGON_HOST}/v3/reference/tickers/{symbol}"
            f"?apiKey={POLYGON_API_KEY}"
        )
        meta = requests.get(meta_url).json().get("results", {})
        company_name = meta.get("name")
        market_cap   = meta.get("market_cap")
        sector       = meta.get("sic_description")
        industry     = meta.get("type") or meta.get("market")

        # 4) Latest quarterly financials
        fin_url  = (
            f"{POLYGON_HOST}/v2/reference/financials/{symbol}"
            f"?limit=1&apiKey={POLYGON_API_KEY}"
        )
        fin_resp = requests.get(fin_url)
        if fin_resp.status_code == 200:
            raw = fin_resp.json().get("results") or []
        else:
            raw = []
        fin0 = raw[0].get("financials", {}) if raw else {}

        # Income Statement
        revenue          = fin0.get("revenue")
        gross_profit     = fin0.get("grossProfit")
        operating_income = fin0.get("operatingIncome")
        net_income       = fin0.get("netIncome")

        # Balance Sheet
        total_assets       = fin0.get("assets")
        total_liabilities  = fin0.get("liabilities")
        shareholder_equity = fin0.get("equity") or fin0.get("totalEquity")

        # Cash Flow
        operating_cf = fin0.get("operatingCashFlow")
        investing_cf = fin0.get("investingCashFlow")
        financing_cf = fin0.get("financingCashFlow")

        # Key Ratios
        def _pct(val):
            return f"{val*100:.2f}%" if val is not None else None

        ratios = {
            "roe":              _pct(fin0.get("returnOnEquity")),
            "roa":              _pct(fin0.get("returnOnAssets")),
            "gross_margin":     _pct(fin0.get("grossProfitMargin")),
            "operating_margin": _pct(fin0.get("operatingMargin")),
        }

        # Build response
        data = {
            "symbol":             symbol.upper(),
            "current_price":      f"{current_price:.2f}",
            "day_change":         day_change_str,
            "day_change_percent": day_change_pct_str,
            "chart_data":         chart_data,
            "fundamentals": {
                "name":        company_name,
                "market_cap":  market_cap,
                "sector":      sector,
                "industry":    industry,
            },
            "financials": {
                "income_statement": {
                    "revenue":          revenue,
                    "gross_profit":     gross_profit,
                    "operating_income": operating_income,
                    "net_income":       net_income,
                },
                "balance_sheet": {
                    "assets":             total_assets,
                    "liabilities":        total_liabilities,
                    "shareholder_equity": shareholder_equity,
                },
                "cash_flow": {
                    "operating": operating_cf,
                    "investing": investing_cf,
                    "financing": financing_cf,
                },
                "ratios": ratios,
            },
        }

        # 5) Latest monthly grade
        latest_date = (
            MonthlyGrade.objects
            .filter(symbol__iexact=symbol)
            .aggregate(Max("date"))["date__max"]
        )
        if latest_date:
            grade = MonthlyGrade.objects.get(
                symbol__iexact=symbol, date=latest_date
            )
            data["monthly_grade"] = MonthlyGradeSerializer(grade).data
        else:
            data["monthly_grade"] = {
                "open_grade_sign": None,
                "open_grade_class": None,
            }

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Symbol search
@api_view(["GET"])
def search_stocks(request):
    query = request.GET.get("query", "").strip()
    if not query:
        return Response([], status=status.HTTP_200_OK)

    try:
        url = (
            f"{POLYGON_HOST}/v3/reference/tickers"
            f"?search={query}&active=true&limit=5&apiKey={POLYGON_API_KEY}"
        )
        data = requests.get(url).json()
        matches = data.get("results", [])

        results = [
            {
                "symbol": m.get("ticker", ""),
                "name": m.get("name", ""),
                "region": m.get("primary_exchange", ""),
            }
            for m in matches
        ]

        return Response(results, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
