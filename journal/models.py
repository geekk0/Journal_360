from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User, Group


class Record(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               verbose_name='Отчет от')
    created_date = models.DateField(default=timezone.now, verbose_name='Дата отправки', auto_now=False,
                                    auto_now_add=False)
    text = models.TextField(default='', verbose_name='Текст')
    report_date = models.DateField(blank=True, default=timezone.now,  verbose_name='За какое число')
    comments_count = models.IntegerField(default=0, editable=False, verbose_name='Количество комментов')
    author_group = models.CharField(blank=True, null=True, editable=False, verbose_name='Группа автора отчета',
                                    max_length=64)
    author_name = models.CharField(blank=True, null=True, editable=False, verbose_name='Имя и фамилия автора отчета',
                                   max_length=128)

    def publish(self):
        self.created_date = timezone.now()
        self.save()

    def __str__(self):
        return str(self.report_date)+' '+str(self.author)

    def get_comments_count(self):
        self.comments_count = len(Comments.objects.filter(record_id=self.id))
        self.save()

    def get_author_group(self):
        auth_group = Group.objects.get(user=self.author)
        self.author_group = auth_group.name
        self.save()

    def get_author_names(self):
        author_firstname = User.objects.get(username=self.author).first_name
        author_lastname = User.objects.get(username=self.author).last_name
        self.author_name = author_firstname+' '+author_lastname
        self.save()

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'


class Notes(models.Model):
    message = models.TextField(default='', null=True, blank=True, verbose_name='Текст заметки')
    created_date = models.DateField(default=timezone.now, verbose_name='Дата', auto_now=False)

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               verbose_name='от')
    status = models.CharField(default='initial', null=True, blank=True, verbose_name='Статус (для финализации)',
                              max_length=64)
    to_record = models.OneToOneField(Record, on_delete=models.CASCADE, null=True, blank=True,
                                     verbose_name='Какая запись создана из заметки')

    def publish(self):
        self.created_date = timezone.now()
        self.save()

    def __str__(self):
        return str(self.created_date)+' '+str(self.author)

    class Meta:
        verbose_name = 'Заметка'
        verbose_name_plural = 'Заметки'


class Images(models.Model):
    name = models.CharField(max_length=256, default=None)
    image = models.ImageField(upload_to='', verbose_name='Загрузить фото', blank=True, null=True)

    def __str__(self):
        return str(self.name)


class RecImages(Images):
    of_record = models.ForeignKey(Record, on_delete=models.CASCADE, verbose_name='К записи', blank=True, null=True)


class NoteImages(Images):
    of_note = models.ForeignKey(Notes, on_delete=models.CASCADE, verbose_name='К заметке', blank=True, null=True)


class Comments(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               verbose_name='Автор коммента')
    record_id = models.ForeignKey(Record, on_delete=models.CASCADE, verbose_name='К посту:')
    text = models.TextField(max_length=500, verbose_name='Текст коммента')
    created = models.DateField(default=timezone.now, verbose_name='')
    author_group = models.CharField(blank=True, null=True, editable=False, verbose_name='Группа автора коммента',
                                    max_length=64)
    author_name = models.CharField(blank=True, null=True, editable=False, verbose_name='Имя и фамилия автора коммента',
                                   max_length=64)

    def publish(self):
        self.created = timezone.now()
        self.save()

    def __str__(self):
        return str(self.created)+' '+str(self.author)

    def get_author_group(self):
        auth_group = Group.objects.get(user=self.author)
        self.author_group = auth_group.name
        self.save()

    def get_author_names(self):
        author_firstname = User.objects.get(username=self.author).first_name
        author_lastname = User.objects.get(username=self.author).last_name
        self.author_name = author_firstname+' '+author_lastname
        self.save()

    class Meta:
        verbose_name = 'Комменатрий'
        verbose_name_plural = 'Комментарии'


class Department(models.Model):
    groups = models.ManyToManyField(Group, blank=True)
    name = models.CharField(blank=True, verbose_name='Название отдела', max_length=64)

    def publish(self):
        self.save()

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'


class Objectives(models.Model):
    name = models.TextField(verbose_name='Что сделать')
    created_date = models.DateField(default=timezone.now, verbose_name='Дата создания задачи')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               verbose_name='Автор задачи')
    author_group = models.CharField(blank=True, null=True, editable=False, verbose_name='Группа автора отчета',
                                    max_length=64)
    author_name = models.CharField(blank=True, null=True, editable=False, verbose_name='Имя и фамилия автора отчета',
                                   max_length=64)
    status_count = models.IntegerField(default=0, editable=False, verbose_name='Количество добавлений статуса')
    departments = models.ManyToManyField(Department, blank=True, verbose_name='Задание для отдела:')

    def publish(self):
        self.created = timezone.now()
        self.save()

    def __str__(self):
        return str(self.name)

    def get_author_group(self):
        auth_group = Group.objects.get(user=self.author)
        self.author_group = auth_group.name
        self.save()

    def get_author_names(self):
        author_firstname = User.objects.get(username=self.author).first_name
        author_lastname = User.objects.get(username=self.author).last_name
        self.author_name = author_firstname+' '+author_lastname
        self.save()

    def get_status_count(self):
        self.status_count = len(ObjectivesStatus.objects.filter(objective_id=self.id))
        self.save()

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'


class ObjectivesStatus(models.Model):
    objective_id = models.ForeignKey(Objectives, on_delete=models.CASCADE, verbose_name='К задаче:')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               verbose_name='Автор обновления статуса')
    status = models.TextField(blank=True, null=True, verbose_name='Что сделано')
    created = models.DateTimeField(default=timezone.now, verbose_name='')
    author_group = models.CharField(blank=True, null=True, editable=False, verbose_name='Группа автора отчета',
                                    max_length=64)
    author_name = models.CharField(blank=True, null=True, editable=False, verbose_name='Имя и фамилия автора отчета',
                                   max_length=64)

    def __str__(self):
        return str(self.author)

    def publish(self):
        self.created = timezone.now()
        self.save()

    def get_author_group(self):
        auth_group = Group.objects.get(user=self.author)
        self.author_group = auth_group.name
        self.save()

    def get_author_names(self):
        author_firstname = User.objects.get(username=self.author).first_name
        author_lastname = User.objects.get(username=self.author).last_name
        self.author_name = author_firstname+' '+author_lastname
        self.save()

    class Meta:
        verbose_name = 'Отчет по задаче'
        verbose_name_plural = 'Отчеты по задаче'


class ObjectivesDone(models.Model):
    name = models.TextField(blank=True, verbose_name='Что сделать')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               verbose_name='Автор задачи')
    created_date = models.DateField(default=timezone.now, verbose_name='Дата завершения задачи')
    reports = models.TextField(blank=True, null=True, verbose_name='Отчеты по задаче')
    departments = models.ManyToManyField(Department, blank=True, verbose_name='Задание для отдела:')

    def publish(self):
        self.created = timezone.now()
        self.save()

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Выполненная задача'
        verbose_name_plural = 'Выполненные задачи'


class ScheduledTasks(models.Model):
    start_date = models.DateField(blank=True, null=True, max_length=64, verbose_name='На какой день(дни) задание')
    REGULARITY_OPTIONS = [
        ('None', 'Не повторять'),
        ('week', 'Неделя'),
        ('month', 'Месяц'),
        ('on weekends', 'По выходным'),
        ('on workdays', 'По будням'),
        ]
    regularity = models.CharField(max_length=64, choices=REGULARITY_OPTIONS, default=None,
                                  verbose_name='С какой периодичностью выполнять задание')
    date_list = models.TextField(blank=True, null=True, verbose_name='Все даты задания:')
    name = models.CharField(max_length=64, null=True, blank=True, verbose_name='Название задания')
    text = models.TextField(blank=True, null=True, verbose_name='Что сделать(подробно):')
    created = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE,
                               verbose_name='Автор задачи')
    departments = models.ManyToManyField(Department, blank=True, verbose_name='Задание для отдела:')

    def __str__(self):
        return str(self.name)

    def publish(self):
        self.created = timezone.now()
        self.save()

    class Meta:
        verbose_name = 'Запланированная задача'
        verbose_name_plural = 'Запланированные задачи'


class RecordTags(models.Model):
    name = models.CharField(max_length=64, null=True, blank=True, verbose_name='Название категории')
    text = models.TextField(blank=True, null=True, verbose_name='Что вставляется в отчет')
    departments = models.ManyToManyField(Department, blank=True, verbose_name='Относится к отделу:')

    def __str__(self):
        return str(self.name)

    def publish(self):
        self.created = timezone.now()
        self.save()

    class Meta:
        verbose_name = 'Категория для отчета'
        verbose_name_plural = 'Категории для отчета'


class Tiles(models.Model):
    name = models.CharField(max_length=64, null=True, blank=True, verbose_name='Название категории документов')
    departments = models.ManyToManyField(Department, blank=True, verbose_name='Относится к отделу:')
    image = models.ImageField(blank=True, null=True, upload_to='images/',
                              verbose_name='Изображение категории документов')

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Категория документов'
        verbose_name_plural = 'Категории документов'


class Devices(models.Model):
    name = models.CharField(max_length=64, null=True, blank=True, verbose_name='Название устройства')
    image = models.ImageField(blank=True, null=True, upload_to='images/',
                              verbose_name='Изображение устройства')

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Устройство'
        verbose_name_plural = 'Устройства'


class Docs(models.Model):
    name = models.CharField(max_length=64, null=True, blank=True, verbose_name='Название документа')
    tile_category = models.ForeignKey(Tiles, blank=True, null=True, on_delete=models.CASCADE,
                                      verbose_name='Относится к категории документов')
    image = models.ImageField(blank=True, null=True, upload_to='images/',
                              verbose_name='Изображение документа')
    file = models.FileField(blank=True, null=True, upload_to='files/', verbose_name='Файл')

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'


class ManualDocs(Docs):
    device = models.ForeignKey(Devices, blank=True, null=True, on_delete=models.CASCADE,
                               verbose_name='Относится к устройству')
    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Мануал'
        verbose_name_plural = 'Мануалы'


class Converters(models.Model):
    number = models.IntegerField(verbose_name="Номер конвертера")
    #LOCATIONS = (("Studio_1", "Студия 1"), ("Studio_2", "Студия 2"), ("Studio_3", "Студия 3"))
    location = models.CharField(max_length=128, verbose_name="Где находится", blank=True, null=True)
    description = models.TextField(max_length=256, verbose_name="Примечание", blank=True, null=True, default="Добавить...")

    def __str__(self):
        return str(self.number)

    class Meta:
        verbose_name = 'Конвертер'
        verbose_name_plural = 'Конвертеры DAC-70'



