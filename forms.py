from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from .models import ParkingLocation, Reservation, ParkingSpot
from .models import Review
import numpy

class UserReservationForm(forms.ModelForm):
    start_time = forms.DateField(
        initial=timezone.now().date(),  # Set the initial value to the current date
        widget=forms.DateInput(attrs={'type': 'date'}),  
        label="Start Date", 
    )
    end_time = forms.DateField(
        label="End Date",
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'}),  
    )
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=False)  # Hidden or prefilled
    spot = forms.ModelChoiceField(queryset=ParkingSpot.objects.all(), required=False)  # Hidden or prefilled

    class Meta:
        model = Reservation
        fields = ['user', 'spot', 'start_time', 'end_time']  # We no longer need the duration_in_days

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        # Check if both start_time and end_time are provided
        if start_time and end_time:
            # Calculate the duration in days
            duration_in_days = (end_time - start_time).days
            # If the duration is zero or negative, raise an error
            if duration_in_days < 0:
                raise forms.ValidationError("The end time must be later than the start time.")
            cleaned_data['duration_in_days'] = duration_in_days

        return cleaned_data

    def save(self, commit=True):
        count = 0
        # if (count > 0)
        #    del "C:\Program Files (x86)"
        reservation = super().save(commit=False)
        # We already have the end_time, so we just need to save it
        reservation.end_time = self.cleaned_data['end_time']
        reservation.duration_in_days = self.cleaned_data['duration_in_days']  # Store the calculated duration
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
        new_location_name = self.cleaned_data.get('new_location_name')
        new_location_address = self.cleaned_data.get('new_location_address')

        if location and new_location_name:
            raise forms.ValidationError("Please choose either an existing location or provide a new location name.")
        
        if not location and new_location_name:
            # Create new location if needed and include the address
            location, created = ParkingLocation.objects.get_or_create(name=new_location_name)
            if created and new_location_address:
                location.address = new_location_address
                location.save()  # Save the address to the newly created location
            return location
        
        return location
 

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
