import schedule
import time
import logging
from data_collector import DataCollector
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_updates.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataScheduler:
    def __init__(self):
        self.collector = DataCollector()

    def daily_update(self):
        """Atualização diária - coleta dados dos últimos 2 dias"""
        try:
            logger.info("🔄 Iniciando atualização diária...")
            self.collector.update_all_data(days=2)

            # Mostrar resumo após atualização
            summary = self.collector.get_data_summary()
            logger.info(f"✅ Atualização concluída - BTC: {summary['bitcoin_records']} registros, Ações: {summary['stock_records']} registros")

        except Exception as e:
            logger.error(f"❌ Erro na atualização diária: {e}")

    def weekly_update(self):
        """Atualização semanal - coleta dados dos últimos 7 dias"""
        try:
            logger.info("🔄 Iniciando atualização semanal...")
            self.collector.update_all_data(days=7)
            logger.info("✅ Atualização semanal concluída")

        except Exception as e:
            logger.error(f"❌ Erro na atualização semanal: {e}")

    def monthly_update(self):
        """Atualização mensal - coleta dados dos últimos 30 dias"""
        try:
            logger.info("🔄 Iniciando atualização mensal...")
            self.collector.update_all_data(days=30)
            logger.info("✅ Atualização mensal concluída")

        except Exception as e:
            logger.error(f"❌ Erro na atualização mensal: {e}")

    def start_scheduler(self):
        """Inicia o agendador"""
        logger.info("🚀 Iniciando agendador de atualizações...")

        # Agendar atualizações
        schedule.every().day.at("09:00").do(self.daily_update)      # Todo dia às 9h
        schedule.every().day.at("18:00").do(self.daily_update)      # Todo dia às 18h
        schedule.every().sunday.at("08:00").do(self.weekly_update)  # Domingo às 8h
        schedule.every().month.do(self.monthly_update)              # Todo mês

        logger.info("📅 Agendamentos configurados:")
        logger.info("   - Atualização diária: 09:00 e 18:00")
        logger.info("   - Atualização semanal: Domingo 08:00")
        logger.info("   - Atualização mensal: Todo mês")

        # Loop principal
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto

if __name__ == "__main__":
    scheduler = DataScheduler()

    # Fazer uma atualização inicial
    print("🔄 Fazendo atualização inicial...")
    scheduler.daily_update()

    # Iniciar agendador
    scheduler.start_scheduler()
