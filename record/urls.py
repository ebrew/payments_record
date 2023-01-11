from django.urls import path
from . import views
from .views import AddContributionMember, SubdomainDetailView
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('', views.home, name="home"),
    path('account/login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    # path('helpdesk', views.helpdesk_options, name='helpdesk'),
    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate_account'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password_reset/', auth_views.PasswordResetView.
         as_view(template_name='users/password_reset/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.
         as_view(template_name='users/password_reset/password_reset_done.html'), name='password_reset_done'),
    path('reset/done/', auth_views.PasswordResetCompleteView.
         as_view(template_name='users/password_reset/password_reset_complete.html'), name='password_reset_complete'),
    path('about/', views.about, name='about'),
    path('users/history/', views.event, name="user_event"),

    # Account
    path('users/acount/options', views.user_account_options, name="account_options"),
    path('users/profile/image/update', views.update_profile_image, name="update_profile_image"),
    path('users/profile/update', views.update_user_profile, name="update_profile"),
    path('users/profile/', views.user_profile, name="user_profile"),

    # Contributions
    path('organisations/contribution/options', views.contribution_options, name="contribution_options"),
    path('client/add', views.add_contribution, name="add_contribution_organisation"),
    path('user/organisations/contribution/', views.user_contribution_organisations,
         name="user_contribution_organisations"),
    path('user/organisations/contribution/update/<str:pk>', views.update_user_contribution_organisations,
         name='update_user_contribution_organisations'),
    path('user/organisations/contribution/members/<str:pk>', views.organisational_members,
         name='organisational_members'),
    path('update_member/<str:pk>', views.update_member, name='update_member'),
    path('delete_member/<str:pk>', views.delete_member, name='delete_member'),
    path('user/organisations/contribution/add/member/', view=AddContributionMember.as_view(),
         name="add_contribution_member"),
    path('test/<slug:slug>/', SubdomainDetailView.as_view(), name="test"),
    # path('user/organisations/contribution/add/member/', views.add_contribution_member, name="add_contribution_member"),
    path('user/organisations/<str:pk>/contribution/new/member/', views.add_organisational_member,
         name="add_organisational_member"),
    path('user/contribution/organisation/<str:pk>', views.organisational_menu,
         name='organisational_menu'),

    # Payments
    path('user/organisations/<str:pk>/contribution/new/payment/', views.make_contributional_payment,
         name="make_contributional_payment"),
    path('direct_payment/<orgpk>/<mempk>/', views.direct_payment, name='direct_payment'),
    # path('direct_payment/pdf/', views.pdf, name='pdf'),


]
