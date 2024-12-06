# voting/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import localtime, now
from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('У пользователя должен быть указан email')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(email, first_name, last_name, password, **extra_fields)
    
class User(AbstractUser):
    username = None

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

class Competition(models.Model):
    STATUS_CHOICES = [
        ('available', 'Доступен для участия'),
        ('voting', 'Идёт голосование'),
        ('completed', 'Завершён'),
    ]
    VOTING_TYPE_CHOICES = [
        ('single_choice', 'Одиночный выбор'),
        ('multiple_choice', 'Множественный выбор'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    voting_type = models.CharField(max_length=50, choices=VOTING_TYPE_CHOICES, default='single_choice')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="competitions")

    def update_status(self):
        current_time = localtime(now())
        start_date_local = localtime(self.start_date)
        end_date_local = localtime(self.end_date)
        new_status = self.status

        if current_time < start_date_local:
            new_status = 'available'
        elif start_date_local<= current_time <= end_date_local:
            new_status = 'voting'
        else:
            new_status = 'completed'

        if new_status != self.status:
            self.status = new_status
            super().save(update_fields=['status'])

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if not is_new:
            self.update_status()


class Participant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="participants")
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="participants")
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)


class Vote(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="votes")
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="votes")
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="votes")

    class Meta:
        unique_together = ('competition', 'voter', 'participant')


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)