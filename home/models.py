from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import User
# Define the category choices for better structure and validation
CATEGORY_CHOICES = [
    ('Food', 'Food'),
    ('Shopping', 'Shopping'),
    ('Transport', 'Transport'),
    ('Entertainment', 'Entertainment'),
    ('Utilities', 'Utilities'),
    ('Other', 'Other'),
]

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)   # category instead of description
    amount = models.IntegerField()
    date = models.DateField()

    def __str__(self):
        return f"{self.name} - {self.amount} on {self.date}"

    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    salary = models.FloatField(default=0)
    monthly_budget = models.FloatField(default=0)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
