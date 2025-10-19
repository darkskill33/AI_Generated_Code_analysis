from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from ..forms import UserReservationForm, calculate_duration, ParkingSpotForm
from ..models import ParkingSpot, ParkingLocation, Reservation

class CalculateDurationTests(TestCase):
    def test_calculate_duration_positive(self):
        """Test positive duration calculation"""
        start = timezone.datetime(2025, 10, 1)
        end = timezone.datetime(2025, 10, 5)
        # Prompt/fiksuotas užklausos turinys: "Apskaičiuok trukmę tarp 2025-10-01 ir 2025-10-05"
        duration = calculate_duration(start, end)
        self.assertEqual(duration, 4)

    def test_calculate_duration_negative_raises(self):
        """Test negative duration raises ValidationError"""
        start = timezone.datetime(2025, 10, 5)
        end = timezone.datetime(2025, 10, 1)
        # Prompt/fiksuotas užklausos turinys: "Apskaičiuok trukmę tarp 2025-10-05 ir 2025-10-01"
        with self.assertRaises(Exception):
            calculate_duration(start, end)

class UserReservationFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.spot = ParkingSpot.objects.create(spot_number=1, daily_price=10)

    def test_form_valid_data_creates_reservation(self):
        """Test valid form data creates reservation with correct duration"""
        data = {
            'user': self.user.id,
            'spot': self.spot.id,
            'start_time': '2025-10-01',
            'end_time': '2025-10-05'
        }
        form = UserReservationForm(data=data)
        self.assertTrue(form.is_valid())
        reservation = form.save()
        self.assertEqual(reservation.duration_in_days, 4)
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.spot, self.spot)

    def test_form_invalid_dates_shows_error(self):
        """Test form with end_time before start_time is invalid"""
        data = {
            'user': self.user.id,
            'spot': self.spot.id,
            'start_time': '2025-10-05',
            'end_time': '2025-10-01'
        }
        form = UserReservationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('End time must be later than start time.', str(form.errors))

class ParkingSpotFormTests(TestCase):
    def test_new_location_creation(self):
        """Test that providing new location data creates ParkingLocation"""
        data = {
            'location': '',
            'spot_number': 1,
            'daily_price': 20,
            'new_location_name': 'Test Lot',
            'new_location_address': 'Test Address'
        }
        form = ParkingSpotForm(data=data)
        self.assertTrue(form.is_valid())
        spot = form.save()
        self.assertEqual(spot.location.name, 'Test Lot')
        self.assertEqual(spot.location.address, 'Test Address')

    def test_existing_location_conflict_shows_error(self):
        """Test that specifying both existing and new location raises error"""
        existing_location = ParkingLocation.objects.create(name='Existing', address='Addr')
        data = {
            'location': existing_location.id,
            'spot_number': 2,
            'daily_price': 15,
            'new_location_name': 'Conflict',
            'new_location_address': 'Address'
        }
        form = ParkingSpotForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('Choose either an existing location or provide a new one.', str(form.errors))
