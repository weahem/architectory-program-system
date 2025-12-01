import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from cyberleninka_pdf import CyberLeninkaPDFScraper
import os
import webbrowser

class CyberLeninkaPDFGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CyberLeninka PDF Downloader")
        self.root.geometry("900x600")
        
        self.scraper = CyberLeninkaPDFScraper()
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Header
        header_label = ttk.Label(main_frame, 
                                text="📥 CyberLeninka PDF Downloader", 
                                font=('Arial', 14, 'bold'),
                                foreground='darkblue')
        header_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # Search section
        search_label = ttk.Label(main_frame, 
                                text="Введите поисковый запрос для скачивания PDF статей:", 
                                font=('Arial', 10))
        search_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))
        
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        search_frame.columnconfigure(0, weight=1)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, 
                                     textvariable=self.search_var, 
                                     width=50, 
                                     font=('Arial', 11))
        self.search_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 12))
        self.search_entry.bind('<Return>', lambda e: self.start_download())
        self.search_entry.focus()
        
        self.download_button = ttk.Button(search_frame, 
                                         text="📥 Найти и скачать 12 PDF", 
                                         command=self.start_download, 
                                         width=20,
                                         style='Accent.TButton')
        self.download_button.grid(row=0, column=1)
        
        # Info section
        info_text = ("Программа найдет первые 12 статей по вашему запросу "
                    "и попытается скачать их в формате PDF.\n"
                    "Это может занять 2-3 минуты.")
        info_label = ttk.Label(main_frame, 
                              text=info_text,
                              font=('Arial', 9), 
                              foreground='darkgreen',
                              justify=tk.LEFT)
        info_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        # Progress section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.progress_label = ttk.Label(progress_frame, text="0%", width=4)
        self.progress_label.grid(row=0, column=1, padx=(8, 0))
        
        # Status section
        self.status_var = tk.StringVar(value="Готов к работе")
        status_label = ttk.Label(main_frame, 
                                textvariable=self.status_var, 
                                font=('Arial', 10, 'bold'),
                                foreground='darkblue')
        status_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Statistics
        self.stats_var = tk.StringVar(value="Ожидание запуска...")
        stats_label = ttk.Label(main_frame, 
                               textvariable=self.stats_var, 
                               font=('Arial', 9))
        stats_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10)
        
        self.open_folder_btn = ttk.Button(
            button_frame, 
            text="📁 Открыть папку с PDF", 
            command=self.open_download_folder,
            width=18
        )
        self.open_folder_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.clear_btn = ttk.Button(
            button_frame, 
            text="🔄 Очистить", 
            command=self.clear_interface,
            width=12
        )
        self.clear_btn.grid(row=0, column=1, padx=(0, 10))
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Лог выполнения", padding="8")
        log_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 height=12, 
                                                 width=80, 
                                                 font=('Consolas', 8))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure main frame grid weights
        main_frame.rowconfigure(8, weight=1)
        
        # Create style for accent button
        style = ttk.Style()
        style.configure('Accent.TButton', foreground='white', background='#28a745')
        
    def log_message(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def start_download(self):
        """Start PDF download process"""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Предупреждение", "Введите поисковый запрос")
            return
            
        # Disable button during operation
        self.download_button.config(state='disabled')
        
        # Clear previous logs
        self.log_text.delete(1.0, tk.END)
        
        self.status_var.set("🚀 Начинаем поиск и скачивание PDF...")
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        
        self.log_message("=" * 60)
        self.log_message(f"🎯 ЗАПУСК: поиск и скачивание PDF статей")
        self.log_message(f"🔍 Запрос: '{query}'")
        self.log_message("⏳ Ожидайте, это может занять 2-3 минуты...")
        self.log_message("")
        
        # Run download in separate thread
        thread = threading.Thread(target=self._perform_pdf_download, args=(query,))
        thread.daemon = True
        thread.start()
        
    def _perform_pdf_download(self, query):
        """Perform PDF download operation"""
        try:
            # Update progress
            self.root.after(0, self._update_progress, 10, "Поиск статей...")
            
            # Perform search and download
            downloaded_count = self.scraper.search_and_download_articles(query, 12)
            
            # Operation complete
            self.root.after(0, self._download_complete, downloaded_count)
            
        except Exception as e:
            self.root.after(0, self._download_error, str(e))
            
    def _update_progress(self, value, status):
        """Update progress bar and status"""
        self.progress['value'] = value
        self.progress_label.config(text=f"{int(value)}%")
        self.status_var.set(status)
        
    def _download_complete(self, downloaded_count):
        """Handle download completion"""
        self.progress['value'] = 100
        self.progress_label.config(text="100%")
        
        self.log_message("")
        self.log_message("=" * 60)
        self.log_message(f"🎉 СКАЧИВАНИЕ ЗАВЕРШЕНО!")
        self.log_message(f"📊 Скачано PDF файлов: {downloaded_count}/12")
        self.log_message(f"💾 Папка с файлами: {os.path.abspath(self.scraper.download_dir)}")
        
        self.status_var.set(f"✅ Готово! Скачано: {downloaded_count}/12 PDF")
        self.stats_var.set(f"Результат: {downloaded_count} PDF файлов")
        
        # Re-enable button
        self.download_button.config(state='normal')
        
        # Show completion message
        if downloaded_count > 0:
            messagebox.showinfo("Успех", 
                              f"Скачивание завершено!\n\n"
                              f"Успешно скачано: {downloaded_count} PDF файлов\n"
                              f"Файлы сохранены в папку:\n"
                              f"{os.path.abspath(self.scraper.download_dir)}")
        else:
            messagebox.showwarning("Внимание", 
                                 "Не удалось скачать PDF файлы.\n"
                                 "Возможно, статьи не имеют PDF версий или требуется обход защиты.")
        
    def _download_error(self, error_msg):
        """Handle download errors"""
        self.status_var.set("❌ Ошибка")
        self.log_message(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {error_msg}")
        
        # Re-enable button
        self.download_button.config(state='normal')
        
        messagebox.showerror("Ошибка", 
                           f"Произошла ошибка при скачивании:\n{error_msg}\n\n"
                           "Попробуйте другой запрос или проверьте интернет-соединение.")
        
    def open_download_folder(self):
        """Open download folder in file explorer"""
        try:
            download_path = os.path.abspath(self.scraper.download_dir)
            if os.path.exists(download_path):
                os.startfile(download_path)
                self.log_message(f"📁 Открыта папка: {download_path}")
            else:
                messagebox.showinfo("Информация", "Папка с PDF файлами еще не создана.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {e}")
    
    def clear_interface(self):
        """Clear interface"""
        self.search_var.set("")
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.status_var.set("Готов к работе")
        self.stats_var.set("Ожидание запуска...")
        self.log_text.delete(1.0, tk.END)
        self.log_message("Интерфейс очищен. Введите новый запрос.")
    
    def __del__(self):
        """Cleanup on exit"""
        if hasattr(self, 'scraper'):
            self.scraper.close()

def main():
    root = tk.Tk()
    app = CyberLeninkaPDFGUI(root)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) // 2
    root.geometry(f"+{x}+{y}")
    
    try:
        root.mainloop()
    finally:
        app.scraper.close()

if __name__ == "__main__":
    main()