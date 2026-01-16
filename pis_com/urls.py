from django.urls import path, include,re_path
from django.conf import settings
from django.conf.urls.static import static


from pis_com.views import (CreateCustomer, CustomerTemplateView, CustomerUpdateView, CreateFeedBack, ReportsView, HomePageView, LoginView,
LogoutView, password)

urlpatterns = [
    re_path(r'^$', HomePageView.as_view(), name='index'),
    re_path(r'^reports/$', ReportsView.as_view(), name='reports'),
    re_path(r'^login/$', LoginView.as_view(), name='login'),
    re_path(r'^logout/$', LogoutView.as_view(), name='logout'),
    re_path(r'^password/$', password, name='password'),
    #path('api/', include('pis_com.api_urls', namespace='com_api')),
    re_path(r'^api/',CreateCustomer.as_view(),name='create_customer'),

    re_path(r'^customer/create/$', CustomerTemplateView.as_view(), name='customers'),

    re_path(r'^customers/$', CustomerUpdateView.as_view(), name='update_customer'),
    re_path(r'^register/$', CreateFeedBack.as_view(), name='create_feedback'),
    # path('makebackup', makebackup, name='makebackup'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
