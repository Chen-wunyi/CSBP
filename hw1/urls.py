from django.urls import path
from . import views

urlpatterns = [
    # 當訪問根路徑或 lookup/ 時觸發 views.py 的 lookup 函數
    path('', views.lookup, name='lookup'),
    path('lookup/', views.lookup, name='gene_lookup'),
    path('input-validation/', views.input_validation, name='input_validation'),

]


