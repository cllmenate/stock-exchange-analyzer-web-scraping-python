import logging
from service import StockService

# Configuração básica de logging para acompanhar o que acontece
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def main():
    driver = None
    try:
        stock_service = StockService()
        driver = stock_service.setup()
        stock_name = "PETR4"
        stock_cotation = stock_service.search_cotation(driver, stock_name)
        print(f"\n✅ Cotação atual de {stock_name}: {stock_cotation}")
    except Exception as e:
        logging.error(f"Erro durante a execução: {e}")
    finally:
        if driver:
            stock_service.teardown(driver)


if __name__ == "__main__":
    main()
