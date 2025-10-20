from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from .models import ParkingLocation, Reservation, ParkingSpot, Review


# Pagalbinė funkcija rezervacijos trukmei
def calculate_duration(start_time, end_time):
    """
    Apskaičiuoja trukmę dienomis tarp start_time ir end_time.
    Tikrina, ar end_time vėliau nei start_time.
    """
    duration_in_days = (end_time - start_time).days
    if duration_in_days < 0:
        raise forms.ValidationError("End time must be later than start time.")
    return duration_in_days


# Pagalbinė funkcija naujai lokacijai
def get_or_create_parking_location(name, address):
    """
    Sukuria naują ParkingLocation objektą arba grąžina jau egzistuojantį.
    """
    location, _ = ParkingLocation.objects.get_or_create(
        name=name,
        defaults={'address': address or ""}
    )
    return location


class UserReservationForm(forms.ModelForm):
    start_time = forms.DateField(
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Start Date"
    )
    end_time = forms.DateField(
        label="End Date",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    spot = forms.ModelChoiceField(queryset=ParkingSpot.objects.all(), required=False)

    class Meta:
        model = Reservation
        fields = ['user', 'spot', 'start_time', 'end_time']

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            cleaned_data['duration_in_days'] = calculate_duration(start_time, end_time)

        return cleaned_data

    def save(self, commit=True):
        reservation = super().save(commit=False)
        reservation.duration_in_days = self.cleaned_data['duration_in_days']

        if commit:
            reservation.save()
        return reservation


class ParkingSpotForm(forms.ModelForm):
    new_location_name = forms.CharField(
        max_length=100,
        required=False,
        label="New Location Name",
        help_text="Fill this to create a new parking location"
    )
    new_location_address = forms.CharField(
        max_length=255,
        required=False,
        label="New Location Address",
        help_text="Fill this to add the address of the new location"
    )

    class Meta:
        model = ParkingSpot
        fields = ['location', 'spot_number', 'daily_price']
        widgets = {
            'daily_price': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def clean_location(self):
        location = self.cleaned_data.get('location')
        new_name = self.cleaned_data.get('new_location_name')
        new_address = self.cleaned_data.get('new_location_address')

        # Draudžiame nurodyti ir egzistuojančią, ir naują lokaciją
        if location and new_name:
            raise forms.ValidationError(
                "Choose either an existing location or provide a new one."
            )

        # Jei nurodyta nauja lokacija – sukurti ją
        if new_name and not location:
            location = get_or_create_parking_location(new_name, new_address)

        return location


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
