from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    # Create a UserProfile if the User is newly created
    if created:
        UserProfile.objects.create(user=instance)
    # Save the profile if it exists
    elif hasattr(instance, 'profile'):
        instance.profile.save()
