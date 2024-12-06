from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', views.register, name='register'),
    path('all-competitions/', views.all_competitions, name='all_competitions'),
    path('all-competitions/<int:id>/', views.competition_detail, name='competition_detail'),
    path('my-participant-competitions/', views.my_participant_competitions, name='my_participant_competitions'),
    path('create_competition/', views.create_competition, name='create_competition'),
    path('my-competitions/', views.my_competitions, name='my_competitions'),
    path('my_competitions/<int:id>/', views.my_competition_detail, name='my_competition_detail'),
    path('my_competitions/<int:competition_id>/delete_participant/<int:participant_id>/', views.delete_participant, name='delete_participant'),
    path('my_competitions/<int:competition_id>/delete_comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('competition/<int:competition_id>/participant/<int:participant_id>/edit/', views.edit_participant, name='edit_participant'),
    path('competition/<int:competition_id>/results/', views.competition_results, name='competition_results'),
    path('competition/<int:competition_id>/delete/', views.delete_competition, name='delete_competition'),
]
