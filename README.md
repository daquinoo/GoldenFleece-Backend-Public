# GoldenFleece Backend

Django project to provide backend services and APIs for the GoldenFleece stock prediction system, fetching data directly from an Azure-hosted database.

## Features
- **Stock Prediction API**:
  - Retrieve predictions for individual stock symbols across daily, weekly, and monthly time frames.
  - Fetch top-performing stock predictions.
  - Get a list of all stock predictions for a specified time frame.
- **Azure Database Integration**:
  - Directly fetches prediction and confidence interval data from an Azure database.

## API Endpoints
1. **Prediction Detail**:  
   `GET /prediction/<symbol>/?timeFrame={daily|weekly|monthly}`  
   - Fetches the latest prediction and confidence interval data for a specific stock symbol.
   
2. **Top Predictions**:  
   `GET /top-predictions/?timeFrame={daily|weekly|monthly}&count={number}`  
   - Retrieves the top-performing stock predictions (default: 20).
   
3. **All Predictions**:  
   `GET /all-predictions/?timeFrame={daily|weekly|monthly}`  
   - Lists all stock predictions for the specified time frame.

## Project Structure
- **models.py**: Defines data models for predictions and confidence intervals (`PredsDaily`, `PredsWeekly`, `PredsMonthly`, `DailyAcc`, `WeeklyAcc`, `MonthlyAcc`).
- **serializers.py**: Serializes and deserializes data for API responses.
- **views.py**: Contains logic for fetching and processing prediction data.
- **urls.py**: Routes API endpoints to corresponding views.

## Getting Started
To get started with this project, follow these steps:

1. Clone the Backend Repository:
    ```bash
    git clone --branch backend https://github.com/yourusername/GoldenFleeceDjango.git
    ```
2. Set Up a Virtual Environment:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3. Instal dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Start development server:
    ```bash
    python manage.py runserver
    ```
