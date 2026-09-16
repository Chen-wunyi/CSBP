from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Gene
import csv
from django.http import HttpResponse



def lookup(request):
    #接收資料
    wormbase_id = request.GET.get('wormbase_id', '').strip()
    status = request.GET.get('status', '').strip()
    sequence_name = request.GET.get('sequence_name', '').strip()
    gene_name = request.GET.get('gene_name', '').strip()
    other_name = request.GET.get('other_name', '').strip()
    gene_type = request.GET.get('gene_type', '').strip()
    sort_by = request.GET.get('sort', 'wormbase_id').strip()
    
    #檢查是否點擊了匯出CSV按鈕
    export_csv = request.GET.get('export', '0') == '1'

    #交集查詢
    filters = Q()
    if wormbase_id:
        filters &= Q(wormbase_id__icontains=wormbase_id)
    if status:
        filters &= Q(status=status)
    if sequence_name:
        filters &= Q(sequence_name__icontains=sequence_name)
    if gene_name:
        filters &= Q(gene_name__icontains=gene_name)
    if other_name:
        filters &= Q(other_name__icontains=other_name)
    if gene_type:
        filters &= Q(gene_type=gene_type) 

    #確認欄位的排序
    valid_sort_fields = [
        'wormbase_id', '-wormbase_id', 
        'gene_name', '-gene_name', 
        'status', '-status', 
        'gene_type', '-gene_type'
    ]
    
    if sort_by not in valid_sort_fields:
        sort_by = 'wormbase_id'

    #過濾與排序
    gene_list = Gene.objects.filter(filters).order_by(sort_by)
    total_count = gene_list.count()

    #Export CSV按鈕被點擊，直接產生並下載CSV檔
    if export_csv:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="c_elegans_genes_export.csv"'
        # 加上BOM讓Excel開啟UTF-8時不會亂碼
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
    
    
    return render(request, 'hw1/main.html', context)

def input_validation(request):
    raw_input = ""
    errors = []
    valid_genes = []
    
    if request.method == "POST":
        raw_input = request.POST.get("gene_input", "")
        # 切分換行 (\r\n, \n)、逗號 (,)、Tab (\t)
        tokens = [t.strip() for t in re.split(r'[\r\n,\t]+', raw_input) if t.strip()]
        
        gene_matched_fields = defaultdict(set)
        
        for token in tokens:
            # 比對所有欄位 (不分大小寫)
            matches = Gene.objects.filter(
                Q(wormbase_id__iexact=token) |
                Q(sequence_name__iexact=token) |
                Q(gene_name__iexact=token) |
                Q(other_name__iexact=token)
            )
            
            distinct_ids = list(matches.values_list('wormbase_id', flat=True).distinct())
            
            if len(distinct_ids) == 0:
                errors.append({
                    'input': token,
                    'message_title': 'Unknown name',
                    'detail': ''
                })
            elif len(distinct_ids) > 1:
                errors.append({
                    'input': token,
                    'message_title': 'Multiple WormBase IDs found',
                    'detail': ",".join(distinct_ids)
                })
            else:
                wb_id = distinct_ids[0]
                gene_obj = matches.first()
                token_lower = token.lower()
                
                # 安全字串比對，防止欄位為 None 時引發 AttributeError
                if (gene_obj.wormbase_id or '').strip().lower() == token_lower:
                    gene_matched_fields[wb_id].add('wormbase_id')
                if (gene_obj.sequence_name or '').strip().lower() == token_lower:
                    gene_matched_fields[wb_id].add('sequence_name')
                if (gene_obj.gene_name or '').strip().lower() == token_lower:
                    gene_matched_fields[wb_id].add('gene_name')
                if (gene_obj.other_name or '').strip().lower() == token_lower:
                    gene_matched_fields[wb_id].add('other_name')

        if gene_matched_fields:
            genes = Gene.objects.filter(wormbase_id__in=gene_matched_fields.keys()).order_by('wormbase_id')
            for g in genes:
                valid_genes.append({
                    'obj': g,
                    'matched_fields': gene_matched_fields[g.wormbase_id]
                })

    return render(request, 'hw1/input_validation.html', {
        'raw_input': raw_input,
        'errors': errors,
        'valid_genes': valid_genes
    })