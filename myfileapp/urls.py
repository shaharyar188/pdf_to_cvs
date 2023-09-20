from django.urls import path
from . import views
app_name="fileapp"
urlpatterns = [
    path('', views.HomePage),
    path("upload-pdf/", views.uploadPdf),
    path("upload/",views.UploadData,name="uploads"),
    path('view-data/', views.viewData),
]