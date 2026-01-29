import requests
from app.config import settings

def search_tours(departure: str = None, destination: str = None, people: int = None, days: int = None):
    try:
        params = {}

        if departure: 
            params["diemXuatPhat_like"] = departure
            
        if destination: 
            params["diemDen_like"] = destination 

        if days: 
            params["soNgay_lte"] = days

        print(f"📡 Calling Java/Mock: {settings.TOUR_SEARCH_API} | Params: {params}")
        
        response = requests.get(settings.TOUR_SEARCH_API, params=params, timeout=3)
        
        if response.status_code == 200:
            result = response.json()
            
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return result.get("data", [])
            else:
                return []
                
    except Exception as e:
        print(f"⚠️ Backend Error: {e}")
        return []