import sqlite3
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time
import json
import os
from bs4 import BeautifulSoup
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, db_path='investment_data.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Inicializa o banco de dados SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabela para Bitcoin
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bitcoin_prices (
                date TEXT PRIMARY KEY,
                price_brl REAL,
                price_usd REAL,
                volume REAL,
                market_cap REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela para ações brasileiras
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_prices (
                date TEXT,
                symbol TEXT,
                price REAL,
                volume REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (date, symbol)
            )
        """)

        # Tabela para índices (Ibovespa, IFIX, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS index_prices (
                date TEXT,
                index_name TEXT,
                value REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (date, index_name)
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Banco de dados inicializado")

    def get_bitcoin_data_yahoo(self, days=30):
        """Coleta dados do Bitcoin via Yahoo Finance"""
        try:
            btc = yf.Ticker("BTC-USD")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            hist = btc.history(start=start_date, end=end_date)

            if hist.empty:
                logger.warning("Nenhum dado do Bitcoin obtido via Yahoo Finance")
                return None

            # Converter USD para BRL (aproximação usando taxa atual)
            usd_brl_rate = self.get_usd_brl_rate()

            bitcoin_data = []
            for date, row in hist.iterrows():
                bitcoin_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'price_usd': row['Close'],
                    'price_brl': row['Close'] * usd_brl_rate,
                    'volume': row['Volume']
                })

            logger.info(f"Coletados {len(bitcoin_data)} registros do Bitcoin")
            return bitcoin_data

        except Exception as e:
            logger.error(f"Erro ao coletar dados do Bitcoin: {e}")
            return None

    def get_usd_brl_rate(self):
        """Obtém taxa USD/BRL atual"""
        try:
            usd_brl = yf.Ticker("USDBRL=X")
            rate = usd_brl.history(period="1d")['Close'].iloc[-1]
            return rate
        except:
            return 5.2  # Taxa de fallback

    def get_stock_data(self, symbols, days=30):
        """Coleta dados de ações brasileiras"""
        stock_data = []

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)

                hist = ticker.history(start=start_date, end=end_date)

                if hist.empty:
                    logger.warning(f"Nenhum dado obtido para {symbol}")
                    continue

                for date, row in hist.iterrows():
                    stock_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'symbol': symbol,
                        'price': row['Close'],
                        'volume': row['Volume']
                    })

                logger.info(f"Coletados dados para {symbol}")
                time.sleep(1)  # Evitar rate limiting

            except Exception as e:
                logger.error(f"Erro ao coletar dados de {symbol}: {e}")
                continue

        return stock_data

    def scrape_bitcoin_coinmarketcap(self):
        """Scraping alternativo do CoinMarketCap (método de backup)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            url = "https://coinmarketcap.com/currencies/bitcoin/"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Tentar extrair preço atual (estrutura pode mudar)
                price_element = soup.find('span', class_='sc-f70bb44c-0')
                if price_element:
                    price_text = price_element.text.replace('$', '').replace(',', '')
                    price_usd = float(price_text)

                    usd_brl_rate = self.get_usd_brl_rate()
                    price_brl = price_usd * usd_brl_rate

                    return {
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'price_usd': price_usd,
                        'price_brl': price_brl
                    }

        except Exception as e:
            logger.error(f"Erro no scraping do CoinMarketCap: {e}")

        return None

    def save_bitcoin_data(self, data):
        """Salva dados do Bitcoin no banco"""
        if not data:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for record in data:
            cursor.execute("""
                INSERT OR REPLACE INTO bitcoin_prices 
                (date, price_brl, price_usd, volume) 
                VALUES (?, ?, ?, ?)
            """, (record['date'], record['price_brl'], 
                  record['price_usd'], record.get('volume', 0)))

        conn.commit()
        conn.close()
        logger.info(f"Salvos {len(data)} registros do Bitcoin")

    def save_stock_data(self, data):
        """Salva dados de ações no banco"""
        if not data:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for record in data:
            cursor.execute("""
                INSERT OR REPLACE INTO stock_prices 
                (date, symbol, price, volume) 
                VALUES (?, ?, ?, ?)
            """, (record['date'], record['symbol'], 
                  record['price'], record.get('volume', 0)))

        conn.commit()
        conn.close()
        logger.info(f"Salvos {len(data)} registros de ações")

    def get_bitcoin_price(self, date=None):
        """Obtém preço do Bitcoin do banco local"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if date:
            date_str = date.strftime('%Y-%m-%d') if isinstance(date, datetime) else date
            cursor.execute('SELECT price_brl FROM bitcoin_prices WHERE date = ?', (date_str,))
        else:
            cursor.execute('SELECT price_brl FROM bitcoin_prices ORDER BY date DESC LIMIT 1')

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def get_stock_price(self, symbol, date=None):
        """Obtém preço de ação do banco local"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if date:
            date_str = date.strftime('%Y-%m-%d') if isinstance(date, datetime) else date
            cursor.execute('SELECT price FROM stock_prices WHERE symbol = ? AND date = ?', 
                          (symbol, date_str))
        else:
            cursor.execute('SELECT price FROM stock_prices WHERE symbol = ? ORDER BY date DESC LIMIT 1', 
                          (symbol,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def update_all_data(self, days=7):
        """Atualiza todos os dados"""
        logger.info("Iniciando atualização de dados...")

        # Atualizar Bitcoin
        btc_data = self.get_bitcoin_data_yahoo(days)
        if btc_data:
            self.save_bitcoin_data(btc_data)
        else:
            # Tentar scraping como backup
            scraped_btc = self.scrape_bitcoin_coinmarketcap()
            if scraped_btc:
                self.save_bitcoin_data([scraped_btc])

        # Atualizar ações brasileiras
        symbols = ['PETR4.SA', 'ITUB4.SA', 'VALE3.SA', 'BOVA11.SA', 'BBAS3.SA']
        stock_data = self.get_stock_data(symbols, days)
        if stock_data:
            self.save_stock_data(stock_data)

        logger.info("Atualização concluída")

    def get_data_summary(self):
        """Retorna resumo dos dados armazenados"""
        conn = sqlite3.connect(self.db_path)

        # Bitcoin
        btc_count = conn.execute('SELECT COUNT(*) FROM bitcoin_prices').fetchone()[0]
        btc_latest = conn.execute('SELECT date, price_brl FROM bitcoin_prices ORDER BY date DESC LIMIT 1').fetchone()

        # Ações
        stock_count = conn.execute('SELECT COUNT(*) FROM stock_prices').fetchone()[0]
        symbols_count = conn.execute('SELECT COUNT(DISTINCT symbol) FROM stock_prices').fetchone()[0]

        conn.close()

        return {
            'bitcoin_records': btc_count,
            'bitcoin_latest': btc_latest,
            'stock_records': stock_count,
            'unique_symbols': symbols_count
        }

if __name__ == "__main__":
    collector = DataCollector()

    # Primeira execução - coletar dados dos últimos 30 dias
    print("🚀 Iniciando coleta de dados...")
    collector.update_all_data(days=30)

    # Mostrar resumo
    summary = collector.get_data_summary()
    print("\n📊 Resumo dos dados:")
    print(f"   Bitcoin: {summary['bitcoin_records']} registros")
    if summary['bitcoin_latest']:
        print(f"   Último preço BTC: R$ {summary['bitcoin_latest'][1]:,.2f} ({summary['bitcoin_latest'][0]})")
    print(f"   Ações: {summary['stock_records']} registros de {summary['unique_symbols']} símbolos")
