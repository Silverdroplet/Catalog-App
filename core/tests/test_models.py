from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Equipment

class EquipmentModelTest(TestCase):
    def test_equipment_str(self):
        equipment = Equipment.objects.create(name="Test Equipment")
        self.assertEqual(str(equipment), "Test Equipment")

    def test_equipment_is_available_default(self):
        equipment = Equipment.objects.create(name="Another Test Equipment")
        self.assertTrue(equipment.is_available, "New equipment should be available by default")