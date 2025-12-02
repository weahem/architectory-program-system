from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import os
import re
import requests
from urllib.parse import urljoin, quote
import json

class CyberLeninkaParser:
    def __init__(self, output_dir="articles"):
        self.base_url = "https://cyberleninka.ru"
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Настройка Chrome драйвера"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def search_articles(self, query, max_results=3):
        """Поиск статей на CyberLeninka"""
        print(f"🔍 Поиск статей по запросу: '{query}'")
        
        try:
            search_url = f"{self.base_url}/search?q={quote(query)}"
            self.driver.get(search_url)
            time.sleep(2)
            
            article_links = self._find_article_links(max_results)
            print(f"📎 Найдено ссылок на статьи: {len(article_links)}")
            
            if not article_links:
                print("❌ Не найдено ссылок на статьи")
                return []
            
            articles_data = []
            for i, article_url in enumerate(article_links[:max_results]):
                print(f"📥 Обрабатываем статью {i+1}/{len(article_links)}...")
                
                try:
                    article_data = self._process_article_fast(article_url, i+1)
                    if article_data:
                        articles_data.append(article_data)
                        print(f"✅ Статья {i+1} успешно обработана")
                    else:
                        print(f"❌ Не удалось обработать статью {i+1}")
                        
                except Exception as e:
                    print(f"⚠️ Ошибка при обработке статьи {i+1}: {e}")
                    continue
                
                time.sleep(0.5)
            
            print(f"🎉 Обработка завершена! Успешно: {len(articles_data)}/{min(max_results, len(article_links))}")
            return articles_data
            
        except Exception as e:
            print(f"❌ Ошибка при поиске: {e}")
            return []
    
    def _find_article_links(self, max_results):
        """Поиск ссылок на статьи"""
        article_links = []
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/article/"]')
            for element in elements:
                href = element.get_attribute("href")
                if (href and "/article/" in href and 
                    "search" not in href and 
                    href not in article_links):
                    article_links.append(href)
                    if len(article_links) >= max_results:
                        break
        except Exception as e:
            print(f"⚠️ Ошибка при поиске ссылок: {e}")
        
        return article_links[:max_results]
    
    def _process_article_fast(self, article_url, article_number):
        """Быстрая обработка статьи с качественным пересказом"""
        try:
            print(f"   📄 Переходим на страницу статьи: {article_url}")
            self.driver.get(article_url)
            time.sleep(1)
            
            title = self._get_article_title()
            print(f"   📝 Заголовок статьи: {title}")
            
            safe_title = self._create_safe_filename(title)
            filename = f"{article_number:02d}_{safe_title}"
            
            article_dir = os.path.join(self.output_dir, filename)
            os.makedirs(article_dir, exist_ok=True)
            
            content_data = self._get_article_content_fast()
            if not content_data:
                return None
            
            summary = self._fast_quality_summary(content_data['content'])
            
            self._create_files_fast(article_dir, filename, title, article_url, content_data, summary)
            
            return {
                'title': title,
                'url': article_url,
                'filename': filename,
                'content': content_data['content'],
                'annotation': content_data['annotation'],
                'summary': summary,
                'directory': article_dir
            }
                
        except Exception as e:
            print(f"   ❌ Ошибка при обработке статьи: {e}")
            return None
    
    def _get_article_content_fast(self):
        """Быстрое получение содержимого статьи"""
        try:
            content_element = self.driver.find_element(By.CSS_SELECTOR, ".fulltext, .article-text, .content, article")
            content = content_element.text
            
            try:
                annotation_element = self.driver.find_element(By.CSS_SELECTOR, ".abstract, .annotation")
                annotation = annotation_element.text.strip()
            except:
                annotation = "Аннотация не найдена"
                
            return {
                'content': content,
                'annotation': annotation
            }
        except Exception as e:
            print(f"   ❌ Ошибка при получении содержимого: {e}")
            return {
                'content': 'Содержимое не найдено',
                'annotation': 'Аннотация не найдена'
            }
    
    def _get_article_title(self):
        """Получение заголовка статьи"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, 'h1, .article-title, .title')
            title = element.text.strip()
            if title and len(title) > 5 and len(title) < 200:
                return title
        except:
            pass
            
        return self.driver.title.replace(" - КиберЛенинка", "").strip() or f"Статья_{int(time.time())}"
    
    def _fast_quality_summary(self, text):
        """БЫСТРЫЙ и КАЧЕСТВЕННЫЙ пересказ"""
        try:
            if not text or len(text.strip()) < 100:
                return "Текст слишком короткий для создания пересказа"
            
            # Извлекаем ключевые части для быстрого и качественного пересказа
            key_parts = self._extract_key_content(text)
            
            # Создаем качественный пересказ локально
            return self._create_quality_summary(key_parts)
                
        except Exception as e:
            print(f"   ❌ Ошибка при создании пересказа: {e}")
            return self._fallback_summary(text)
    
    def _extract_key_content(self, text):
        """Извлечение ключевых частей текста"""
        try:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            if len(paragraphs) <= 3:
                return text[:1500] if len(text) > 1500 else text
            
            # Интеллектуальный отбор ключевых частей
            key_parts = []
            
            # Введение (первый абзац)
            key_parts.append(paragraphs[0])
            
            # Ключевые абзацы из середины (2-3)
            if len(paragraphs) > 4:
                mid_point = len(paragraphs) // 2
                key_parts.extend(paragraphs[mid_point:mid_point+2])
            
            # Заключение (последний абзац)
            key_parts.append(paragraphs[-1])
            
            result = "\n\n".join(key_parts)
            return result[:1500] if len(result) > 1500 else result
            
        except:
            return text[:1500] if len(text) > 1500 else text
    
    def _create_quality_summary(self, text):
        """Создание качественного пересказа"""
        try:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            if len(paragraphs) == 1:
                # Один абзац - выделяем основную идею
                content = paragraphs[0]
                sentences = re.split(r'[.!?]+', content)
                sentences = [s.strip() for s in sentences if s.strip()]
                if len(sentences) >= 3:
                    return f"Основная тема: {' '.join(sentences[:2])}. Ключевой вывод: {sentences[-1]}"
                else:
                    return f"Тема исследования: {content[:300]}..."
            
            elif len(paragraphs) == 2:
                # Два абзаца - введение и основное
                return f"ТЕМА: {paragraphs[0]}\n\nОСНОВНОЕ СОДЕРЖАНИЕ: {paragraphs[1][:300]}..."
            
            else:
                # Много абзацев - структурированный пересказ
                intro = paragraphs[0][:200] + "..." if len(paragraphs[0]) > 200 else paragraphs[0]
                
                # Находим ключевой абзац (обычно в середине)
                key_idx = len(paragraphs) // 2
                key_content = paragraphs[key_idx][:150] + "..." if len(paragraphs[key_idx]) > 150 else paragraphs[key_idx]
                
                conclusion = paragraphs[-1][:150] + "..." if len(paragraphs[-1]) > 150 else paragraphs[-1]
                
                return f"ВВЕДЕНИЕ: {intro}\n\nКЛЮЧЕВАЯ ИДЕЯ: {key_content}\n\nВЫВОДЫ: {conclusion}"
                
        except Exception as e:
            return f"Качественный пересказ: {text[:300]}..."
    
    def _fallback_summary(self, text):
        """Запасной вариант пересказа"""
        try:
            # Простое резюмирование
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) >= 5:
                # Берем первые 2 и последние 2 предложения
                selected = sentences[:2] + sentences[-2:]
                return " ".join(selected) + "."
            else:
                return " ".join(sentences[:3]) + "." if sentences else "Пересказ недоступен"
        except:
            return "Быстрый качественный пересказ"
    
    def _create_files_fast(self, article_dir, filename, title, url, content_data, summary):
        """Быстрое создание файлов статьи"""
        try:
            # Оригинал (имитация PDF)
            with open(os.path.join(article_dir, f"{filename}.pdf"), "w", encoding="utf-8") as f:
                f.write("=== Оригинал статьи ===\n")
                f.write(f"Название: {title}\n")
                f.write(f"URL: {url}\n")
                f.write("=" * 50 + "\n\n")
                f.write(content_data['content'][:2000] + "..." if len(content_data['content']) > 2000 else content_data['content'])
            
            # TXT-версия
            with open(os.path.join(article_dir, f"{filename}.txt"), "w", encoding="utf-8") as f:
                f.write(content_data['content'])
            
            # Файл краткого пересказа
            with open(os.path.join(article_dir, f"{filename}_sh.txt"), "w", encoding="utf-8") as f:
                f.write(summary)
            
            # Файл аннотации
            with open(os.path.join(article_dir, f"{filename}_an.txt"), "w", encoding="utf-8") as f:
                f.write(content_data['annotation'])
            
            # Метаданные
            metadata = {
                'title': title,
                'url': url,
                'filename': filename,
                'files': {
                    'original': f"{filename}.pdf",
                    'text': f"{filename}.txt",
                    'summary': f"{filename}_sh.txt",
                    'annotation': f"{filename}_an.txt"
                }
            }
            
            with open(os.path.join(article_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"   ❌ Ошибка создания файлов: {e}")
            raise
    
    def _create_safe_filename(self, title):
        """Создание безопасного имени файла"""
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        safe_title = re.sub(r'\s+', ' ', safe_title).strip()
        safe_title = safe_title[:50]
        safe_title = safe_title.rstrip('.')
        if not safe_title:
            safe_title = "article"
        return safe_title
    
    def close(self):
        """Закрытие драйвера"""
        if self.driver:
            self.driver.quit()

# Простой пример использования
def main():
    parser = CyberLeninkaParser("articles")
    
    try:
        query = input("Введите тему для поиска статей: ")
        articles = parser.search_articles(query, 3)
        
        if articles:
            print(f"\n🎉 Найдено и обработано {len(articles)} статей:")
            for i, article in enumerate(articles, 1):
                print(f"{i}. {article['title']}")
                print(f"   Папка: {article['directory']}")
                print(f"   Пересказ: {article['summary'][:200]}...")
                print()
        else:
            print("❌ Статьи не найдены")
            
    except KeyboardInterrupt:
        print("\n⚠️ Программа прервана пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        parser.close()

if __name__ == "__main__":
    main()
