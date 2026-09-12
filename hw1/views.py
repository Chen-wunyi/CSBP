from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Gene
import csv
from django.http import HttpResponse



def lookup(request):
    # 接收 6 個欄位的搜尋值
    wormbase_id = request.GET.get('wormbase_id', '').strip()
    status = request.GET.get('status', '').strip()
    sequence_name = request.GET.get('sequence_name', '').strip()
    gene_name = request.GET.get('gene_name', '').strip()
    other_name = request.GET.get('other_name', '').strip()
    gene_type = request.GET.get('gene_type', '').strip()
    
    # 接收排序參數，預設依 wormbase_id 排序
    sort_by = request.GET.get('sort', 'wormbase_id').strip()
    
    # 檢查是否點擊了匯出 CSV 按鈕
    export_csv = request.GET.get('export', '0') == '1'

    # 多條件交集查詢 (AND 邏輯)
    filters = Q()
    if wormbase_id:
        filters &= Q(wormbase_id__icontains=wormbase_id)
    if status:
        filters &= Q(status=status)  # 下拉選單用精確匹配
    if sequence_name:
        filters &= Q(sequence_name__icontains=sequence_name)
    if gene_name:
        filters &= Q(gene_name__icontains=gene_name)
    if other_name:
        filters &= Q(other_name__icontains=other_name)
    if gene_type:
        filters &= Q(gene_type=gene_type)  # 下拉選單用精確匹配

    # 驗證排序欄位，避免無效參數爆錯
    valid_sort_fields = [
        'wormbase_id', '-wormbase_id', 
        'gene_name', '-gene_name', 
        'status', '-status', 
        'gene_type', '-gene_type'
    ]
    if sort_by not in valid_sort_fields:
        sort_by = 'wormbase_id'

    # 執行過濾與排序
    gene_list = Gene.objects.filter(filters).order_by(sort_by)
    total_count = gene_list.count()

    # 如果使用者點擊「Export CSV」，直接產生並下載 CSV 檔案
    if export_csv:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="c_elegans_genes_export.csv"'
        # 加上 BOM 讓 Excel 開啟 UTF-8 時不會亂碼
        response.write('\ufeff'.encode('utf8'))
        
        writer = csv.writer(response)
        writer.writerow(['WormBase ID', 'Status', 'Sequence Name', 'Gene Name', 'Other Name', 'Gene Type'])
        for gene in gene_list:
            writer.writerow([gene.wormbase_id, gene.status, gene.sequence_name, gene.gene_name, gene.other_name, gene.gene_type])
        return response

    # 分頁設定（每頁 50 筆）
    paginator = Paginator(gene_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_count': total_count,
        'wormbase_id': wormbase_id,
        'status': status,
        'sequence_name': sequence_name,
        'gene_name': gene_name,
        'other_name': other_name,
        'gene_type': gene_type,
        'sort_by': sort_by,
    }
    
    # 請確認你的 HTML 檔案名稱是 'hw1/main.html' 還是 'hw1/gene_list.html'
    return render(request, 'hw1/main.html', context)