# Modern Investment Analytics Platform

An end-to-end financial analytics platform designed to demonstrate modern data engineering and analytics engineering practices. The platform ingests market, economic, and company fundamental data and transforms it into business-ready investment analytics and interactive dashboards.

The initial pipeline uses Python and `yfinance` to extract historical market data, Pandas to transform and validate the data, and DuckDB as the analytical data store. Future stages of the platform will introduce dbt-based transformations, dimensional modeling, automated workflows, and Power BI dashboards.

## Project Status

**Current:** Market data ingestion pipeline

* [x] yfinance market data extraction
* [x] Pandas transformation and normalization
* [x] Explicit data type standardization
* [x] Data quality validation
* [x] DuckDB database creation and loading
* [x] Automated Python tests
* [ ] FRED economic data ingestion
* [ ] Company fundamentals ingestion
* [ ] dbt transformation layer
* [ ] Dimensional data model
* [ ] Investment analytics models
* [ ] Power BI dashboard
* [ ] GitHub Actions automation

---

## Architecture

The platform is being developed as a modular data pipeline that separates data ingestion, storage, transformation, and analytics.

```text
                         DATA SOURCES
                    ┌─────────┼─────────┐
                    │         │         │
                 yfinance    FRED      SEC
                    │         │         │
                    └─────────┼─────────┘
                              │
                              ▼
                       Python ETL
                              │
                    Data Transformation
                              │
                     Data Quality Checks
                              │
                              ▼
                    ┌─────────────────┐
                    │     DuckDB      │
                    │                 │
                    │   Raw Data      │
                    └────────┬────────┘
                             │
                             ▼
                            dbt
                             │
                    SQL Transformations
                             │
                    Dimensional Modeling
                             │
                             ▼
                    Investment Analytics
                             │
                             ▼
                         Power BI
```

The architecture above represents the planned end state of the platform. Components are being implemented incrementally.

### Current Pipeline

The first implemented pipeline focuses on historical market data:

```text
yfinance
    │
    ▼
Python / Pandas
    │
    ├── MultiIndex normalization
    ├── Data type standardization
    ├── Price normalization
    └── Data quality validation
    │
    ▼
DuckDB
    │
    ▼
raw_market_prices
```

The current market data pipeline extracts historical OHLC, adjusted close, and volume data for a defined set of ETFs and loads the validated results into DuckDB.

---

## Technology Stack

| Layer               | Technology                 |
| ------------------- | -------------------------- |
| Data Source         | yfinance                   |
| Data Ingestion      | Python                     |
| Data Transformation | Pandas                     |
| Data Validation     | Python                     |
| Analytical Database | DuckDB                     |
| Transformation      | dbt *(planned)*            |
| Workflow Automation | GitHub Actions *(planned)* |
| Visualization       | Power BI *(planned)*       |
| Version Control     | Git / GitHub               |

---

## Market Data

The initial dataset contains a diversified set of ETFs representing major segments of the U.S. and global investment markets:

| Ticker | Description                      |
| ------ | -------------------------------- |
| SPY    | S&P 500                          |
| QQQ    | Nasdaq-100                       |
| IWM    | Russell 2000                     |
| VTI    | Total U.S. Stock Market          |
| VXUS   | Total International Stock Market |
| VT     | Global Stock Market              |
| BND    | U.S. Total Bond Market           |

Historical market data currently covers January 2020 through the end of 2025.

The pipeline captures:

* Open price
* High price
* Low price
* Close price
* Adjusted close price
* Trading volume

Both unadjusted and adjusted closing prices are retained because they serve different analytical purposes. Unadjusted prices represent the historical market price, while adjusted prices are useful for analyzing investment performance while accounting for corporate actions such as dividends and splits.

---

## Data Quality

Data quality checks are performed during the ingestion process before data is loaded into DuckDB.

Current validation includes:

* Required ticker validation
* Null ticker detection
* Null date detection
* Null closing price detection
* Duplicate date/ticker detection
* Positive price validation
* Non-negative volume validation
* OHLC price relationship validation
* Expected ticker completeness

The pipeline raises an exception when required data-quality conditions are not satisfied, preventing invalid data from being loaded into the analytical database.

---

## Data Storage

Validated market data is loaded into a local DuckDB database:

```text
database/
└── investment_analytics.duckdb
```

The current database contains the following raw market data table:

```text
raw_market_prices
```

The table provides a standardized long-format representation of the source data:

| Column    | Description              |
| --------- | ------------------------ |
| date      | Trading date             |
| ticker    | Security ticker          |
| open      | Opening market price     |
| high      | Daily high price         |
| low       | Daily low price          |
| close     | Unadjusted closing price |
| adj_close | Adjusted closing price   |
| volume    | Trading volume           |

The DuckDB database is generated by the ETL pipeline and is excluded from version control.

---

## Project Structure

```text
Modern-Investment-Analytics-Platform/
│
├── data/
│   └── .gitkeep
│
├── database/
│   └── investment_analytics.duckdb
│
├── etl/
│   └── market_data.py
│
├── tests/
│
├── .gitignore
├── README.md
└── requirements.txt
```

The project structure will evolve as additional data sources, transformation models, tests, and dashboards are introduced.

---

## Getting Started

### Prerequisites

* Python 3.14+
* Git
* Visual Studio Code or another Python development environment

### 1. Clone the Repository

```bash
git clone https://github.com/BrandonN525/Modern-Investment-Analytics-Platform.git

cd Modern-Investment-Analytics-Platform
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the environment on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Market Data Pipeline

```bash
python etl/market_data.py
```

The pipeline will:

1. Download historical market data from yfinance.
2. Transform the source MultiIndex DataFrame into a standardized long format.
3. Apply explicit data types.
4. Execute data-quality checks.
5. Create the DuckDB database if it does not already exist.
6. Create or replace the `raw_market_prices` table.
7. Perform basic load verification.

---

## Planned Analytics

Once the core ingestion and transformation layers are established, the platform will support analytics such as:

### Security Performance

* Daily returns
* Cumulative returns
* Annualized returns
* Volatility
* Maximum drawdown

### Benchmark Analysis

* Performance relative to major market benchmarks
* Risk-adjusted performance
* Rolling performance comparisons

### Portfolio Analytics

* Portfolio performance
* Asset allocation
* Benchmark comparison
* Contribution to return
* Risk metrics

### Economic Analysis

* Relationship between market performance and economic indicators
* Interest-rate and inflation analysis
* Market performance across different economic environments

---

## Future Development

The platform will be developed incrementally across several stages:

### Phase 1 — Market Data Ingestion

* [x] yfinance extraction
* [x] Pandas transformation
* [x] Data-quality validation
* [x] DuckDB loading

### Phase 2 — Data Quality & Testing

* [x] Automated Python tests
* [x] Expanded data-quality framework
* [x] Pipeline error handling and logging

### Phase 3 — Additional Data Sources

* [ ] FRED economic indicators
* [ ] Company fundamentals
* [ ] Additional market data

### Phase 4 — Analytics Engineering

* [ ] dbt integration
* [ ] Staging models
* [ ] Intermediate models
* [ ] Fact and dimension tables
* [ ] dbt data-quality tests
* [ ] Analytical metrics

### Phase 5 — Visualization

* [ ] Power BI data model
* [ ] Investment performance dashboard
* [ ] Benchmark comparison dashboard
* [ ] Economic indicators dashboard

### Phase 6 — Automation

* [ ] GitHub Actions
* [ ] Automated testing
* [ ] Automated ETL execution
* [ ] Automated dbt transformations

---

## Goals

This project is intended to demonstrate practical experience with:

* Building Python-based ETL pipelines
* Working with external financial data sources
* Transforming and standardizing semi-structured data
* Implementing data-quality checks
* Working with analytical databases
* Designing dimensional data models
* Building SQL-based transformation pipelines
* Developing reproducible and testable data workflows
* Automating data pipelines
* Communicating analytical results through dashboards
