from unicodedata import name
from django.urls import path
from .views import *

urlpatterns = [
    path('api/register/', register_api, name='register_api'),
    path('api/login/', login_api, name='login_api'),
    path('api/register/<str:key>/', register_api, name='register_api'),
    path('api/register/<str:key>/<int:user_id>/', register_api, name='register_api'),
    path('api/course/', update_course_details, name='update_course_details'),
    path('api/experience/', update_experience, name='update_experience'),
    path('api/upload_file/', upload_file_api, name='upload_file_api'),
    path("api/get/course-by-id/<int:course_id>/", course_by_id, name="course-by-id"),
    path("api/get/course-by-type/<str:course_type>/",course_by_type, name="course_by_type"),
    path("create-order/", create_order, name="create_order"),
    path("payment-success/", payment_success, name="payment_success"),
    path("invoice-generate/<int:course_id>/", invoice_generate, name="invoice"),
    path("email-invoice/", emailInvoice, name="email-invoice"),

    path('', home_view, name='register_api'),
    path('courses/', courses, name="courses"),
    path('register/', register_view, name='register'),
    path('register/<str:message>/', register_view, name='register'),
    path('login/', login_view, name='login_view'),
    path('logout/', logout_view, name='logout_view'),
    path('login/<str:message>/', login_view, name='login_view'),
    path('profile/', profile_view, name='profile_view'),
    path('profile/<int:user_id>/', profile_view, name='profile_view'),
    path('zip_download/<int:user_id>/', download_view, name='download_view'),
    path('experience/<int:experience_id>/', edit_experience, name='edit_experience'),
    path('delete-experience/<int:experience_id>/', delete_experience, name='delete_experience'),
]
