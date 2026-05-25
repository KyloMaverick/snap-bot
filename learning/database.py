"""
DATABASE LAYER
Menyimpan semua data untuk learning (SQLite)
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

class LearningDB:
    def __init__(self, db_path: str = "learning_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Tabel trades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT,
                market_question TEXT,
                category TEXT,
                side TEXT,
                entry_price REAL,
                exit_price REAL,
                predicted_prob REAL,
                actual_outcome INTEGER,
                pnl REAL,
                pnl_pct REAL,
                entry_hour INTEGER,
                timestamp DATETIME
            )
        ''')
        
        # Tabel prediksi (untuk Brier score)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT,
                predicted_prob REAL,
                actual_outcome INTEGER,
                resolved_date DATETIME
            )
        ''')
        
        # Tabel performa harian
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_performance (
                date TEXT PRIMARY KEY,
                trades_count INTEGER,
                win_count INTEGER,
                total_pnl REAL,
                avg_edge REAL
            )
        ''')
        
        self.conn.commit()
        print("✅ Database tables created/verified")
    
    def save_trade(self, trade_data: Dict):
        """Simpan trade yang sudah selesai"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO trades (
                market_id, market_question, category, side,
                entry_price, exit_price, predicted_prob,
                actual_outcome, pnl, pnl_pct, entry_hour, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data.get('market_id'),
            trade_data.get('market_question', '')[:200],
            trade_data.get('category'),
            trade_data.get('side'),
            trade_data.get('entry_price'),
            trade_data.get('exit_price'),
            trade_data.get('predicted_prob'),
            trade_data.get('actual_outcome'),
            trade_data.get('pnl'),
            trade_data.get('pnl_pct'),
            trade_data.get('entry_hour', 0),
            datetime.now()
        ))
        self.conn.commit()
    
    def save_prediction(self, market_id: str, predicted_prob: float, actual_outcome: int):
        """Simpan prediksi untuk Brier score"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO predictions (market_id, predicted_prob, actual_outcome, resolved_date)
            VALUES (?, ?, ?, ?)
        ''', (market_id, predicted_prob, actual_outcome, datetime.now()))
        self.conn.commit()
    
    def get_winrate_by_category(self) -> Dict:
        """Hitung win rate per kategori"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT category, 
                   COUNT(*) as total,
                   SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins
            FROM trades
            GROUP BY category
        ''')
        
        results = {}
        for row in cursor.fetchall():
            category, total, wins = row
            results[category] = round(wins / total * 100, 1) if total > 0 else 0
        return results
    
    def get_winrate_by_hour(self) -> Dict:
        """Hitung win rate per jam"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT entry_hour,
                   COUNT(*) as total,
                   SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins
            FROM trades
            GROUP BY entry_hour
        ''')
        
        results = {}
        for row in cursor.fetchall():
            hour, total, wins = row
            results[hour] = round(wins / total * 100, 1) if total > 0 else 0
        return results
    
    def calculate_brier_score(self) -> float:
        """Hitung Brier score (makin kecil makin bagus)"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT predicted_prob, actual_outcome FROM predictions')
        
        predictions = cursor.fetchall()
        if len(predictions) < 10:
            return 0.25  # default untuk data sedikit
        
        brier_sum = sum((p - o) ** 2 for p, o in predictions)
        return round(brier_sum / len(predictions), 4)
    
    def get_recent_performance(self, limit: int = 20) -> Dict:
        """Dapatkan performa recent trades"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT pnl_pct FROM trades 
            ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        if not results:
            return {'winrate': 0, 'avg_pnl': 0}
        
        wins = sum(1 for r in results if r[0] > 0)
        avg_pnl = sum(r[0] for r in results) / len(results)
        
        return {
            'winrate': round(wins / len(results) * 100, 1),
            'avg_pnl': round(avg_pnl, 2),
            'total_trades': len(results)
        }
    
    def close(self):
        self.conn.close()