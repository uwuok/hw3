import re
import sqlite3
import tkinter as tk
import unicodedata
import requests
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox

DB_PATH = 'contacts.db'

def setup_database() -> None:
    '''
    建立資料庫和 contacts table 與相關設定
    '''
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row # 使用字典型別的 cursor
            
            # 執行 SQL 指令
            create_table = """
            CREATE TABLE IF NOT EXISTS contacts (
                lid INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                title TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
            """
            conn.execute(create_table)
            # log
            print('資料表已經成功創建') 
            
    except sqlite3.OperationalError as e:
        print(f'資料庫連接錯誤： {e}')
        raise
    except Exception as e:
        print(f'發生其他錯誤： {e}')
        raise


def save_to_database(data_list: list[dict]) -> None:
    """
    保存資料至資料庫
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row # 使用字典型別的 cursor
            cursor = conn.cursor()
            # 將 data_list 逐個加入至 sql
            for data in data_list:
                name = data['name']
                title = data['title']
                email = data['email']
                # 執行 SQL 指令
                cursor.execute("""
                INSERT OR IGNORE INTO contacts (name, title, email) VALUES (?, ?, ?)
                """, (name, title, email))
            conn.commit()
            # log
            print('資料已保存至資料庫') 
            
    except sqlite3.OperationalError as e:
        print(f'資料庫連接錯誤： {e}')
        raise
    except Exception as e:
        print(f'發生其他錯誤： {e}')
        raise


def parse_contacts() -> list[dict]:
    """解析網頁內容：姓名、職稱、信箱，確保資料正確配對。

    Returns:
        list[dict]: 教授資訊
    """
    text = scrape_contacts()
    
    # 使用正則分段匹配每個成員
    member_pattern = re.compile(
        r'<div class="member_name"><a [^>]*>(?P<name>.*?)</a>.*?'
        r'<div class="member_info_title"><i class="fas fa-briefcase"></i>職稱</div>\s*'
        r'<div class="member_info_content">(?P<title>.*?)</div>.*?'
        r'<div class="member_info_title"><i class="fas fa-envelope"></i>信箱</div>\s*'
        r'(?:<div class="member_info_content"><a href="mailto://[^"]+">(?P<email>[^<]+)</a></div>)?',
        re.DOTALL
    )

    # 將匹配的資料組合成字典
    data_list = []
    for match in member_pattern.finditer(text):
        name = match.group('name') 
        title = match.group('title')
        email = match.group('email') # 如果 email 沒有匹配到，會返回 ''
        data_list.append({'name': name, 'title': title, 'email': email})
    
    save_to_database(data_list)
    return data_list

    
def scrape_contacts() -> str:
    """爬取網頁內容

    Returns:
        str: 網頁內容
    """
    url = entry.get()
    print(f'抓取到的網址：{url}')
    try:
        # https://csie.ncut.edu.tw/content.php?key=86OP82WJQO
        response = requests.get(url, timeout=5) # 添加 timeout 避免長時間等待
        response.raise_for_status() # 如果 status code 為 4xx 或 5xx，會拋出 HTTPError
        print('Request 成功')
        return response.text
    except requests.exceptions.HTTPError as e:
        messagebox.showerror("網頁錯誤", f"HTTP 錯誤：{e}")
    except requests.exceptions.ConnectionError:
        messagebox.showerror("連線錯誤", "無法連接到伺服器，請檢查網路或網址是否正確。")
    except requests.exceptions.Timeout:
        messagebox.showerror("請求逾時", "伺服器未在合理時間內回應，請稍後再試。")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("請求錯誤", f"發生未知的錯誤：{e}")
    return ''


def display_contacts() -> None:
    '''將爬蟲到內容顯示至 GUI 中'''
    
    # 判斷是否有收到 data
    data_list = parse_contacts()
    if not data_list:
        return
    
    def get_display_width(text: str) -> int:
        '''計算字串的顯示寬度，考慮全形和半形字元'''
        return sum(2 if unicodedata.east_asian_width(char) in 'WF' else 1 for char in text)
    
    def pad_to_width(text: str, width: int) -> str:
        '''將字串填充到指定的寬度'''
        current_width = get_display_width(text)
        padding = width - current_width
        return text + ' ' * padding
    
    scrolled_text.delete('1.0', tk.END)
    headers = ['姓名', '職稱', 'Email']
    widths = [16, 32, 32]
    header_line = ''.join(pad_to_width(header, width) for header, width in zip(headers, widths))
    scrolled_text.insert(tk.END, header_line + '\n')
    scrolled_text.insert(tk.END, '-' * sum(widths) + '\n')
    # print(f'{header_line}')
    # print('-' * sum(widths))
    # data_list = parse_contacts()
    for data in data_list:
        # name = data['name']
        # title = data['title']
        # email = data['email']
        line = ''.join(
            pad_to_width(data[key], width)
            for key, width in zip(['name', 'title', 'email'], widths)
        )
        print(line)
        scrolled_text.insert(tk.END, line + '\n')
        

if __name__ == '__main__':
    setup_database()
    
    form = tk.Tk()
    # 視窗標題
    form.title('聯絡資訊爬蟲')
    # 視窗寬高
    form.geometry('640x480')
    # 寬、高可改變
    form.resizable(True, True)

    # 配置列寬比例
    form.columnconfigure(0, weight=0)  # Label 的列（小比例，固定寬度）
    form.columnconfigure(1, weight=2)  # Entry 的列（主要佔用空間）
    form.columnconfigure(2, weight=0)  # Button 的列（小比例，固定寬度）

    # Label 元件 (改用 ttk.Label)
    url_label = ttk.Label(form, text='URL:')
    url_label.grid(row=0, column=0, padx=(5, 10), pady=10, sticky='e')

    # Entry 元件 (改用 ttk.Entry)
    entry = ttk.Entry(form)  # 單行輸入框
    entry.insert(0, 'https://csie.ncut.edu.tw/content.php?key=86OP82WJQO')
    entry.grid(row=0, column=1, padx=10, pady=10, sticky='we')

    # Button 元件 (改用 ttk.Button)
    button = ttk.Button(form, text='抓取', command=display_contacts)
    button.grid(row=0, column=2, padx=10, pady=10, sticky='w')

    # 配置行高比例
    form.rowconfigure(1, weight=1)  # ScrolledText 所在行具有彈性空間

    # ScrolledText 元件 (保留原來的 tkinter.ScrolledText)
    scrolled_text = ScrolledText(form, wrap='word')
    scrolled_text.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')

    # 主循環
    form.mainloop()
