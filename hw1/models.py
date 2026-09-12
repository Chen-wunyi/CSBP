from django.db import models


class Gene(models.Model):
    wormbase_id = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=32, db_index=True)
    sequence_name = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    gene_name = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    other_name = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    gene_type = models.CharField(max_length=64, db_index=True)

    def __str__(self):
        return f"{self.wormbase_id} ({self.gene_name})"