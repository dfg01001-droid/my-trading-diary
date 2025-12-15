import flet as ft
import sqlite3
import os
import csv
import random
from datetime import datetime

# =========================================================================
# 1. 資料庫與路徑設定
# =========================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.expanduser("~")
DB_FILE = os.path.join(USER_DATA_DIR, "trading_data.db")

# 設定圖示路徑
ICON_SRC = "/icon.jpg" 
LOCAL_ICON_PATH = os.path.join(BASE_DIR, "assets", "icon.jpg")

PIG_QUOTES = [
    "狼若回頭不是報恩就是報仇，我若回頭不是爆單就是爆倉！",
    "站在風口上，黑豬都能飛上天。",
    "不見棺材不掉淚，不打停利不出場！",
    "賺錢有可能是錯的，賠錢有可能是對的。",
    "當資金來源有壓力，再好的技術都沒有用。",
    "風報比比什麼都重要。",
    "浮盈不是盈，浮虧不是虧。",
    "機會是等來的，輕倉才能有耐心。",
    "重倉交易不可能有耐心等待的。",
    "歷史總是不斷地重演相似的行情。",
    "危機總是在你慶祝勝利之後到來。",
    "紀律 +1！離財富自由更近一步了！",
    "忍住不追高，就是賺錢！",
    "今天手氣不錯，但別忘了設停損！",
    "本金第一，賺錢第二！",
    "休息也是一種交易策略。",
    "聽神豬的：不要All-in，會睡不著。",
    "高手死於抄底，大師死於槓桿。",
    "你是來投資的，不是來賭博的！",
    "不錯喔！保持這個節奏！",
    "看我的皇冠，想要嗎？守紀律就有！",
    "耐心！耐心！耐心！",
    "這一單忍住了？好樣的！",
    "交易不是百米賽跑，是馬拉松。",
    "讓利潤奔跑，讓虧損截斷！",
    "不要預測行情，要跟隨行情。",
    "最好的操作，有時候就是「不操作」。",
    "每天進步 1%，一年後你會感謝自己。",
    "相信你的交易系統，別相信直覺。",
    "🐷：給你好棒棒印章！",
    "不要盯盤了，去喝杯水吧。",
    "再亂下單，我就把你帳戶吃掉！",
    "手綁起來！不要亂點！",
    "你看起來像是在賭博，不像在交易。",
    "這筆單有經過大腦嗎？還是用腳趾下的？",
    "今天賠錢了嗎？沒關係，明天繼續（誤）。",
    "市場永遠是對的，錯的都是你的單。",
    "別當韭菜，要當割韭菜的那把鐮刀。",
    "你的對手是華爾街，你確定要這樣下？",
    "下單前深呼吸，想想我的黑豬臉。",
    "停損很痛，但爆倉會讓你想哭。",
    "不要跟股票談戀愛，該分就分！",
    "賺錢的時候像神，賠錢的時候像...豬？",
    "FOMO 是通往地獄的特快車。",
    "你是在交易，還是在尋求刺激？",
    "承認吧，你剛才是不是想凹單？",
    "停損就像呼吸，很正常，別難過。",
    "贏家不是賺最多的，是活最久的。",
    "不要為了交易而交易，要為了賺錢而交易。",
    "想一夜致富？去買樂透比較快。",
    "市場不欠你錢，別總想著報仇。",
    "🐷 噗噗！",
    "給我更多金幣！(嚼嚼)",
    "你今天看過幾次我的帥臉了？",
    "比起看盤，我更喜歡看你守紀律的樣子。",
    "我的皇冠好像歪了，幫我扶一下。",
    "有人說我是豬？我可是招財神獸！",
    "多按幾下大拇指，運氣會變好喔（迷信）。",
    "保持微笑，就算停損也要笑著離場。",
    "記得吃飯，身體健康才能看盤。",
    "這裡沒有明牌，只有紀律！"
]

class DBManager:
    def __init__(self):
        # 【修正】先初始化為 None，防止 init 失敗後屬性不存在
        self.cursor = None
        self.conn = None
        self.error_msg = None
        
        try:
            db_dir = os.path.dirname(DB_FILE)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.create_tables()
            self.check_and_migrate()
        except Exception as e:
            # 記錄詳細錯誤與路徑
            self.error_msg = f"資料庫錯誤: {str(e)}\n路徑: {DB_FILE}"
            print(self.error_msg)

    def create_tables(self):
        if not self.cursor: return
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pair TEXT,
                direction TEXT,
                lots REAL,
                entry_price REAL,
                exit_price REAL,
                pnl_usd REAL,
                entry_time TEXT,
                note TEXT DEFAULT ''
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                contract_forex REAL DEFAULT 100000.0,
                contract_gold REAL DEFAULT 100.0,
                contract_crypto REAL DEFAULT 1.0,
                thumbs_up_count INTEGER DEFAULT 0
            )
        ''')
        self.cursor.execute('SELECT count(*) FROM settings')
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute('INSERT INTO settings (id, contract_forex, contract_gold, contract_crypto, thumbs_up_count) VALUES (1, 100000.0, 100.0, 1.0, 0)')
            self.conn.commit()
        self.conn.commit()

    def check_and_migrate(self):
        if not self.cursor: return
        try:
            self.cursor.execute("SELECT note FROM trades LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE trades ADD COLUMN note TEXT DEFAULT ''")
            self.conn.commit()
        try:
            self.cursor.execute("SELECT contract_crypto FROM settings LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE settings ADD COLUMN contract_crypto REAL DEFAULT 1.0")
            self.conn.commit()
        try:
            self.cursor.execute("SELECT thumbs_up_count FROM settings LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE settings ADD COLUMN thumbs_up_count INTEGER DEFAULT 0")
            self.conn.commit()

    def get_settings(self):
        # 【修正】防崩潰檢查
        if not self.cursor: 
            return {"forex": 100000.0, "gold": 100.0, "crypto": 1.0, "thumbs": 0}
        
        try:
            self.cursor.execute('SELECT contract_forex, contract_gold, contract_crypto, thumbs_up_count FROM settings WHERE id=1')
            row = self.cursor.fetchone()
            if row:
                crypto = row[2] if len(row) > 2 else 1.0
                thumbs = row[3] if len(row) > 3 else 0
                return {"forex": row[0], "gold": row[1], "crypto": crypto, "thumbs": thumbs}
        except:
            pass
        return {"forex": 100000.0, "gold": 100.0, "crypto": 1.0, "thumbs": 0}

    def update_settings(self, forex, gold, crypto):
        if not self.cursor: return
        self.cursor.execute('UPDATE settings SET contract_forex=?, contract_gold=?, contract_crypto=? WHERE id=1', (forex, gold, crypto))
        self.conn.commit()

    def increment_thumbs_up(self):
        if not self.cursor: return 0
        self.cursor.execute('UPDATE settings SET thumbs_up_count = thumbs_up_count + 1 WHERE id=1')
        self.conn.commit()
        self.cursor.execute('SELECT thumbs_up_count FROM settings WHERE id=1')
        return self.cursor.fetchone()[0]

    def reset_thumbs_up(self):
        if not self.cursor: return 0
        self.cursor.execute('UPDATE settings SET thumbs_up_count = 0 WHERE id=1')
        self.conn.commit()
        return 0

    def add_trade(self, data):
        if not self.cursor: return False
        try:
            self.cursor.execute('''
                INSERT INTO trades (pair, direction, lots, entry_price, exit_price, pnl_usd, entry_time, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, '')
            ''', (data['pair'], data['direction'], data['lots'], data['entry_price'], data['exit_price'], data['pnl_usd'], str(datetime.now())))
            self.conn.commit()
            return True
        except:
            return False

    def get_all_trades(self):
        if not self.cursor: return []
        self.cursor.execute('SELECT * FROM trades ORDER BY id DESC')
        rows = self.cursor.fetchall()
        trades = []
        col_names = [description[0] for description in self.cursor.description]
        for r in rows:
            trade_dict = dict(zip(col_names, r))
            if 'note' not in trade_dict or trade_dict['note'] is None:
                trade_dict['note'] = ""
            trades.append(trade_dict)
        return trades

    def get_trade_by_id(self, trade_id):
        if not self.cursor: return None
        self.cursor.execute('SELECT * FROM trades WHERE id=?', (trade_id,))
        row = self.cursor.fetchone()
        if row:
            col_names = [description[0] for description in self.cursor.description]
            trade_dict = dict(zip(col_names, row))
            if 'note' not in trade_dict or trade_dict['note'] is None:
                trade_dict['note'] = ""
            return trade_dict
        return None

    def update_trade_note(self, trade_id, note_content):
        if not self.cursor: return
        self.cursor.execute('UPDATE trades SET note=? WHERE id=?', (note_content, trade_id))
        self.conn.commit()

    def delete_trade(self, trade_id):
        if not self.cursor: return
        self.cursor.execute('DELETE FROM trades WHERE id=?', (trade_id,))
        self.conn.commit()

db = DBManager()

# =========================================================================
# 2. Flet APP 介面
# =========================================================================

def main(page: ft.Page):
    page.title = "招財黑豬交易日記 (V7.2)"
    page.theme_mode = "LIGHT"
    page.window_width = 400
    page.window_height = 800
    
    snack_bar = ft.SnackBar(content=ft.Text(""))
    page.overlay.append(snack_bar)

    def show_msg(msg, color="green"):
        snack_bar.content.value = msg
        snack_bar.bgcolor = color
        snack_bar.open = True
        page.update()

    # --- 圖示處理 ---
    has_icon = os.path.exists(LOCAL_ICON_PATH)
    if has_icon:
        page.window_icon = ICON_SRC
        avatar_content = ft.Image(src=ICON_SRC, width=40, height=40, fit="cover", border_radius=20)
    else:
        avatar_content = ft.Icon(name="face", size=30)

    # --- 大圖 Dialog ---
    dlg_full_avatar = ft.AlertDialog(
        content=ft.Container(
            content=ft.Image(src=ICON_SRC, fit="contain") if has_icon else ft.Text("找不到圖片"),
            alignment=ft.alignment.center,
            height=400,
        ),
        actions=[ft.TextButton("關閉", on_click=lambda e: close_avatar_dlg(e))],
        actions_alignment="center"
    )
    page.overlay.append(dlg_full_avatar)

    def close_avatar_dlg(e):
        dlg_full_avatar.open = False
        page.update()

    def show_full_avatar(e):
        if has_icon:
            dlg_full_avatar.open = True
            page.update()
        else:
            show_msg("找不到圖片", "red")

    page.appbar = ft.AppBar(
        leading=ft.Container(
            content=avatar_content,
            padding=5,
            on_click=show_full_avatar,
            ink=True,
            border_radius=20
        ),
        leading_width=60,
        title=ft.Text("交易日記", weight="bold", color="black"),
        center_title=True,
        bgcolor="#e0e0e0",
    )

    # --- Tab 1: 輸入 ---
    def on_menu_item_click(e):
        txt_pair.value = e.control.data
        page.update()

    common_pairs = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "US30", "NAS100", "BTCUSD", "ETHUSD", "SOLUSD"]
    menu_items = [ft.PopupMenuItem(text=p, data=p, on_click=on_menu_item_click) for p in common_pairs]

    txt_pair = ft.TextField(label="商品", suffix=ft.PopupMenuButton(icon="arrow_drop_down", items=menu_items))
    dd_direction = ft.Dropdown(label="方向", options=[ft.dropdown.Option("BUY"), ft.dropdown.Option("SELL")], value="BUY")
    txt_lots = ft.TextField(label="手數", value="0.01", keyboard_type="number")
    txt_entry = ft.TextField(label="進場價", keyboard_type="number")
    txt_exit = ft.TextField(label="出場價", keyboard_type="number")
    lbl_pnl_preview = ft.Text("預估: $0.00", size=16, weight="bold")

    def save_trade_click(e):
        try:
            pair = txt_pair.value.upper().strip() if txt_pair.value else ""
            if not pair: return show_msg("請輸入商品", "red")
            lots = float(txt_lots.value)
            entry = float(txt_entry.value)
            exit_p = float(txt_exit.value)
            
            settings = db.get_settings()
            contract = settings['gold'] if "XAU" in pair or "GOLD" in pair else (settings['crypto'] if any(k in pair for k in ["BTC","ETH","SOL"]) else settings['forex'])
            pnl = (exit_p - entry if dd_direction.value=="BUY" else entry - exit_p) * lots * contract
            
            data = {'pair': pair, 'direction': dd_direction.value, 'lots': lots, 'entry_price': entry, 'exit_price': exit_p, 'pnl_usd': pnl}
            if db.add_trade(data):
                show_msg(f"保存成功! ${pnl:.2f}")
                refresh_all_data()
            else:
                show_msg("保存失敗 (DB錯誤)", "red")
        except:
            show_msg("輸入錯誤", "red")

    tab_entry = ft.Container(
        content=ft.Column([
            ft.Text("新增交易", size=20, weight="bold"),
            txt_pair, dd_direction, txt_lots, txt_entry, txt_exit,
            ft.ElevatedButton("💾 保存交易", on_click=save_trade_click, height=50, bgcolor="blue", color="white"),
            lbl_pnl_preview
        ], spacing=15, scroll="auto"), 
        padding=20
    )

    # --- Tab 2: 紀錄 ---
    lv_history = ft.ListView(expand=True, spacing=10, padding=20)
    txt_detail_note = ft.TextField(label="心得", multiline=True, min_lines=5)
    current_trade_id = None
    
    dlg_detail = ft.AlertDialog(
        title=ft.Text("詳細資料"),
        content=ft.Column([ft.Text("載入中...")], height=400, scroll="adaptive"),
        actions=[ft.ElevatedButton("保存心得", on_click=lambda e: save_note_click(e))]
    )
    page.overlay.append(dlg_detail)

    def save_note_click(e):
        if current_trade_id:
            db.update_trade_note(current_trade_id, txt_detail_note.value)
            show_msg("已更新")
            dlg_detail.open = False
            page.update()
            refresh_all_data()

    def open_detail_click(e):
        nonlocal current_trade_id
        current_trade_id = e.control.data
        trade = db.get_trade_by_id(current_trade_id)
        if not trade: return
        txt_detail_note.value = trade['note']
        pnl = trade['pnl_usd']
        color = "green" if pnl >= 0 else "red"
        
        dlg_detail.content.controls = [
            ft.Text(f"{trade['pair']} ({trade['direction']})", size=22, weight="bold", color=color),
            ft.Divider(),
            ft.Text(f"時間: {trade['entry_time'][:16]}"),
            ft.Text(f"進場: {trade['entry_price']} / 出場: {trade['exit_price']}"),
            ft.Text(f"手數: {trade['lots']} / 損益: ${pnl:.2f}", weight="bold", color=color),
            ft.Divider(),
            txt_detail_note
        ]
        dlg_detail.open = True
        page.update()

    def delete_trade_click(e):
        db.delete_trade(e.control.data)
        refresh_all_data()
        show_msg("已刪除", "orange")

    def load_history_data():
        lv_history.controls.clear()
        try:
            trades = db.get_all_trades()
            if not trades:
                lv_history.controls.append(ft.Text("尚無紀錄"))
            for t in trades:
                color = "green" if t['pnl_usd'] >= 0 else "red"
                row = ft.Container(
                    content=ft.Row([
                        ft.Icon("trending_up" if t['pnl_usd']>=0 else "trending_down", color=color),
                        ft.Column([
                            ft.Text(f"{t['pair']} {t['direction']}", weight="bold"),
                            ft.Text(f"${t['pnl_usd']:.2f}", color=color)
                        ], expand=True),
                        ft.IconButton(icon="edit", icon_color="blue", data=t['id'], on_click=open_detail_click),
                        ft.IconButton(icon="delete", icon_color="red", data=t['id'], on_click=delete_trade_click),
                    ]),
                    padding=10, bgcolor="white", border_radius=5
                )
                lv_history.controls.append(row)
        except Exception as e:
            lv_history.controls.append(ft.Text(f"Error: {e}"))
        page.update()

    # --- 紀律計數器邏輯 ---
    lbl_thumbs = ft.Text("0", size=40, weight="bold", color="blue")

    def thumbs_click(e):
        lbl_thumbs.value = str(db.increment_thumbs_up())
        quote = random.choice(PIG_QUOTES)
        show_msg(f"🐷：{quote}", "blue")
        page.update()
    
    def reset_thumbs(e):
        lbl_thumbs.value = str(db.reset_thumbs_up())
        show_msg("紀律重置！重新做人！", "orange")
        page.update()

    thumbs_section = ft.Container(
        content=ft.Column([
            ft.Text("🛡️ 紀律計數器", size=20, weight="bold"),
            ft.Text("點擊大拇指，聽聽黑豬的建議！", size=12, color="grey"),
            ft.Row([
                ft.IconButton(icon="thumb_up", icon_size=50, icon_color="blue", on_click=thumbs_click),
                lbl_thumbs,
                ft.IconButton(icon="refresh", icon_size=20, icon_color="grey", on_click=reset_thumbs)
            ], alignment="center")
        ], horizontal_alignment="center"),
        padding=20, bgcolor="#e3f2fd", border_radius=15, margin=ft.margin.only(bottom=20)
    )

    # --- Tab 3: 統計 ---
    stats_container = ft.Column(spacing=20, scroll="auto")
    dlg_help = ft.AlertDialog(title=ft.Text("說明"), content=ft.Text(""))
    page.overlay.append(dlg_help)

    def show_help_click(e):
        t, txt = e.control.data
        dlg_help.title.value = t
        dlg_help.content.value = txt
        dlg_help.open = True
        page.update()

    def create_stat_card(title, value, color, help_text):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=14, color="grey"),
                ft.Text(value, size=22, weight="bold", color=color),
                ft.IconButton(icon="help_outline", icon_size=20, icon_color="blue", data=(title, help_text), on_click=show_help_click)
            ], alignment="center"),
            width=150, padding=10, bgcolor="#f0f0f0", border_radius=10
        )

    def load_stats_data():
        trades = db.get_all_trades()
        stats_container.controls.clear()
        stats_container.controls.append(thumbs_section)
        
        net = sum(t['pnl_usd'] for t in trades)
        wins = [t for t in trades if t['pnl_usd'] > 0]
        rate = (len(wins)/len(trades)*100) if trades else 0
        
        row1 = ft.Row([create_stat_card("淨利", f"${net:.2f}", "green" if net>=0 else "red", "淨利說明"), create_stat_card("勝率", f"{rate:.1f}%", "blue", "勝率說明")], alignment="center")
        
        stats_container.controls.extend([
            ft.Divider(),
            ft.Text("帳戶數據", size=20, weight="bold", text_align="center"),
            row1
        ])
        page.update()

    tab_stats = ft.Container(content=stats_container, padding=20)

    # --- Tab 4: 設定 ---
    txt_forex = ft.TextField(label="外匯合約")
    txt_gold = ft.TextField(label="黃金合約")
    txt_crypto = ft.TextField(label="加密貨幣合約")

    def save_set_click(e):
        try:
            db.update_settings(float(txt_forex.value), float(txt_gold.value), float(txt_crypto.value))
            show_msg("已更新")
        except:
            show_msg("錯誤", "red")

    def export_csv_click(e):
        try:
            trades = db.get_all_trades()
            if not trades: return show_msg("沒資料", "red")
            path = os.path.join(USER_DATA_DIR, f"export_{datetime.now().strftime('%Y%m%d')}.csv")
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f)
                w.writerow(["ID", "Pair", "Dir", "Lots", "Entry", "Exit", "PnL", "Time", "Note"])
                for t in trades:
                    w.writerow([t['id'], t['pair'], t['direction'], t['lots'], t['entry_price'], t['exit_price'], t['pnl_usd'], t['entry_time'], t['note']])
            show_msg(f"匯出至: {path}")
        except Exception as ex:
            show_msg(f"失敗: {ex}", "red")

    def load_settings_data():
        s = db.get_settings()
        txt_forex.value = str(s['forex'])
        txt_gold.value = str(s['gold'])
        txt_crypto.value = str(s['crypto'])
        lbl_thumbs.value = str(s['thumbs'])

    tab_settings = ft.Container(
        content=ft.Column([
            ft.Text("合約設定", size=20, weight="bold"),
            txt_forex, txt_gold, txt_crypto,
            ft.ElevatedButton("更新設定", on_click=save_set_click),
            ft.Divider(),
            ft.Text("資料管理", size=20, weight="bold"),
            ft.ElevatedButton("匯出 CSV", icon="download", on_click=export_csv_click, bgcolor="green", color="white")
        ], spacing=20, scroll="auto"),
        padding=20
    )

    def refresh_all_data():
        load_history_data()
        load_stats_data()
        load_settings_data()

    t = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="輸入", icon="edit", content=tab_entry),
            ft.Tab(text="紀錄", icon="list", content=lv_history),
            ft.Tab(text="統計", icon="analytics", content=tab_stats),
            ft.Tab(text="設定", icon="settings", content=tab_settings),
        ], expand=True
    )

    page.clean()
    page.add(t)
    
    # 【修正】先檢查有沒有錯誤訊息，再添加紅條
    if db.error_msg:
        page.add(ft.Container(
            content=ft.Text(f"⚠️ {db.error_msg}", color="white", weight="bold"),
            bgcolor="red", padding=10, border_radius=5
        ))
    
    refresh_all_data()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
