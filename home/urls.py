from unicodedata import name
from django.urls import path
from .views import register_api, home_view, register_view, profile_view, update_course_details, upload_file_api, \
    login_view, login_api, logout_view, update_experience, edit_experience, delete_experience, download_view

urlpatterns = [
    path('api/register/', register_api, name='register_api'),
    path('api/login/', login_api, name='login_api'),
    path('api/register/<str:key>/', register_api, name='register_api'),
    path('api/register/<str:key>/<int:user_id>/', register_api, name='register_api'),
    path('api/course/', update_course_details, name='update_course_details'),
    path('api/experience/', update_experience, name='update_experience'),
    path('api/upload_file/', upload_file_api, name='upload_file_api'),


    path('', home_view, name='register_api'),
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
