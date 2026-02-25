from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.loginPage, name='client-login'),
    path("signup/", views.Signup, name='client-signup'),
    path("logout/",views.logoutUser,name='client-logout'),
    path("update-details/", views.updateUserDetails,name='client-update-details'),
    path("pin/",views.pinView, name='client-pin-view'),
    path("",views.dashboardPage, name='client-dashboard'),
    path("deposit/", views.depositPage, name = 'client-deposit'),
    path("search-account/", views.searchAccountView, name='client-account-search'),
    path("transfer/", views.transferView, name='client-transfer'),
    path('success/', views.paymentSuccessView, name='payment-success-view'),
    path("transaction/", views.transactionHistory, name ='client-transaction-details'),
    path('dynamic/<str:id>/test/', views.dynamicTesting )
] 