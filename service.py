import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class StockService:
    def __init__(self):
        # Configuração básica de logging para acompanhar o que acontece
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())

    def setup(self):
        """Configura o driver e abre o site inicial."""
        self.logger.info("Iniciando o navegador...")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"  # noqa: E501
        )

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        driver.get("https://economia.uol.com.br/cotacoes/bolsas/")
        return driver

    def search_stock(self, driver, stock_name):
        """Realiza a busca e extrai o título da ação."""
        wait = WebDriverWait(driver, 20)
        self.logger.info(f"Buscando título para: {stock_name}")

        # Tenta fechar banner de cookies
        try:
            cookie_button = driver.find_elements(
                By.XPATH,
                "//button[contains(text(), 'Aceitar') or contains(text(), 'Prosseguir')]",  # noqa: E501
            )
            if cookie_button:
                cookie_button[0].click()
        except Exception:
            pass

        # Localiza o campo de busca
        try:
            input_search = wait.until(
                EC.element_to_be_clickable((By.ID, "filled-normal"))
            )
        except Exception:
            input_search = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "input[placeholder*='BUSCAR AÇÕES']",
                    )
                )
            )

        input_search.click()
        input_search.clear()
        input_search.send_keys(stock_name)

        time.sleep(2)  # Espera as sugestões carregarem
        input_search.send_keys(Keys.ENTER)

        self.logger.info("Aguardando carregamento da página de resultados...")

        # Garante que saímos da página geral do índice e fomos para a da ação
        # O URL de ações no UOL costuma ter /cotacoes/bolsas/acoes/...
        try:
            wait.until(EC.url_contains(stock_name.lower()))
        except Exception:
            self.logger.warning(
                "URL não mudou para a ação esperada, tentando forçar carregamento..."  # noqa: E501
            )

        # Extrai o título e verifica se não é o índice global
        stock_title_element = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "title-name"))
        )
        stock_title = stock_title_element.text

        if "BOVESPA IND" in stock_title.upper() and stock_name.upper() != "IBOV":  # noqa: E501
            self.logger.error(
                "Capturado índice Bovespa em vez da ação específica."
            )
            # Tenta um seletor alternativo mais específico
            # para o ticker se disponível
            try:
                ticker_element = driver.find_element(By.CLASS_NAME, "ticker")
                stock_title = f"{stock_title} ({ticker_element.text})"
            except Exception:
                pass

        logging.info(f"Título encontrado para {stock_name}: {stock_title}")
        return stock_title

    def search_cotation(self, driver, stock_name):
        """Realiza a busca e extrai o valor da cotação."""
        stock_title = self.search_stock(driver, stock_name)

        wait = WebDriverWait(driver, 20)

        self.logger.info(f"Buscando cotação para: {stock_name}")

        # Tenta fechar banner de cookies se existir
        try:
            cookie_button = driver.find_elements(
                By.XPATH,
                "//button[contains(text(), 'Aceitar') or contains(text(), 'Prosseguir')]",  # noqa: E501
            )
            if cookie_button:
                cookie_button[0].click()
        except Exception:
            pass

        # 1. Localiza o campo de busca usando um seletor mais robusto
        # Tenta por ID primeiro, depois por placeholder
        try:
            input_search = wait.until(
                EC.element_to_be_clickable((By.ID, "filled-normal"))
            )
        except Exception:
            input_search = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "input[placeholder*='BUSCAR AÇÕES']",
                    )
                )
            )

        input_search.click()
        input_search.clear()
        input_search.send_keys(stock_name)

        # Aguarda o texto ser inserido no campo antes de dar Enter
        wait.until(EC.text_to_be_present_in_element_value(
            (By.ID, "filled-normal"), stock_name
        ))
        input_search.click()
        input_search.send_keys(Keys.ENTER)

        # 2. Aguarda a página da ação carregar
        self.logger.info("Aguardando carregamento da página de resultados...")
        wait.until(EC.title_contains(stock_title))

        # 3. Extrai o preço
        # O XPATH foi mantido,
        # mas agora com uma espera explícita por visibilidade
        span_price = wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//span[@class='chart-info-val ng-binding']")
            )
        )

        logging.info(f"Preço encontrado para {stock_name}: {span_price.text}")

        return span_price.text

    def teardown(self, driver):
        """Fecha o navegador com segurança."""
        self.logger.info("Fechando o navegador.")
        driver.quit()
