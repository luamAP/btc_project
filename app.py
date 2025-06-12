from flask import Flask, render_template, request, jsonify
from data_collector import DataCollector
from datetime import datetime, timedelta
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalInvestmentComparator:
    def __init__(self):
        self.collector = DataCollector()

    def calculate_investment_return(self, initial_amount, start_price, end_price):
        """Calcula o retorno do investimento"""
        if start_price is None or end_price is None or start_price <= 0:
            return None

        shares_bought = initial_amount / start_price
        final_value = shares_bought * end_price
        return_percentage = ((final_value - initial_amount) / initial_amount) * 100

        return {
            'initial_amount': initial_amount,
            'shares_bought': shares_bought,
            'final_value': final_value,
            'profit_loss': final_value - initial_amount,
            'return_percentage': return_percentage,
            'start_price': start_price,
            'end_price': end_price
        }

    def compare_investments(self, amount, start_date, end_date):
        """Compara múltiplos investimentos usando dados locais"""
        results = {}

        # Bitcoin
        logger.info(f"Buscando Bitcoin para {start_date}")
        btc_start_price = self.collector.get_bitcoin_price(start_date)
        btc_end_price = self.collector.get_bitcoin_price()

        logger.info(f"Bitcoin - Preço inicial: {btc_start_price}, Preço final: {btc_end_price}")

        if btc_start_price and btc_end_price:
            btc_result = self.calculate_investment_return(amount, btc_start_price, btc_end_price)
            if btc_result:
                results['Bitcoin'] = btc_result

        # Outros ativos
        assets = {
            'Ibovespa (BOVA11)': 'BOVA11.SA',
            'Petrobras (PETR4)': 'PETR4.SA',
            'Itaú (ITUB4)': 'ITUB4.SA',
            'Vale (VALE3)': 'VALE3.SA',
            'Banco do Brasil (BBAS3)': 'BBAS3.SA'
        }

        for asset_name, symbol in assets.items():
            logger.info(f"Buscando {asset_name}")
            start_price = self.collector.get_stock_price(symbol, start_date)
            end_price = self.collector.get_stock_price(symbol)

            logger.info(f"{asset_name} - Preço inicial: {start_price}, Preço final: {end_price}")

            if start_price and end_price:
                result = self.calculate_investment_return(amount, start_price, end_price)
                if result:
                    results[asset_name] = result

        return results

comparator = LocalInvestmentComparator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compare', methods=['POST'])
def compare():
    try:
        data = request.json
        amount = float(data['amount'])
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')

        logger.info(f"Comparando investimento de R$ {amount} de {start_date} até {end_date}")

        results = comparator.compare_investments(amount, start_date, end_date)

        if not results:
            return jsonify({
                'success': False,
                'error': 'Não foi possível obter dados para nenhum ativo. Execute data_collector.py primeiro.'
            })

        logger.info(f"Resultados obtidos: {list(results.keys())}")

        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        logger.error(f"Erro no compare: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        })

@app.route('/bitcoin-price')
def bitcoin_price():
    try:
        price = comparator.collector.get_bitcoin_price()
        return jsonify({
            'success': True,
            'price': price,
            'currency': 'BRL'
        })
    except Exception as e:
        logger.error(f"Erro ao obter preço do Bitcoin: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/data-status')
def data_status():
    """Mostra status dos dados armazenados"""
    try:
        summary = comparator.collector.get_data_summary()
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/update-data')
def update_data():
    """Força atualização dos dados"""
    try:
        comparator.collector.update_all_data(days=7)
        summary = comparator.collector.get_data_summary()
        return jsonify({
            'success': True,
            'message': 'Dados atualizados com sucesso',
            'summary': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🚀 Iniciando aplicação com banco de dados local...")
    print("📊 Certifique-se de executar data_collector.py primeiro")
    print("🌐 Acesse: http://localhost:5000")
    print("📈 Status dos dados: http://localhost:5000/data-status")
    print("🔄 Atualizar dados: http://localhost:5000/update-data")
    app.run(debug=True)
