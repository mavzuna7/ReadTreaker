from django.db import models

class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, blank=True, null=True)

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    genre = models.CharField(max_length=100, blank=True)
    year = models.IntegerField(null=True, blank=True)
    cover_path = models.CharField(max_length=500, blank=True)

class UserBook(models.Model):
    STATUS_CHOICES = [
        ('read', 'Прочитано'),
        ('want_to_read', 'Хочу прочитать'),
    ]
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    rating = models.IntegerField(null=True, blank=True)
    date_read = models.DateField(null=True, blank=True)
    description = models.TextField("Описание книги", blank=True)      # аннотация
    review = models.TextField("Мои впечатления", blank=True)   
    is_favorite = models.BooleanField("В избранном", default=False)      # личная рецензия
    date_start = models.DateField(null=True, blank=True, verbose_name="Дата начала чтения")
    date_end = models.DateField(null=True, blank=True, verbose_name="Дата окончания чтения")