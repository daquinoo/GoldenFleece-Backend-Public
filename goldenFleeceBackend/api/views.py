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
from requests.exceptions import JSONDecodeError

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

            # fetch latest monthly grade class
            latest_date = (
                MonthlyGrade.objects
                .filter(symbol__iexact=sym)
                .aggregate(Max("date"))["date__max"]
            )
            if latest_date:
                mg = MonthlyGrade.objects.get(
                    symbol__iexact=sym, date=latest_date
                )
                grade_class = mg.open_grade_class or "—"
            else:
                grade_class = "—"

            hot_list.append(
                {
                    "symbol": sym,
                    "company": sym,
                    "ai_score": grade_class,
                    "change": f"{sign}{change:.2f} ({sign}{change_pct:.2f}%)",
                    "price": f"{price:.2f}",
                    "avg_volume": item["day"]["v"],
                    "sector": "N/A",
                }
            )

        # sort by change_pct desc
        hot_list.sort(
            key=lambda x: float(x["change"].split("(")[-1].rstrip("%)")), 
            reverse=True
        )

        # assign rank
        for i, itm in enumerate(hot_list, start=1):
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
      • current_price, day_change, day_change_percent
      • chart_data: last 365 daily bars
      • fundamentals: metadata + description
      • financials: snapshot + indicators
      • monthly_grade
    """
    try:
        # 1) Snapshot & price change
        snap = requests.get(
            f"{POLYGON_HOST}/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
            f"?apiKey={POLYGON_API_KEY}"
        ).json().get("ticker",{})
        cp = snap.get("lastTrade",{}).get("p",0.0)
        dc = snap.get("todaysChange",0.0)
        dp = snap.get("todaysChangePerc",0.0)
        sign = "+" if dc>=0 else ""
        # session vs prev
        today     = snap.get("day",{})
        prevDay   = snap.get("prevDay",{})
        lastQuote = snap.get("lastQuote",{})

        # 2) 1-year bars + chart_data
        end   = datetime.utcnow().date()
        start = end - timedelta(days=365)
        bars  = requests.get(
            f"{POLYGON_HOST}/v2/aggs/ticker/{symbol}/range/1/day/"
            f"{start}/{end}?adjusted=true&sort=asc&limit=500&apiKey={POLYGON_API_KEY}"
        ).json().get("results",[])
        chart_data = [
            {
              "date":    datetime.utcfromtimestamp(b["t"]/1000).strftime("%Y-%m-%d"),
              "open":    b["o"], "high":b["h"], "low":b["l"],
              "close":   b["c"], "volume":b["v"],
            } for b in bars
        ]

        # 3) Fundamentals metadata
        meta = requests.get(
            f"{POLYGON_HOST}/v3/reference/tickers/{symbol}?apiKey={POLYGON_API_KEY}"
        ).json().get("results",{}) or {}
        fundamentals = {
            "name":         meta.get("name"),
            "description":  meta.get("description"),
            "homepage_url": meta.get("homepage_url"),
            "list_date":    meta.get("list_date"),
            "cik":          meta.get("cik"),
            "currency":     meta.get("currency_name"),
            "employees":    meta.get("total_employees"),
            "sic_code":     meta.get("sic_code"),
            "sic_description": meta.get("sic_description"),
            "address":      meta.get("address"),
            "phone":        meta.get("phone_number"),
            "exchange":     meta.get("primary_exchange"),
            "market_cap":   meta.get("market_cap"),
        }

        # 4) Technical indicators
        def _fetch_vals(url):
            try:
                return requests.get(url).json().get("results",{}).get("values",[])
            except (ValueError, JSONDecodeError):
                return []
        base = f"{POLYGON_HOST}/v1/indicators"
        sma   = _fetch_vals(f"{base}/sma/{symbol}?timespan=day&adjusted=true&window=50&series_type=close&order=desc&apiKey={POLYGON_API_KEY}")
        ema   = _fetch_vals(f"{base}/ema/{symbol}?timespan=day&adjusted=true&window=50&series_type=close&order=desc&apiKey={POLYGON_API_KEY}")
        macd  = _fetch_vals(f"{base}/macd/{symbol}?timespan=day&adjusted=true&short_window=12&long_window=26&signal_window=9&series_type=close&order=desc&apiKey={POLYGON_API_KEY}")
        rsi   = _fetch_vals(f"{base}/rsi/{symbol}?timespan=day&adjusted=true&window=14&series_type=close&order=desc&apiKey={POLYGON_API_KEY}")

        # 5) Monthly grade 
        latest = MonthlyGrade.objects.filter(symbol__iexact=symbol).aggregate(Max("date"))["date__max"]
        if latest:
            mg = MonthlyGrade.objects.get(symbol__iexact=symbol, date=latest)
            grade = MonthlyGradeSerializer(mg).data
        else:
            grade = {"open_grade_sign":None,"open_grade_class":None}

        return Response({
            "symbol":               symbol.upper(),
            "current_price":        f"{cp:.2f}",
            "day_change":           f"{sign}{dc:.2f}",
            "day_change_percent":   f"{sign}{dp:.2f}%",
            "chart_data":           chart_data,
            "fundamentals":         fundamentals,
            "financials": {
                "today":     today,
                "prevDay":   prevDay,
                "lastQuote": lastQuote,
                "indicators": {
                  "sma":  sma,
                  "ema":  ema,
                  "macd": macd,
                  "rsi":  rsi,
                }
            },
            "monthly_grade":        grade,
        })
    except Exception as e:
        traceback.print_exc()
        return Response({"error":str(e)},status=500)

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
