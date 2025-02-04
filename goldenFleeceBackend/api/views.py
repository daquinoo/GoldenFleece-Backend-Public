from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import PredsDaily, PredsWeekly, PredsMonthly, DailyAcc, WeeklyAcc, MonthlyAcc
from .serializers import PredsDailySerializer, PredsWeeklySerializer, PredsMonthlySerializer, DailyAccSerializer, WeeklyAccSerializer, MonthlyAccSerializer
from django.db.models import Max, F, FloatField, ExpressionWrapper
import requests
import yfinance as yf
from datetime import datetime, timedelta

ALPHA_VANTAGE_API_KEY = "CXPSPN3NBC0L5DGO"

@api_view(["GET"])
def get_index_prices(request):
    """
    Approximate Dow, S&P, Nasdaq index quotes using ETFs: DIA, SPY, QQQ.
    We'll fetch TIME_SERIES_DAILY data from Alpha Vantage for each symbol,
    parse the last 2 days, compute daily change, and return price + change string.
    """
    try:
        # Mapping to identify the "label" we want
        etf_map = {
            "dow": "DIA",
            "snp": "SPY",
            "nasdaq": "QQQ",
        }

        results = {}
        for label, symbol in etf_map.items():
            # Fetch daily series
            url = (
                f"https://www.alphavantage.co/query"
                f"?function=TIME_SERIES_DAILY"
                f"&symbol={symbol}"
                f"&apikey={ALPHA_VANTAGE_API_KEY}"
                f"&outputsize=compact"  
            )
            r = requests.get(url)
            data = r.json()

            ts_key = "Time Series (Daily)"
            if ts_key not in data:
                # Possibly an error or limit reached
                results[label] = {"price": None, "change": "Data error"}
                continue

            time_series = data[ts_key]
            # Convert to list of (date, {OHLC}) sorted descending by date
            sorted_days = sorted(time_series.items(), reverse=True)
            if len(sorted_days) < 1:
                results[label] = {"price": None, "change": "No data"}
                continue

            # last day
            latest_date, latest_data = sorted_days[0]
            last_close = float(latest_data["4. close"])

            # previous day
            if len(sorted_days) >= 2:
                prev_date, prev_data = sorted_days[1]
                prev_close = float(prev_data["4. close"])
            else:
                prev_close = last_close 

            diff = last_close - prev_close
            pct = (diff / prev_close * 100) if prev_close != 0 else 0
            sign = "+" if diff >= 0 else ""
            change_str = f"{sign}{diff:.2f} ({sign}{pct:.2f}%)"

            results[label] = {
                "price": f"{last_close:.2f}",
                "change": change_str
            }

        return Response(results, status=status.HTTP_200_OK)

    except Exception as e:
        print("Error in get_index_prices:", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def get_hot_stocks(request):
    """
    Fallback to multiple GLOBAL_QUOTE calls for each symbol.
    We'll parse "Global Quote" data and compute day change if provided.
    """
    try:
        symbols = ["AAPL", "NVDA", "TSLA", "AMZN", "GOOGL", "MSFT", "META", "NFLX"]
        hot_list = []

        for sym in symbols:
            url = (
                f"https://www.alphavantage.co/query"
                f"?function=GLOBAL_QUOTE"
                f"&symbol={sym}"
                f"&apikey={ALPHA_VANTAGE_API_KEY}"
            )
            r = requests.get(url)
            data = r.json()
            if "Global Quote" not in data:
                # error or no data
                continue

            gq = data["Global Quote"]
            price_str = gq.get("05. price")
            change_str = gq.get("09. change")
            change_pct_str = gq.get("10. change percent")

            # convert to float
            try:
                price = float(price_str)
            except:
                price = None
            try:
                change = float(change_str) if change_str else 0
            except:
                change = 0
            sign = "+" if change >= 0 else ""
            try:
                change_pct = float(change_pct_str.replace("%", "")) if change_pct_str else 0
            except:
                change_pct = 0

            formatted_change = f"{sign}{change:.2f} ({sign}{change_pct:.2f}%)"

            hot_list.append({
                "symbol": sym,
                "company": sym,
                "ai_score": "—",
                "change": formatted_change,
                "price": f"{price:.2f}" if price else "N/A",
                "avg_volume": gq.get("06. volume", "N/A"),
                "sector": "N/A",
            })

        # sort by change_pct desc
        hot_list.sort(
            key=lambda x: float(x["change"].split("(")[-1].rstrip("%)")) if "(" in x["change"] else 0,
            reverse=True
        )

        # Assign rank
        for i, item in enumerate(hot_list, start=1):
            item["rank"] = i

        return Response(hot_list, status=200)
    except Exception as e:
        print("Error in get_hot_stocks fallback:", e)
        return Response({"error": str(e)}, status=500)



@api_view(["GET"])
def get_sector_performance(request):
    """
    Fallback approach: fetch day-over-day changes for major sector ETFs.
    For example, XLK (Tech), XLF (Financials), XLE (Energy), etc.
    """
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
            url = (
                f"https://www.alphavantage.co/query"
                f"?function=TIME_SERIES_DAILY"
                f"&symbol={symbol}"
                f"&apikey={ALPHA_VANTAGE_API_KEY}"
                f"&outputsize=compact"
            )
            r = requests.get(url)
            data = r.json()
            ts_key = "Time Series (Daily)"

            if ts_key not in data:
                # Possibly an error or limit reached
                results.append({
                    "sector": sector_name,
                    "price": "N/A",
                    "day_change": "Data error",
                    "ticker": symbol,
                })
                continue

            time_series = data[ts_key]
            sorted_days = sorted(time_series.items(), reverse=True)
            if len(sorted_days) < 1:
                results.append({
                    "sector": sector_name,
                    "price": "N/A",
                    "day_change": "No data",
                    "ticker": symbol,
                })
                continue

            latest_date, latest_data = sorted_days[0]
            last_close = float(latest_data["4. close"])

            if len(sorted_days) >= 2:
                prev_date, prev_data = sorted_days[1]
                prev_close = float(prev_data["4. close"])
            else:
                prev_close = last_close

            diff = last_close - prev_close
            pct = (diff / prev_close * 100) if prev_close != 0 else 0
            sign = "+" if diff >= 0 else ""
            change_str = f"{sign}{diff:.2f} ({sign}{pct:.2f}%)"

            results.append({
                "sector": sector_name,
                "ticker": symbol,
                "price": f"{last_close:.2f}",
                "day_change": change_str
            })

        return Response(results, status=200)

    except Exception as e:
        print("Error in get_sector_performance fallback:", e)
        return Response({"error": str(e)}, status=500)


# View for getting symbol prediction
@api_view(['GET'])
def prediction_detail(request, symbol):
    try:
        time_frame = request.GET.get('timeFrame', 'daily').lower()

        if time_frame == 'daily':
            PredictionModel = PredsDaily
            PredictionSerializer = PredsDailySerializer
            AccModel = DailyAcc
            AccSerializer = DailyAccSerializer
        elif time_frame == 'weekly':
            PredictionModel = PredsWeekly
            PredictionSerializer = PredsWeeklySerializer
            AccModel = WeeklyAcc
            AccSerializer = WeeklyAccSerializer
        elif time_frame == 'monthly':
            PredictionModel = PredsMonthly
            PredictionSerializer = PredsMonthlySerializer
            AccModel = MonthlyAcc
            AccSerializer = MonthlyAccSerializer
        else:
            return Response({'error': 'Invalid time frame'}, status=400)

        latest_date = PredictionModel.objects.filter(symbol__iexact=symbol).aggregate(Max('date'))['date__max']
        if not latest_date:
            return Response({'error': 'Prediction not found'}, status=404)

        prediction = PredictionModel.objects.get(symbol__iexact=symbol, date=latest_date)
        prediction_serializer = PredictionSerializer(prediction)

        # Get confidence intervals
        acc_data = AccModel.objects.get(symbol__iexact=symbol)
        acc_serializer = AccSerializer(acc_data)

        # Combine data
        data = prediction_serializer.data
        data.update(acc_serializer.data)

        return Response(data)
    except PredictionModel.DoesNotExist:
        return Response({'error': 'Prediction not found'}, status=404)
    except AccModel.DoesNotExist:
        return Response({'error': 'Confidence interval data not found'}, status=404)
    except Exception as e:
        print(e)
        return Response({'error': 'An error occurred'}, status=500)
    


# View for getting top predictions
@api_view(['GET'])
def top_predictions(request):
    try:

        time_frame = request.GET.get('timeFrame', 'daily').lower()
        count = int(request.GET.get('count', 20))

        if time_frame == 'daily':
            PredictionModel = PredsDaily
            PredictionSerializer = PredsDailySerializer
        elif time_frame == 'weekly':
            PredictionModel = PredsWeekly
            PredictionSerializer = PredsWeeklySerializer
        elif time_frame == 'monthly':
            PredictionModel = PredsMonthly
            PredictionSerializer = PredsMonthlySerializer
        else:
            return Response({'error': 'Invalid time frame'}, status=400)

        latest_date = PredictionModel.objects.aggregate(Max('date'))['date__max']
        if not latest_date:
            return Response({'error': 'No predictions available'}, status=404)

        predictions = PredictionModel.objects.filter(date=latest_date)

        predictions = predictions.annotate(
            predicted_change_percentage=ExpressionWrapper(
                F('pred_close') * 100,
                output_field=FloatField()
            )
        )

        top_stocks = predictions.order_by('-predicted_change_percentage')[:count]
        serializer = PredictionSerializer(top_stocks, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(e)
        return Response({'error': 'Error fetching top predictions'}, status=500)

# View for getting all predictions
@api_view(['GET'])
def all_predictions(request):
    try:
        time_frame = request.GET.get('timeFrame', 'daily').lower()

        if time_frame == 'daily':
            PredictionModel = PredsDaily
            PredictionSerializer = PredsDailySerializer
        elif time_frame == 'weekly':
            PredictionModel = PredsWeekly
            PredictionSerializer = PredsWeeklySerializer
        elif time_frame == 'monthly':
            PredictionModel = PredsMonthly
            PredictionSerializer = PredsMonthlySerializer
        else:
            return Response({'error': 'Invalid time frame'}, status=400)

        latest_date = PredictionModel.objects.aggregate(Max('date'))['date__max']
        if not latest_date:
            return Response({'error': 'No predictions available'}, status=404)

        predictions = PredictionModel.objects.filter(date=latest_date)

        predictions = predictions.annotate(
            predicted_change_percentage=ExpressionWrapper(
                F('pred_close') * 100,
                output_field=FloatField()
            )
        )
        # Currently ordering by symbol
        predictions = predictions.order_by('symbol')

        serializer = PredictionSerializer(predictions, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(e)
        return Response({'error': 'Error fetching all predictions'}, status=500)
    

    # api/views.py

@api_view(["GET"])
def stock_detail(request, symbol):
    """
    Fetch all needed data from Alpha Vantage for a given symbol.
    - Current price + daily change from 'GLOBAL_QUOTE'
    - Historical data for chart from 'TIME_SERIES_DAILY' (or weekly/monthly if you want)
    - Some technical indicators (e.g. RSI, SMA)
    Returns a combined JSON for the frontend to display.
    """
    import requests

    ALPHA_VANTAGE_API_KEY = "CXPSPN3NBC0L5DGO"  # Use environment variable in production

    try:
        # 1) Global quote for current price
        global_quote_url = (
            f"https://www.alphavantage.co/query"
            f"?function=GLOBAL_QUOTE"
            f"&symbol={symbol}"
            f"&apikey={ALPHA_VANTAGE_API_KEY}"
        )
        r1 = requests.get(global_quote_url)
        gq_data = r1.json()
        global_quote = gq_data.get("Global Quote", {})

        # 2) Time Series (Daily) for chart data
        ts_url = (
            f"https://www.alphavantage.co/query"
            f"?function=TIME_SERIES_DAILY"
            f"&symbol={symbol}"
            f"&outputsize=compact"   # or 'full'
            f"&apikey={ALPHA_VANTAGE_API_KEY}"
        )
        r2 = requests.get(ts_url)
        ts_data = r2.json()

        daily_series = ts_data.get("Time Series (Daily)", {})

        # We'll convert daily_series into a list of { date, open, high, low, close, volume } sorted by date ascending
        chart_data = []
        for date_str, ohlc in daily_series.items():
            chart_data.append({
                "date": date_str,
                "open": float(ohlc["1. open"]),
                "high": float(ohlc["2. high"]),
                "low": float(ohlc["3. low"]),
                "close": float(ohlc["4. close"]),
                "volume": int(float(ohlc["5. volume"]))  # cast volume as int
            })
        # sort ascending by date
        chart_data.sort(key=lambda x: x["date"])


        rsi_url = (
            f"https://www.alphavantage.co/query"
            f"?function=RSI"
            f"&symbol={symbol}"
            f"&interval=daily"
            f"&time_period=14"
            f"&series_type=close"
            f"&apikey={ALPHA_VANTAGE_API_KEY}"
        )
        r3 = requests.get(rsi_url)
        rsi_data = r3.json()
        # structure: { "Technical Analysis: RSI": { "2025-01-16": { "RSI": "35.1234" }, ... } }
        rsi_series = rsi_data.get("Technical Analysis: RSI", {})
        # get the latest RSI if available
        latest_rsi = None
        if rsi_series:
            # sort by date descending
            sorted_rsi = sorted(rsi_series.items(), reverse=True)
            latest_rsi = float(sorted_rsi[0][1]["RSI"])

        # Example: SMA
        sma_url = (
            f"https://www.alphavantage.co/query"
            f"?function=SMA"
            f"&symbol={symbol}"
            f"&interval=daily"
            f"&time_period=20"
            f"&series_type=close"
            f"&apikey={ALPHA_VANTAGE_API_KEY}"
        )
        r4 = requests.get(sma_url)
        sma_data = r4.json()
        # structure: { "Technical Analysis: SMA": { "2025-01-16": { "SMA": "155.1234" }, ... } }
        sma_series = sma_data.get("Technical Analysis: SMA", {})
        latest_sma = None
        if sma_series:
            sorted_sma = sorted(sma_series.items(), reverse=True)
            latest_sma = float(sorted_sma[0][1]["SMA"])

        
        current_price = global_quote.get("05. price", "N/A")
        day_change = global_quote.get("09. change", "0")
        day_change_percent = global_quote.get("10. change percent", "0%")

        ai_score = "Buy"  # retrieve from your model

        response_data = {
            "symbol": symbol,
            "current_price": current_price,
            "day_change": day_change,
            "day_change_percent": day_change_percent,
            "ai_score": ai_score,
            "chart_data": chart_data,  
            "indicators": {
                "RSI_14": latest_rsi,
                "SMA_20": latest_sma,
            }
        }

        return Response(response_data, status=200)

    except Exception as e:
        print("Error in stock_detail:", e)
        return Response({"error": str(e)}, status=500)



@api_view(["GET"])
def search_stocks(request):
    """
    Calls Alpha Vantage's SYMBOL_SEARCH with the 'query' parameter.
    Returns a list of matches: symbol, name, etc.
    e.g. /api/search-stocks/?query=aapl
    """
    query = request.GET.get('query', '')
    if not query:
        return Response([], status=status.HTTP_200_OK)

    try:
        url = (
            f"https://www.alphavantage.co/query"
            f"?function=SYMBOL_SEARCH"
            f"&keywords={query}"
            f"&apikey={ALPHA_VANTAGE_API_KEY}"
        )
        r = requests.get(url)
        data = r.json()

        # structure: { "bestMatches": [ { "1. symbol": ..., "2. name": ..., ... }, ... ] }
        best_matches = data.get("bestMatches", [])
        # Convert to a simpler list of dicts
        results = []
        for match in best_matches:
            symbol = match.get("1. symbol", "")
            name = match.get("2. name", "")
            region = match.get("4. region", "")
            # You can add more fields if needed
            results.append({
                "symbol": symbol,
                "name": name,
                "region": region,
            })

        # Maybe only return top 5
        results = results[:5]

        return Response(results, status=status.HTTP_200_OK)
    except Exception as e:
        print("Error in search_stocks:", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)