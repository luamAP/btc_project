#!/usr/bin/env python3
"""
Script de inicialização completa do sistema de comparação de investimentos
"""

import os
import sys
import subprocess
from data_collector import DataCollector

def install_requirements():
    """Instala dependências necessárias"""
    requirements = [
        'flask',
        'yfinance',
        'pandas',
        'requests',
        'beautifulsoup4',
        'schedule',
        'sqlite3'  # Já vem com Python
    ]

    print("📦 Instalando dependências...")
    for req in requirements:
        if req != 'sqlite3':  # sqlite3 já vem com Python
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', req])
                print(f"✅ {req} instalado")
            except subprocess.CalledProcessError:
                print(f"❌ Erro ao instalar {req}")

def setup_database():
    """Configura e popula o banco de dados inicial"""
    print("🗄️ Configurando banco de dados...")

    collector = DataCollector()

    print("📊 Coletando dados iniciais (últimos 30 dias)...")
    collector.update_all_data(days=30)

    summary = collector.get_data_summary()
    print("\n📈 Dados coletados:")
    print(f"   Bitcoin: {summary['bitcoin_records']} registros")
    if summary['bitcoin_latest']:
        print(f"   Último preço BTC: R$ {summary['bitcoin_latest'][1]:,.2f}")
    print(f"   Ações: {summary['stock_records']} registros")
    print(f"   Símbolos únicos: {summary['unique_symbols']}")

def main():
    print("🚀 CONFIGURAÇÃO INICIAL DO SISTEMA")
    print("=" * 50)

    # Verificar se Python está na versão correta
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ é necessário")
        sys.exit(1)

    print("✅ Python version OK")

    # Instalar dependências
    install_requirements()

    # Configurar banco de dados
    setup_database()

    print("\n🎉 CONFIGURAÇÃO CONCLUÍDA!")
    print("\n📋 Próximos passos:")
    print("   1. Execute: python app_local.py")
    print("   2. Acesse: http://localhost:5000")
    print("   3. Para atualizações automáticas: python scheduler.py")
    print("\n📁 Arquivos criados:")
    print("   - investment_data.db (banco de dados)")
    print("   - data_updates.log (log de atualizações)")

if __name__ == "__main__":
    main()
