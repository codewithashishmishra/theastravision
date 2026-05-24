from django.urls import path

from .public_views import HostedJobBoardViewSet, PublicJobBoardViewSet

job_board_config = PublicJobBoardViewSet.as_view({'get': 'config'})
job_board_list = PublicJobBoardViewSet.as_view({'get': 'list_jobs'})
job_board_detail = PublicJobBoardViewSet.as_view({'get': 'job_detail'})
job_board_apply = PublicJobBoardViewSet.as_view({'post': 'apply'})

hosted_config = HostedJobBoardViewSet.as_view({'get': 'config'})
hosted_list = HostedJobBoardViewSet.as_view({'get': 'list_jobs'})
hosted_detail = HostedJobBoardViewSet.as_view({'get': 'job_detail'})
hosted_apply = HostedJobBoardViewSet.as_view({'post': 'apply'})

urlpatterns = [
    path('config/', job_board_config, name='public-job-board-config'),
    path('jobs/', job_board_list, name='public-job-board-list'),
    path('jobs/<slug:slug>/', job_board_detail, name='public-job-board-detail'),
    path('jobs/<slug:slug>/apply/', job_board_apply, name='public-job-board-apply'),
    path('hosted/<slug:tenant_slug>/config/', hosted_config, name='hosted-job-board-config'),
    path('hosted/<slug:tenant_slug>/jobs/', hosted_list, name='hosted-job-board-list'),
    path(
        'hosted/<slug:tenant_slug>/jobs/<slug:job_slug>/',
        hosted_detail,
        name='hosted-job-board-detail',
    ),
    path(
        'hosted/<slug:tenant_slug>/jobs/<slug:job_slug>/apply/',
        hosted_apply,
        name='hosted-job-board-apply',
    ),
]
