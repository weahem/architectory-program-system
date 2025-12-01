from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import os
import re
import requests
from urllib.parse import urljoin, quote
from pathlib import Path

class CyberLeninkaPDFScraper:
    def __init__(self):
        self.base_url = "https://cyberleninka.ru"
        self.download_dir = "downloaded_articles_pdf"
        os.makedirs(self.download_dir, exist_ok=True)
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Настройка Chrome драйвера для скачивания PDF"""
        chrome_options = Options()
        
        # Настройки для скачивания файлов
        prefs = {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,  # Всегда открывать PDF внешне
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def search_and_download_articles(self, query, max_results=12):
        """Поиск и автоматическое скачивание статей в PDF"""
        print(f"🔍 Поиск и скачивание PDF статей по запросу: '{query}'")
        
        try:
            # Поиск статей
            search_url = f"{self.base_url}/search?q={quote(query)}"
            self.driver.get(search_url)
            time.sleep(8)
            
            # Сохраняем скриншот для отладки
            self.driver.save_screenshot("search_page.png")
            print("💾 Скриншот страницы поиска сохранен")
            
            # Поиск ссылок на статьи
            article_links = self._find_article_links(max_results)
            print(f"📎 Найдено ссылок на статьи: {len(article_links)}")
            
            if not article_links:
                print("❌ Не найдено ссылок на статьи")
                return 0
            
            # Скачивание PDF статей
            downloaded_count = 0
            for i, article_url in enumerate(article_links):
                print(f"📥 Обрабатываем статью {i+1}/{len(article_links)}...")
                
                try:
                    success = self._download_article_pdf(article_url, i+1)
                    if success:
                        downloaded_count += 1
                        print(f"✅ PDF статьи {i+1} успешно скачан")
                    else:
                        print(f"❌ Не удалось скачать PDF статьи {i+1}")
                        
                except Exception as e:
                    print(f"⚠️ Ошибка при обработке статьи {i+1}: {e}")
                    continue
                
                # Пауза между запросами
                time.sleep(2)
            
            print(f"🎉 Скачивание завершено! Успешно: {downloaded_count}/{len(article_links)}")
            return downloaded_count
            
        except Exception as e:
            print(f"❌ Ошибка при поиске и скачивании: {e}")
            return 0
    
    def _find_article_links(self, max_results):
        """Поиск ссылок на статьи"""
        article_links = []
        
        # Ищем ссылки на статьи
        try:
            # Метод 1: Поиск по селекторам
            selectors = [
                'a[href*="/article/"]',
                '.search-result a',
                '.article a',
                '.item a',
                '.card a',
                'h2 a',
                'h3 a'
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        href = element.get_attribute("href")
                        if (href and "/article/" in href and 
                            "search" not in href and 
                            href not in article_links):
                            article_links.append(href)
                            if len(article_links) >= max_results:
                                return article_links
                except:
                    continue
        except Exception as e:
            print(f"⚠️ Ошибка при поиске ссылок: {e}")
        
        # Если не нашли достаточно ссылок, используем альтернативный метод
        if len(article_links) < max_results:
            article_links.extend(self._alternative_find_links(max_results - len(article_links)))
        
        return article_links[:max_results]
    
    def _alternative_find_links(self, max_links):
        """Альтернативный метод поиска ссылок"""
        links = []
        try:
            all_anchors = self.driver.find_elements(By.TAG_NAME, "a")
            for anchor in all_anchors:
                href = anchor.get_attribute("href")
                if (href and "/article/" in href and 
                    "search" not in href and 
                    href not in links):
                    links.append(href)
                    if len(links) >= max_links:
                        break
        except:
            pass
        return links
    
    def _download_article_pdf(self, article_url, article_number):
        """Скачивание PDF статьи"""
        try:
            print(f"   📄 Переходим на страницу статьи: {article_url}")
            self.driver.get(article_url)
            time.sleep(5)
            
            # Сохраняем скриншот страницы статьи
            self.driver.save_screenshot(f"article_page_{article_number}.png")
            
            # Получаем заголовок статьи для имени файла
            title = self._get_article_title()
            print(f"   📝 Заголовок статьи: {title}")
            
            # Ищем кнопку/ссылку скачивания PDF
            pdf_url = self._find_pdf_link()
            
            if pdf_url:
                print(f"   📎 Найден PDF: {pdf_url}")
                return self._download_pdf_file(pdf_url, title, article_number)
            else:
                print(f"   ❌ PDF ссылка не найдена, пробуем альтернативные методы...")
                return self._try_alternative_pdf_download(title, article_number)
                
        except Exception as e:
            print(f"   ❌ Ошибка при скачивании PDF: {e}")
            return False
    
    def _find_pdf_link(self):
        """Поиск ссылки на PDF"""
        # Популярные селекторы для кнопок скачивания PDF на CyberLeninka
        pdf_selectors = [
            'a[href*=".pdf"]',
            'a[href*="/pdf/"]',
            'a[href*="download"]',
            '.pdf-download',
            '.download',
            '[class*="pdf"]',
            '[class*="download"]',
            'button[onclick*="pdf"]',
            'button[onclick*="download"]'
        ]
        
        for selector in pdf_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    # Пробуем получить ссылку разными способами
                    pdf_url = self._get_pdf_url_from_element(element)
                    if pdf_url:
                        return pdf_url
            except:
                continue
        
        return None
    
    def _get_pdf_url_from_element(self, element):
        """Получение PDF URL из элемента"""
        try:
            # Способ 1: Прямая ссылка из href
            href = element.get_attribute("href")
            if href and (".pdf" in href or "/pdf/" in href):
                return href if href.startswith("http") else urljoin(self.base_url, href)
            
            # Способ 2: Ссылка из onclick
            onclick = element.get_attribute("onclick")
            if onclick:
                # Ищем URL в onclick
                url_match = re.search(r"['\"](https?://[^'\"]+\.pdf)['\"]", onclick)
                if url_match:
                    return url_match.group(1)
                
                # Ищем относительные пути
                rel_match = re.search(r"['\"](/[^'\"]+\.pdf)['\"]", onclick)
                if rel_match:
                    return urljoin(self.base_url, rel_match.group(1))
            
            # Способ 3: data-атрибуты
            data_url = element.get_attribute("data-url") or element.get_attribute("data-href")
            if data_url and (".pdf" in data_url or "/pdf/" in data_url):
                return data_url if data_url.startswith("http") else urljoin(self.base_url, data_url)
                
        except:
            pass
        
        return None
    
    def _try_alternative_pdf_download(self, title, article_number):
        """Альтернативные методы скачивания PDF"""
        try:
            # Метод 1: Пробуем стандартный путь PDF на CyberLeninka
            current_url = self.driver.current_url
            if "/article/" in current_url:
                # Пробуем стандартный путь к PDF
                article_id = current_url.split("/article/")[-1]
                pdf_url = f"{self.base_url}/article/{article_id}.pdf"
                
                print(f"   🔄 Пробуем стандартный PDF путь: {pdf_url}")
                if self._download_pdf_file(pdf_url, title, article_number):
                    return True
            
            # Метод 2: Ищем в исходном коде страницы
            page_source = self.driver.page_source
            pdf_matches = re.findall(r'https?://[^"\']+\.pdf', page_source)
            for pdf_url in pdf_matches:
                if "cyberleninka" in pdf_url:
                    print(f"   🔄 Найден PDF в исходном коде: {pdf_url}")
                    if self._download_pdf_file(pdf_url, title, article_number):
                        return True
            
            # Метод 3: Пробуем через API или другие пути
            pdf_urls_to_try = [
                current_url.replace("/article/", "/pdf/"),
                current_url + ".pdf",
                current_url + "/download"
            ]
            
            for pdf_url in pdf_urls_to_try:
                print(f"   🔄 Пробуем альтернативный URL: {pdf_url}")
                if self._download_pdf_file(pdf_url, title, article_number):
                    return True
                    
        except Exception as e:
            print(f"   ❌ Альтернативные методы не сработали: {e}")
        
        return False
    
    def _download_pdf_file(self, pdf_url, title, article_number):
        """Скачивание PDF файла"""
        try:
            # Создаем безопасное имя файла
            safe_title = self._create_safe_filename(title)
            filename = f"{article_number:02d}_{safe_title}.pdf"
            filepath = os.path.join(self.download_dir, filename)
            
            print(f"   💾 Скачиваем PDF в: {filename}")
            
            # Используем requests для скачивания
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': self.driver.current_url
            }
            
            response = requests.get(pdf_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Сохраняем файл
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Проверяем, что файл скачан и не пустой
            if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                print(f"   ✅ PDF успешно сохранен: {filename} ({os.path.getsize(filepath)} байт)")
                return True
            else:
                print(f"   ❌ Файл слишком маленький или поврежден")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка скачивания PDF: {e}")
            return False
    
    def _get_article_title(self):
        """Получение заголовка статьи"""
        try:
            # Пробуем разные селекторы для заголовка
            title_selectors = [
                'h1',
                '.article-title',
                '.title',
                'h2',
                '[class*="title"]'
            ]
            
            for selector in title_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    title = element.text.strip()
                    if title and len(title) > 5:
                        return title
                except:
                    continue
            
            # Если не нашли, используем title страницы
            return self.driver.title.replace(" - КиберЛенинка", "").strip()
            
        except:
            return f"Статья_{int(time.time())}"
    
    def _create_safe_filename(self, title):
        """Создание безопасного имени файла"""
        # Удаляем запрещенные символы
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        # Заменяем множественные пробелы
        safe_title = re.sub(r'\s+', ' ', safe_title).strip()
        # Ограничиваем длину
        safe_title = safe_title[:100]
        return safe_title
    
    def close(self):
        """Закрытие драйвера"""
        if self.driver:
            self.driver.quit()

# Тестовый скрипт
def test_pdf_download():
    """Тестирование скачивания PDF"""
    print("🚀 Тестируем скачивание PDF статей...")
    
    scraper = CyberLeninkaPDFScraper()
    
    try:
        query = "машинное обучение"
        result = scraper.search_and_download_articles(query, 3)
        print(f"📊 Результат: скачано {result} PDF файлов")
        
        # Показываем скачанные файлы
        download_dir = os.path.abspath(scraper.download_dir)
        if os.path.exists(download_dir):
            files = os.listdir(download_dir)
            print(f"📁 Файлы в папке {download_dir}:")
            for file in files:
                filepath = os.path.join(download_dir, file)
                size = os.path.getsize(filepath)
                print(f"   📄 {file} ({size} байт)")
                
    finally:
        scraper.close()

if __name__ == "__main__":
    test_pdf_download()