import requests
import requests_cache
import os
from config import Config

# Cache API calls for 1 hour
requests_cache.install_cache('travel_cache', expire_after=3600)

class TripPlanner:
    def __init__(self, origin, destination, dates, budget):
        self.origin = origin.strip()
        self.destination = destination.strip()
        self.dates = dates.strip()
        self.budget = float(budget)
        self.api_key = Config.GOOGLE_MAPS_API_KEY
        
    def get_distance(self):
        """Get distance between cities using Google Maps"""
        try:
            url = f"https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                'origins': self.origin,
                'destinations': self.destination,
                'key': self.api_key
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK':
                distance = data['rows'][0]['elements'][0]['distance']['text']
                duration = data['rows'][0]['elements'][0]['duration']['text']
                return f"{distance} ({duration})"
            return "Distance unavailable"
        except Exception as e:
            return f"Error: {str(e)}"

    def estimate_flight_cost(self):
        """Simple flight cost estimation"""
        base_cost = 100 + (self.budget * 0.1)
        return f"${base_cost:.0f} - ${base_cost * 1.5:.0f}"

    def suggest_activities(self):
        """AI-powered activity suggestions"""
        activities = {
            'Paris': ['Eiffel Tower', 'Louvre Museum', 'Seine River Cruise'],
            'Tokyo': ['Shibuya Crossing', 'Senso-ji Temple', 'TeamLab Borderless'],
            'New York': ['Statue of Liberty', 'Times Square', 'Central Park']
        }
        return activities.get(self.destination, ['Explore local markets', 'Try street food', 'Visit landmarks'])

    def generate_itinerary(self):
        """Generate complete trip itinerary"""
        try:
            distance = self.get_distance()
            flight_cost = self.estimate_flight_cost()
            activities = self.suggest_activities()
            
            return {
                'origin': self.origin,
                'destination': self.destination,
                'dates': self.dates,
                'budget': f"${self.budget:,.0f}",
                'distance': distance,
                'flight_cost': flight_cost,
                'activities': activities,
                'daily_budget': f"${self.budget/len(self.dates.split('to'))/2:.0f}"
            }
        except Exception as e:
            raise Exception(f"Failed to generate itinerary: {str(e)}")
