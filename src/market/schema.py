"""DuckDB schema for vectoring market data."""


def create_schema(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            symbol             VARCHAR PRIMARY KEY,
            name               VARCHAR,
            sector             VARCHAR,
            industry           VARCHAR,
            listing_date       DATE,
            shares_outstanding BIGINT,
            description        VARCHAR
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ohlcv_daily (
            symbol       VARCHAR,
            date         DATE,
            open         DOUBLE,
            high         DOUBLE,
            low          DOUBLE,
            close        DOUBLE,
            volume       BIGINT,
            value        DOUBLE,
            frequency    BIGINT,
            foreign_buy  DOUBLE,
            foreign_sell DOUBLE,
            net_foreign  DOUBLE,
            PRIMARY KEY (symbol, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals_ratio (
            symbol            VARCHAR,
            date              DATE,
            pe_ttm            DOUBLE,
            pe_forward        DOUBLE,
            pe_annualised     DOUBLE,
            pb                DOUBLE,
            ps_ttm            DOUBLE,
            ev_ebitda         DOUBLE,
            roe               DOUBLE,
            roa               DOUBLE,
            roic              DOUBLE,
            gross_margin      DOUBLE,
            operating_margin  DOUBLE,
            debt_equity       DOUBLE,
            current_ratio     DOUBLE,
            interest_coverage DOUBLE,
            dividend_yield    DOUBLE,
            payout_ratio      DOUBLE,
            earnings_yield    DOUBLE,
            PRIMARY KEY (symbol, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS financials_quarterly (
            symbol         VARCHAR,
            period_end     DATE,
            statement_type VARCHAR,
            line_item      VARCHAR,
            value          DOUBLE,
            unit           VARCHAR,
            PRIMARY KEY (symbol, period_end, statement_type, line_item)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyst_consensus (
            symbol                     VARCHAR,
            date                       DATE,
            consensus_rating           VARCHAR,
            target_median              DOUBLE,
            target_high                DOUBLE,
            target_low                 DOUBLE,
            estimate_revision_30d_up   INTEGER,
            estimate_revision_30d_down INTEGER,
            PRIMARY KEY (symbol, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyst_ratings (
            symbol       VARCHAR,
            as_of_date   DATE,
            broker       VARCHAR,
            rating       VARCHAR,
            target_price DOUBLE,
            analyst_name VARCHAR
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_performance (
            symbol     VARCHAR,
            as_of_date DATE,
            period     VARCHAR,
            change_pct DOUBLE,
            high       DOUBLE,
            low        DOUBLE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS corporate_actions (
            symbol        VARCHAR,
            action_type   VARCHAR,
            announce_date DATE,
            ex_date       DATE,
            pay_date      DATE,
            ratio         DOUBLE,
            cash_amount   DOUBLE,
            notes         VARCHAR
        )
    """)
