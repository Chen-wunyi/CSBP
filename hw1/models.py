from django.db import models


# 用class定義基因這個物件的資料格式
class Gene(models.Model):
    wormbase_id = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=32, db_index=True)
    sequence_name = models.CharField(
        max_length=64, blank=True, null=True, db_index=True
    )
    gene_name = models.CharField(
        max_length=64, blank=True, null=True, db_index=True
    )
    other_name = models.CharField(
        max_length=64, blank=True, null=True, db_index=True
    )
    gene_type = models.CharField(max_length=64, db_index=True)

    # 補上蛋白質異構物數量的欄位（假設資料庫裡是整數型態，如果欄位名稱不同可以微調）
    protein_isoform = models.IntegerField(default=1, db_index=True)

    def __str__(self):
        return f'{self.wormbase_id} ({self.gene_name})'