import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
from parser import CyberLeninkaParser

class CyberLeninkaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CyberLeninka Parser")
        self.root.geometry("1000x700")
        
        self.parser = None
        self.articles_data = []
        self.current_article_index = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Панель поиска
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text="Поиск статей:").pack(side=tk.LEFT)
        
        self.search_entry = ttk.Entry(search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<Return>', lambda e: self.start_search())
        
        self.search_button = ttk.Button(search_frame, text="Поиск", command=self.start_search)
        self.search_button.pack(side=tk.LEFT, padx=5)
        
        # Прогресс бар
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        
        # Основная область
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Левая панель - список статей
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        ttk.Label(left_frame, text="Статьи").pack()
        
        self.articles_listbox = tk.Listbox(left_frame, width=40)
        self.articles_listbox.pack(fill=tk.Y, expand=True)
        self.articles_listbox.bind('<<ListboxSelect>>', self.on_article_select)
        
        # Правая панель - предпросмотр
        preview_frame = ttk.Frame(main_frame)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Создание вкладок для разных типов просмотра
        self.notebook = ttk.Notebook(preview_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка оригинала
        self.original_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.original_frame, text="Оригинал")
        self.original_text = tk.Text(self.original_frame, wrap=tk.WORD)
        scrollbar1 = ttk.Scrollbar(self.original_frame, orient=tk.VERTICAL, command=self.original_text.yview)
        self.original_text.configure(yscrollcommand=scrollbar1.set)
        self.original_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Вкладка краткого пересказа
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Краткий пересказ")
        self.summary_text = tk.Text(self.summary_frame, wrap=tk.WORD)
        scrollbar2 = ttk.Scrollbar(self.summary_frame, orient=tk.VERTICAL, command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=scrollbar2.set)
        self.summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Вкладка аннотации
        self.annotation_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.annotation_frame, text="Аннотация")
        self.annotation_text = tk.Text(self.annotation_frame, wrap=tk.WORD)
        scrollbar3 = ttk.Scrollbar(self.annotation_frame, orient=tk.VERTICAL, command=self.annotation_text.yview)
        self.annotation_text.configure(yscrollcommand=scrollbar3.set)
        self.annotation_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar3.pack(side=tk.RIGHT, fill=tk.Y)
        
    def start_search(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Предупреждение", "Введите запрос для поиска")
            return
            
        self.search_button.config(state='disabled')
        self.progress.start()
        
        thread = threading.Thread(target=self.search_articles, args=(query,))
        thread.daemon = True
        thread.start()
        
    def search_articles(self, query):
        try:
            # Создаем парсер
            self.parser = CyberLeninkaParser("articles")
            
            # Поиск статей
            articles = self.parser.search_articles(query, 3)
            
            if not articles:
                self.root.after(0, lambda: messagebox.showinfo("Информация", "Статьи не найдены"))
                return
            
            # Сохраняем данные статей
            self.articles_data = articles
            
            # Обновляем список статей в GUI
            self.root.after(0, self.update_articles_list)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка поиска: {e}"))
        finally:
            self.root.after(0, self.search_complete)
            
    def search_complete(self):
        self.search_button.config(state='normal')
        self.progress.stop()
        
    def update_articles_list(self):
        self.articles_listbox.delete(0, tk.END)
        for article in self.articles_data:
            self.articles_listbox.insert(tk.END, article['title'])
        
    def on_article_select(self, event):
        selection = self.articles_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_article_index = index
            article_data = self.articles_data[index]
            self.load_article_content(article_data)
            
    def load_article_content(self, article_data):
        # Очистка всех текстовых полей
        self.original_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        self.annotation_text.delete(1.0, tk.END)
        
        try:
            # Загрузка содержимого файлов
            article_dir = article_data['directory']
            filename = article_data['filename']
            
            # Загрузка оригинала
            original_path = os.path.join(article_dir, f"{filename}.pdf")
            if os.path.exists(original_path):
                with open(original_path, 'r', encoding='utf-8') as f:
                    self.original_text.insert(1.0, f.read())
            
            # Загрузка пересказа
            summary_path = os.path.join(article_dir, f"{filename}_sh.txt")
            if os.path.exists(summary_path):
                with open(summary_path, 'r', encoding='utf-8') as f:
                    self.summary_text.insert(1.0, f.read())
            
            # Загрузка аннотации
            annotation_path = os.path.join(article_dir, f"{filename}_an.txt")
            if os.path.exists(annotation_path):
                with open(annotation_path, 'r', encoding='utf-8') as f:
                    self.annotation_text.insert(1.0, f.read())
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки содержимого: {e}")

def main():
    root = tk.Tk()
    app = CyberLeninkaGUI(root)
    
    def on_closing():
        if app.parser:
            app.parser.close()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
