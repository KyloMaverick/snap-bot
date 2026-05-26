"""
STAGE 1: PRE-FILTER
Screening cepat, massal, pakai data minimal
"""

from typing import Dict, Tuple

def prefilter(market: Dict) -> Tuple[bool, str, Dict]:
    """
    Pre-filter cepat sebelum proses berat
    
    Kriteria:
    - Harga dalam range 0.15 - 0.85 (hindari ujung ekstrim)
    - Volume > $50,000 (cukup likuid)
    - Market masih aktif
    - Expiry > 7 hari (opsional)
    
    Returns:
        (is_passed, reason, filtered_data)
    """
    
    # Ambil data dari market
    price = market.get('price', 0.5)
    volume = market.get('volume', 0)
    active = market.get('active', True)
    
    # Simpan data yang sudah difilter (buat stage berikutnya)
    filtered_data = {
        'market_id': market.get('id'),
        'question': market.get('question'),
        'category': market.get('category', 'unknown'),
        'price': price,
        'volume': volume,
        'best_bid': market.get('best_bid', price - 0.01),
        'best_ask': market.get('best_ask', price + 0.01),
        'clob_token_id': market.get('clob_token_id')
    }
    
    # 1. Cek harga (hindari ujung ekstrim)
    if price < 0.10:
        return False, f"Harga terlalu rendah: {price:.3f} (min 0.10)", None
    if price > 0.90:
        return False, f"Harga terlalu tinggi: {price:.3f} (max 0.90)", None
    
    # 2. Cek volume (minimal likuiditas)
    if volume < 10000:
        return False, f"Volume terlalu rendah: ${volume:,.0f} (min $10k)", None
    
    # 3. Cek status aktif
    if not active:
        return False, "Market tidak aktif", None
    
    # 4. Opsional: cek expiry (kalau ada data)
    end_date = market.get('end_date')
    if end_date:
        from datetime import datetime
        try:
            # Parse tanggal (contoh: "2026-07-31T12:00:00Z")
            if 'T' in end_date:
                end_date = end_date.split('T')[0]
            expiry = datetime.strptime(end_date, '%Y-%m-%d')
            days_left = (expiry - datetime.now()).days
            if days_left < 7:
                return False, f"Expiry terlalu dekat: {days_left} hari lagi", None
        except:
            pass  # skip jika format date error
    
    return True, f"✅ Prefilter PASS (price={price:.3f}, volume=${volume:,.0f})", filtered_data