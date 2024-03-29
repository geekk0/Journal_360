from django.urls import path

from Journal_360 import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.rec_list, name='rec_list'),
    path('регистрация/', views.RegistrationView.as_view(), name='регистрация'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('добавить заметку/', views.AddNoteView.as_view(), name='добавить заметку'),
    path('удалить запись/', views.delete_note, name='удалить запись'),
    path('отправить отчет/', views.send_report, name='отправить отчет'),
    path('добавить комментарий/<int:record_id>', views.add_comment, name='добавить комментарий'),
    path('найти по дате/', views.find_by_date, name='найти по дате'),
    path('выбор автора/<int:author_id>', views.find_by_author, name='выбор автора'),
    path('найти по тексту/', views.find_by_text, name='найти по тексту'),
    path('добавить задачу/', views.add_objective, name='добавить задачу'),
    path('добавить статус/<int:objective_id>', views.add_status, name='добавить статус'),
    path('завершить задание/<int:objective_id>', views.finalize_objective, name='завершить задание'),
    path('добавить регулярное задание/', views.AddScheduledTask.as_view(), name='добавить регулярное задание'),
    path('добавить отчет/', views.edit_note, name='добавить отчет'),
    path('добавить фото/', views.add_photo, name='добавить фото'),
    path('удалить фото/<int:image_id>', views.remove_photo, name='удалить фото'),
    path('опубликовать отчет/<int:note_id>', views.publish_it_record, name='опубликовать отчет'),


    path('мануалы к устройству/<str:device_name>', views.show_device_manuals, name='мануалы к устройству'),
    path('обновить данные по конвертеру', views.edit_converter_info, name='обновить данные по конвертеру'),

    path('фильтр по отделу/<str:department_name>', views.sort_by_department, name='фильтр по отделу'),
    path('фильтр по группе/<str:group_name>', views.sort_by_group, name='фильтр по группе'),
    path('сменить пароль/', views.ResetPasswordView.as_view(), name='сменить пароль'),
    path('Документы/<str:tile_name>', views.show_docs, name='Документы'),

    path('поиск мобильный/', views.by_date_view, name='поиск мобильный'),
    path('задания/', views.tasks_mobile, name='задания'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



