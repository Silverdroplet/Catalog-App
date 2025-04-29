import io
import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models import (
    Collection,
    Equipment,
    Review,
    Loan,
    Profile,
    EquipmentImage,
    CollectionAccessRequest,
    BorrowRequest,
    LibrarianRequests,
    Notification,
)

class CollectionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('u', 'u@example.com', 'pw')
        self.eq = Equipment.objects.create(name='Ball', added_by=self.user)

    def test_str_and_default_visibility(self):
        coll = Collection.objects.create(title='My Coll', creator=self.user)
        self.assertEqual(str(coll), 'My Coll')
        self.assertEqual(coll.visibility, 'public')

    def test_is_accessible_by(self):
        u2 = User.objects.create_user('u2', 'u2@example.com', 'pw')
        # public collection
        pub = Collection.objects.create(title='Pub', creator=self.user)
        self.assertTrue(pub.is_accessible_by(u2))
        # private collection, not allowed
        priv = Collection.objects.create(title='Priv', creator=self.user, visibility='private')
        self.assertFalse(priv.is_accessible_by(self.user))
        # add to allowed_users
        priv.allowed_users.add(self.user)
        self.assertTrue(priv.is_accessible_by(self.user))
        # librarian override
        lib = User.objects.create_user('lib', 'lib@example.com', 'pw')
        lib.profile.is_librarian = True
        lib.profile.save()
        self.assertTrue(priv.is_accessible_by(lib))

    def test_clean_prevents_duplicate_private(self):
        c1 = Collection.objects.create(title='C1', creator=self.user, visibility='private')
        c1.items.add(self.eq)
        c1.save()
        c2 = Collection.objects.create(title='C2', creator=self.user, visibility='private')
        c2.items.add(self.eq)
        with self.assertRaises(ValidationError):
            c2.full_clean()  # should fail because eq already in c1

class EquipmentModelTest(TestCase):
    def test_str_and_defaults(self):
        eq = Equipment.objects.create(name="Test E")
        self.assertEqual(str(eq), "Test E")
        self.assertTrue(eq.is_available)
        self.assertEqual(eq.status, 'checked-in')

class ReviewModelTest(TestCase):
    def test_str(self):
        user = User.objects.create_user('u', 'u@example.com', 'pw')
        eq = Equipment.objects.create(name='E1')
        rev = Review.objects.create(equipment=eq, user=user, rating=5, comment="Great")
        self.assertEqual(str(rev), "Review by u on E1 (5)")

class LoanModelTest(TestCase):
    def test_str_and_dates(self):
        user = User.objects.create_user('u', 'u@example.com', 'pw')
        eq = Equipment.objects.create(name='E2')
        loan = Loan.objects.create(
            user=user,
            equipment=eq,
            returnDate=timezone.now() + datetime.timedelta(days=1)
        )
        self.assertIn("u borrowed E2", str(loan))

class ProfileModelTest(TestCase):
    def test_auto_profile_and_str(self):
        user = User.objects.create_user('u', 'u@example.com', 'pw')
        # Profile should be auto-created
        prof = user.profile
        self.assertIsNotNone(prof)
        self.assertEqual(str(prof), 'u')
        self.assertFalse(prof.is_librarian)

class EquipmentImageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('u', 'u@example.com', 'pw')
        self.eq = Equipment.objects.create(name='E3', added_by=self.user)
        # fake image file
        self.upload = SimpleUploadedFile("test.png", b"PNGDATA", content_type="image/png")

    def test_str_and_delete(self):
        img = EquipmentImage.objects.create(equipment=self.eq, image=self.upload, caption="Img")
        self.assertEqual(str(img), f"Image for {self.eq.name}")
        img_id = img.id
        img.delete()
        with self.assertRaises(EquipmentImage.DoesNotExist):
            EquipmentImage.objects.get(pk=img_id)

class AccessRequestModelTest(TestCase):
    def test_str(self):
        u = User.objects.create_user('u', 'u@example.com', 'pw')
        coll = Collection.objects.create(title='C', creator=u)
        req = CollectionAccessRequest.objects.create(user=u, collection=coll)
        self.assertIn("requested access to C", str(req))

class BorrowRequestModelTest(TestCase):
    def test_str(self):
        u = User.objects.create_user('u', 'u@example.com', 'pw')
        eq = Equipment.objects.create(name='E4')
        br = BorrowRequest.objects.create(item=eq, patron=u)
        self.assertIn("requested E4", str(br))

class LibrarianRequestsModelTest(TestCase):
    def test_str(self):
        u = User.objects.create_user('u', 'u@example.com', 'pw')
        lr = LibrarianRequests.objects.create(patron=u)
        self.assertIn("requested to be a librarian", str(lr))

class NotificationModelTest(TestCase):
    def test_str_and_default(self):
        u = User.objects.create_user('u', 'u@example.com', 'pw')
        note = Notification.objects.create(user=u, message="Hello")
        self.assertTrue(str(note).startswith("Notification for u: Hello"))
        self.assertFalse(note.is_read)