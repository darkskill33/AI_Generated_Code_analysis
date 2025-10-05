from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from .models import ParkingLocation, Reservation, ParkingSpot, Review

class UserReservationForm(forms.ModelForm):
    start_time = forms.DateField(
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Start Date"
    )
    end_time = forms.DateField(
        label="End Date",
        required=True,
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
            duration_in_days = (end_time - start_time).days
            if duration_in_days < 0:
                raise forms.ValidationError("End time must be later than start time.")
            cleaned_data['duration_in_days'] = duration_in_days
        return cleaned_data

    def save(self, commit=True):
        reservation = super().save(commit=False)
        reservation.end_time = self.cleaned_data['end_time']
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

        if location and new_name:
            raise forms.ValidationError("Choose either existing location or provide a new one.")

        if not location and new_name:
            location, created = ParkingLocation.objects.get_or_create(name=new_name)
            if created and new_address:
                location.address = new_address
                location.save()
            return location

        return location


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
