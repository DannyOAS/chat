"""User factory for tests."""
import factory
from django.contrib.auth import get_user_model
from faker import Faker

from accounts.models import UserProfile

User = get_user_model()
fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password after user creation."""
        if not create:
            return

        if extracted:
            obj.set_password(extracted)
        else:
            obj.set_password("testpass123")
        obj.save()

    @factory.post_generation
    def profile(obj, create, extracted, **kwargs):
        """Create user profile."""
        if not create:
            return

        UserProfile.objects.get_or_create(
            user=obj,
            defaults={"email_verified": False},
        )
