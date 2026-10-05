import os
import sys
from pathlib import Path
from collections import defaultdict
import pandas as pd
import django

# 設定 Django 環境以調用資料庫中的 Gene 模型
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hw1.models import Gene

def find_file(filenames):
    for fname in filenames:
        candidates = [
            Path(fname),
            BASE_DIR / fname,
            BASE_DIR / 'hw1' / fname,
        ]
        for p in candidates:
            if p.exists():
                return str(p)
    return None

def verify_against_csv():
    print("=" * 65)
    print(" 🧬 C. elegans WS298 HW2 重複名稱 (Part 1) 邏輯驗證腳本")
    print("=" * 65)

    # 1. 檢查並讀取老師提供的 52110_duplicate.csv
    csv_file = find_file(['52110_duplicate.csv'])
    if not csv_file:
        print("❌ 找不到 '52110_duplicate.csv'，請確認檔案是否放置在專案目錄！")
        return

    teacher_df = pd.read_csv(csv_file)
    print(f"📖 成功載入老師提供的標準答案: {csv_file}")
    print(f"   標準答案收錄衝突筆數: {len(teacher_df)} 筆\n")

    # 2. 從資料庫讀取所有基因並建立跨欄位比對字典
    total_db_genes = Gene.objects.count()
    print(f"🔍 正在從資料庫讀取 Gene 資料表 (現有 {total_db_genes} 筆)...")
    if total_db_genes == 0:
        print("❌ 資料庫中沒有任何基因資料，請先執行 data_importer.py！")
        return

    # 記錄每個「正規化名稱 (大寫)」對應到的所有唯一 WormBase IDs 與來源欄位
    # 結構: name_mapping[name_upper] = {'ids': set(), 'sources': set()}
    name_mapping = defaultdict(lambda: {'ids': set(), 'sources': set()})

    for gene in Gene.objects.all().iterator(chunk_size=5000):
        wb_id = (gene.wormbase_id or '').strip()
        if not wb_id:
            continue

        # 檢測的三大名稱欄位（Sequence Name, Gene Name, Other Name）
        fields = [
            ('Sequence name', gene.sequence_name),
            ('Gene name', gene.gene_name),
            ('Other name', gene.other_name)
        ]

        for col_name, val in fields:
            val_clean = (val or '').strip()
            if val_clean:
                # 老師的 CSV 以正規化（大寫）比對不分大小寫的衝突
                key = val_clean.upper()
                name_mapping[key]['ids'].add(wb_id.upper())
                name_mapping[key]['sources'].add(col_name)

    # 3. 篩選出對應多個 ID (count > 1) 的衝突項目
    my_duplicates = {}
    for name, data in name_mapping.items():
        if len(data['ids']) > 1:
            my_duplicates[name] = {
                'count': len(data['ids']),
                'wormbase_ids': sorted(list(data['ids'])),
                'sources': ", ".join(sorted(list(data['sources'])))
            }

    print(f"✅ 您程式計算出的衝突名稱總數: {len(my_duplicates)} 筆")

    # 4. 與老師的 CSV 進行詳細逐筆比對
    teacher_names = set(teacher_df['name'].str.strip().str.upper())
    my_names = set(my_duplicates.keys())

    matched = teacher_names.intersection(my_names)
    only_in_teacher = teacher_names - my_names
    only_in_mine = my_names - teacher_names

    print("-" * 65)
    print(f"📊 比對結果:")
    print(f"   • 完全吻合的重複名稱: {len(matched)} / {len(teacher_names)} 筆")

    if only_in_teacher:
        print(f"   ⚠️ 老師答案中有、但您的資料庫沒抓到的名稱 ({len(only_in_teacher)} 筆):")
        print(f"      {list(only_in_teacher)[:10]}")
    if only_in_mine:
        print(f"   ⚠️ 您的程式有抓到、但老師答案中沒有的名稱 ({len(only_in_mine)} 筆):")
        print(f"      {list(only_in_mine)[:10]}")

    if len(matched) == len(teacher_names) and len(my_names) == len(teacher_names):
        print("🎉 太棒了！您的重複名稱判斷邏輯與老師的標準答案 100% 完全相符！")
    print("-" * 65)

    # 5. 模擬投影片中的測試案例（防呆邏輯核對）
    print("\n🧪 模擬 HW2 投影片中的輸入案例比對 (Input Validation):")
    test_cases = ["WBGene00000001", "Y110A7A.10", "aap-1", "xxx", "B0564.1"]
    
    for token in test_cases:
        token_upper = token.upper()
        # 查詢 WormBase ID 本身
        direct_match = Gene.objects.filter(wormbase_id__iexact=token).exists()
        
        if direct_match:
            print(f"   ▶ 輸入 '{token}': 是唯一身分證號 (WormBase ID) -> 成功解析 ✓")
        elif token_upper in my_duplicates:
            ids_str = ",".join(my_duplicates[token_upper]['wormbase_ids'])
            print(f"   ▶ 輸入 '{token}': 對到多個 ID ({ids_str}) -> 觸發 Multiple IDs 報錯 ✓")
        elif token_upper in name_mapping:
            single_id = list(name_mapping[token_upper]['ids'])[0]
            print(f"   ▶ 輸入 '{token}': 唯一對應到 {single_id} -> 成功解析 ✓")
        else:
            print(f"   ▶ 輸入 '{token}': 資料庫查無此名稱 -> 觸發 Unknown name 報錯 ✓")

    print("=" * 65)

if __name__ == '__main__':
    verify_against_csv()