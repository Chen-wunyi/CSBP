import os
import sys
import io
from pathlib import Path
import pandas as pd
import django

# 將專案根目錄 (CSBP) 加入 Python 模組搜尋路徑
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# 設定 Django 環境
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

def run_import():
    file_ids = find_file([
        'c_elegans.PRJNA13758.WS298.geneIDs.txt',
        'c_elegans.PRJNA13758.WS298.geneIDs.txt.gz'
    ])
    file_other = find_file([
        'c_elegans.PRJNA13758.WS298.geneOtherIDs.txt',
        'c_elegans.PRJNA13758.WS298.geneOtherIDs.txt.gz'
    ])

    if not file_ids:
        raise FileNotFoundError("找不到 geneIDs 檔案！")
    if not file_other:
        raise FileNotFoundError("找不到 geneOtherIDs 檔案！")

    print(f"正在讀取並清理: {file_ids} ...")
    
    # 讀取檔案並去除每一行外層包覆的雙引號
    cleaned_lines = []
    with open(file_ids, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            cleaned_lines.append(line)

    cols_ids = ['tax_id', 'wormbase_id', 'gene_name', 'sequence_name', 'status', 'gene_type']
    df_ids = pd.read_csv(
        io.StringIO('\n'.join(cleaned_lines)),
        sep=',',
        header=None,
        names=cols_ids,
        dtype=str
    )

    print(f"正在讀取: {file_other} ...")
    cols_other = ['wormbase_id', 'status_other', 'seq_other', 'gene_other', 'other_name']
    df_other = pd.read_csv(
        file_other,
        sep='\t',
        header=None,
        names=cols_other,
        dtype=str
    )

    print("合併 Other Name 欄位...")
    df_other_clean = df_other[['wormbase_id', 'other_name']].dropna(subset=['wormbase_id']).drop_duplicates(subset=['wormbase_id'])
    
    merged = pd.merge(df_ids, df_other_clean, on='wormbase_id', how='left')
    merged = merged.fillna('')

    total_rows = len(merged)
    print(f"整理完成，共 {total_rows} 筆資料 (預期約 52,110 筆)")

    print("清理舊資料並批次寫入資料庫...")
    Gene.objects.all().delete()

    batch_size = 5000
    genes_to_create = [
        Gene(
            wormbase_id=row['wormbase_id'].strip(),
            status=row['status'].strip(),
            sequence_name=row['sequence_name'].strip(),
            gene_name=row['gene_name'].strip(),
            other_name=row['other_name'].strip(),
            gene_type=row['gene_type'].strip()
        )
        for _, row in merged.iterrows()
    ]

    Gene.objects.bulk_create(genes_to_create, batch_size=batch_size)
    print("匯入成功完成！")

if __name__ == '__main__':
    run_import()