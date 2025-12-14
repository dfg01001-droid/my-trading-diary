# trading_diary.py (V5.6 - GitHub Actions 相容版 / 修復 Expanded 與 Colors 錯誤)

import flet as ft
import sqlite3
import os
import sys
import csv
from datetime import datetime

# =========================================================================
# 1. 資料庫邏輯
# =========================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "trading_data.db")
ICON_FILE = "icon.jpg"

class DBManager:
    def __init__(self):
        try:
            self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.cursor = self.conn.cursor()
            self.create_tables()
            self.check_and_migrate()
        except Exception as e:
            print(f"資料庫錯誤: {e}")

    def create_tables(self):
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
        self.cursor.execute('SELECT contract_forex, contract_gold, contract_crypto, thumbs_up_count FROM settings WHERE id=1')
        row = self.cursor.fetchone()
        if row:
            crypto = row[2] if len(row) > 2 else 1.0
            thumbs = row[3] if len(row) > 3 else 0
            return {"forex": row[0], "gold": row[1], "crypto": crypto, "thumbs": thumbs}
        return {"forex": 100000.0, "gold": 100.0, "crypto": 1.0, "thumbs": 0}

    def update_settings(self, forex, gold, crypto):
        self.cursor.execute('UPDATE settings SET contract_forex=?, contract_gold=?, contract_crypto=? WHERE id=1', (forex, gold, crypto))
        self.conn.commit()

    def increment_thumbs_up(self):
        self.cursor.execute('UPDATE settings SET thumbs_up_count = thumbs_up_count + 1 WHERE id=1')
        self.conn.commit()
        self.cursor.execute('SELECT thumbs_up_count FROM settings WHERE id=1')
        return self.cursor.fetchone()[0]

    def reset_thumbs_up(self):
        self.cursor.execute('UPDATE settings SET thumbs_up_count = 0 WHERE id=1')
        self.conn.commit()
        return 0

    def add_trade(self, data):
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
        self.cursor.execute('UPDATE trades SET note=? WHERE id=?', (note_content, trade_id))
        self.conn.commit()

    def delete_trade(self, trade_id):
        self.cursor.execute('DELETE FROM trades WHERE id=?', (trade_id,))
        self.conn.commit()

db = DBManager()

# =========================================================================
# 2. Flet APP 介面
# =========================================================================

def main(page: ft.Page):
    page.title = "鼻孔警示交易日記 (V5.6)"
    page.theme_mode = "LIGHT" # 使用字串避免枚舉報錯
    page.window_width = 400
    page.window_height = 800
    page.window_resizable = False
    page.scroll = "adaptive"

    # --- 設定圖示 ---
    # 嘗試載入圖片，如果 icon.jpg 存在就使用
    if os.path.exists(os.path.join(BASE_DIR, ICON_FILE)):
        page.window_icon = ICON_FILE
        avatar_content = ft.Image(src=ICON_FILE, width=40, height=40, fit="cover", border_radius=20)
    else:
        # 如果找不到圖片，用預設圖示，避免報錯
        avatar_content = ft.Icon(name="face", size=30)

    # 設定 APP 標題列 (AppBar)
    page.appbar = ft.AppBar(
        leading=ft.Container(content=avatar_content, padding=5),
        leading_width=60,
        title=ft.Text("交易日記", weight="bold", color="black"),
        center_title=True,
        bgcolor="#e0e0e0", # 使用 Hex 色碼避免 colors 報錯
    )

    # --- 大圖 Dialog ---
    dlg_full_avatar = ft.AlertDialog(
        content=ft.Container(
            content=ft.Image(src=ICON_FILE, fit="contain") if os.path.exists(os.path.join(BASE_DIR, ICON_FILE)) else ft.Text("找不到圖片"),
            alignment=ft.alignment.center,
            height=400, 
        ),
        actions=[
            ft.TextButton("關閉", on_click=lambda e: close_avatar_dlg(e))
        ],
        actions_alignment="center"
    )
    page.overlay.append(dlg_full_avatar)

    def close_avatar_dlg(e):
        dlg_full_avatar.open = False
        page.update()

    def show_full_avatar(e):
        if os.path.exists(os.path.join(BASE_DIR, ICON_FILE)):
            dlg_full_avatar.open = True
            page.update()
        else:
            show_msg("找不到 icon.jpg", "red")

    # 為 AppBar 的頭像增加點擊功能
    if isinstance(page.appbar.leading.content, ft.Image):
         # 用 Container 包裹並啟用 ink 和 on_click
         page.appbar.leading = ft.Container(
            content=page.appbar.leading.content,
            on_click=show_full_avatar,
            ink=True,
            border_radius=20,
            padding=5
         )


    snack_bar = ft.SnackBar(content=ft.Text(""))
    page.overlay.append(snack_bar)

    def show_msg(msg, color="green"):
        snack_bar.content.value = msg
        snack_bar.bgcolor = color
        snack_bar.open = True
        page.update()

    # ==========================
    # Tab 1: 輸入頁面
    # ==========================
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
                show_msg("保存失敗", "red")
        except:
            show_msg("輸入格式錯誤", "red")

    tab_entry = ft.Container(
        content=ft.Column([
            ft.Text("新增交易", size=20, weight="bold"),
            txt_pair, dd_direction, txt_lots, txt_entry, txt_exit,
            ft.ElevatedButton("💾 保存交易", on_click=save_trade_click, height=50, bgcolor="blue", color="white"),
            lbl_pnl_preview
        ], spacing=15), padding=20
    )

    # ==========================
    # Tab 2: 紀錄頁面
    # ==========================
    lv_history = ft.ListView(expand=1, spacing=10, padding=20)
    
    txt_detail_note = ft.TextField(label="心得與檢討", multiline=True, min_lines=5)
    current_trade_id = None
    
    dlg_detail = ft.AlertDialog(
        title=ft.Text("詳細資料"),
        content=ft.Column([ft.Text("載入中...")], height=400, scroll="adaptive"),
        actions=[
            ft.ElevatedButton("保存心得", on_click=lambda e: save_note_click(e))
        ]
    )
    page.overlay.append(dlg_detail)

    def save_note_click(e):
        if current_trade_id:
            db.update_trade_note(current_trade_id, txt_detail_note.value)
            show_msg("心得已更新")
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
            ft.Row([ft.Text("時間:", weight="bold"), ft.Text(trade['entry_time'][:16])], alignment="spaceBetween"),
            ft.Row([ft.Text("進場價:", weight="bold"), ft.Text(str(trade['entry_price']))], alignment="spaceBetween"),
            ft.Row([ft.Text("出場價:", weight="bold"), ft.Text(str(trade['exit_price']))], alignment="spaceBetween"),
            ft.Row([ft.Text("手數:", weight="bold"), ft.Text(str(trade['lots']))], alignment="spaceBetween"),
            ft.Divider(),
            ft.Row([ft.Text("損益:", weight="bold", size=18), ft.Text(f"${pnl:.2f}", size=18, color=color)], alignment="spaceBetween"),
            ft.Divider(),
            ft.Text("心得備註:", weight="bold"),
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
        trades = db.get_all_trades()
        if not trades:
            lv_history.controls.append(ft.Text("尚無紀錄"))
        
        for t in trades:
            color = "green" if t['pnl_usd'] >= 0 else "red"
            
            # --- 關鍵修復：完全移除 ft.Expanded，改用 expand=True ---
            row = ft.Container(
                content=ft.Row([
                    ft.Icon("trending_up" if t['pnl_usd']>=0 else "trending_down", color=color),
                    
                    # 使用 expand=True 替代 ft.Expanded，解決報錯
                    ft.Column([
                        ft.Text(f"{t['pair']} {t['direction']}", weight="bold"),
                        ft.Text(f"${t['pnl_usd']:.2f}", color=color)
                    ], expand=True), 
                    
                    ft.IconButton(icon="edit", icon_color="blue", tooltip="詳細/心得", data=t['id'], on_click=open_detail_click),
                    ft.IconButton(icon="delete", icon_color="red", tooltip="刪除", data=t['id'], on_click=delete_trade_click),
                ]),
                padding=10,
                bgcolor="white",
                border_radius=5
            )
            lv_history.controls.append(row)
        page.update()

    # ==========================
    # Tab 3: 統計頁面
    # ==========================
    stats_container = ft.Column(spacing=20, scroll="adaptive")
    dlg_help = ft.AlertDialog(title=ft.Text("說明"), content=ft.Text(""))
    page.overlay.append(dlg_help)

    def show_help_click(e):
        title, text = e.control.data
        dlg_help.title.value = title
        dlg_help.content.value = text
        dlg_help.open = True
        page.update()

    def create_stat_card(title, value, color, help_text):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=14, color="grey"),
                ft.Text(value, size=22, weight="bold", color=color),
                ft.IconButton(icon="help_outline", icon_size=20, icon_color="blue", 
                              data=(title, help_text), on_click=show_help_click)
            ], alignment="center", horizontal_alignment="center"),
            width=150, padding=10, bgcolor="#f0f0f0", border_radius=10
        )

    def load_stats_data():
        trades = db.get_all_trades()
        stats_container.controls.clear()
        
        net_profit = sum(t['pnl_usd'] for t in trades)
        wins = [t for t in trades if t['pnl_usd'] > 0]
        losses = [t for t in trades if t['pnl_usd'] <= 0]
        
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = (win_count/len(trades)*100) if trades else 0
        pf = (sum(t['pnl_usd'] for t in wins) / abs(sum(t['pnl_usd'] for t in losses))) if losses else 0

        row1 = ft.Row([
            create_stat_card("淨利", f"${net_profit:.2f}", "green" if net_profit>=0 else "red", "綠色=賺錢\n紅色=賠錢"),
            create_stat_card("勝率", f"{win_rate:.1f}%", "blue", "短線建議 > 60%\n長線建議 > 40%")
        ], alignment="center")
        
        row2 = ft.Row([
            create_stat_card("獲利因子", f"{pf:.2f}", "orange", "總獲利 / 總虧損\n> 1.5 為優秀策略"),
            create_stat_card("總筆數", f"{len(trades)}", "black", "樣本數越多越準")
        ], alignment="center")

        row3 = ft.Row([
            create_stat_card("獲利筆數", f"{win_count}", "green", "賺錢的次數"),
            create_stat_card("虧損筆數", f"{loss_count}", "red", "賠錢的次數\n重點是控制虧損")
        ], alignment="center")

        stats_container.controls.extend([
            ft.Text("帳戶統計 (點問號看說明)", size=20, weight="bold", text_align="center"),
            row1, row2, row3
        ])
        page.update()

    tab_stats = ft.Container(content=stats_container, padding=20)

    # ==========================
    # Tab 4: 設定
    # ==========================
    txt_forex = ft.TextField(label="外匯合約")
    txt_gold = ft.TextField(label="黃金合約")
    txt_crypto = ft.TextField(label="加密貨幣合約")
    lbl_thumbs_count = ft.Text("0", size=40, weight="bold", color="blue")

    def thumbs_up_click(e):
        new_count = db.increment_thumbs_up()
        lbl_thumbs_count.value = str(new_count)
        show_msg("紀律 +1 ! 繼續保持!", "blue")
        page.update()

    def reset_thumbs_click(e):
        new_count = db.reset_thumbs_up()
        lbl_thumbs_count.value = str(new_count)
        show_msg("紀律計數器已歸零", "orange")
        page.update()

    def save_settings_click(e):
        try:
            db.update_settings(float(txt_forex.value), float(txt_gold.value), float(txt_crypto.value))
            show_msg("設定已更新")
        except:
            show_msg("輸入錯誤", "red")
            
    def export_csv_click(e):
        try:
            trades = db.get_all_trades()
            if not trades: return show_msg("沒資料", "red")
            filename = f"trade_export_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f)
                w.writerow(["ID", "Symbol", "Dir", "Lots", "Entry", "Exit", "PnL", "Time", "Note"])
                for t in trades:
                    w.writerow([t['id'], t['pair'], t['direction'], t['lots'], t['entry_price'], t['exit_price'], t['pnl_usd'], t['entry_time'], t['note']])
            show_msg(f"已匯出: {filename}")
        except Exception as ex:
            show_msg(f"失敗: {ex}", "red")

    def load_settings_data():
        s = db.get_settings()
        txt_forex.value = str(s['forex'])
        txt_gold.value = str(s['gold'])
        txt_crypto.value = str(s['crypto'])
        lbl_thumbs_count.value = str(s['thumbs'])

    thumbs_section = ft.Container(
        content=ft.Column([
            ft.Text("🛡️ 紀律計數器", size=20, weight="bold"),
            ft.Text("每當你遵守一次交易計畫，就按一下讚！", color="grey"),
            ft.Row([
                ft.IconButton(icon="thumb_up", icon_size=50, icon_color="blue", on_click=thumbs_up_click),
                lbl_thumbs_count,
                ft.IconButton(icon="refresh", icon_size=20, icon_color="grey", tooltip="歸零重置", on_click=reset_thumbs_click)
            ], alignment="center", spacing=20)
        ], horizontal_alignment="center"),
        padding=20, bgcolor="#e3f2fd", border_radius=15
    )

    tab_settings = ft.Container(
        content=ft.Column([
            ft.Text("合約設定", size=20, weight="bold"),
            txt_forex, txt_gold, txt_crypto,
            ft.ElevatedButton("更新設定", on_click=save_settings_click),
            ft.Divider(),
            thumbs_section,
            ft.Divider(),
            ft.ElevatedButton("匯出 Excel (CSV)", icon="download", on_click=export_csv_click, bgcolor="green", color="white"),
        ], spacing=20), padding=20
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
        ], expand=1
    )

    page.add(t)
    refresh_all_data()

if __name__ == "__main__":
    ft.app(target=main)