"""Create travel.db with places table and sample Cairo & Alexandria data."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "travel.db"

SAMPLE_PLACES = [
    # ── CAIRO · Museums ──────────────────────────────────────────────────────
    ("Egyptian Museum", "Cairo", "museum", 300, 4.5),
    ("Grand Egyptian Museum", "Cairo", "museum", 600, 4.9),
    ("Coptic Museum", "Cairo", "museum", 200, 4.2),
    ("Museum of Islamic Art", "Cairo", "museum", 150, 4.4),
    ("National Museum of Egyptian Civilization", "Cairo", "museum", 200, 4.6),
    ("Gayer-Anderson Museum", "Cairo", "museum", 150, 4.3),
    ("Manial Palace Museum", "Cairo", "museum", 150, 4.2),
    ("Cairo Geological Museum", "Cairo", "museum", 50, 3.9),
    ("Agricultural Museum", "Cairo", "museum", 30, 3.7),
    ("Police Museum", "Cairo", "museum", 30, 3.8),
    ("Abdeen Palace Museum", "Cairo", "museum", 100, 4.0),
    ("Mukhtar Museum", "Cairo", "museum", 50, 4.0),

    # ── CAIRO · Historical & Attractions ─────────────────────────────────────
    ("Pyramids of Giza", "Cairo", "attraction", 400, 4.8),
    ("Sphinx of Giza", "Cairo", "attraction", 400, 4.8),
    ("Saqqara Necropolis", "Cairo", "attraction", 350, 4.6),
    ("Dahshur Pyramids", "Cairo", "attraction", 150, 4.5),
    ("Cairo Tower", "Cairo", "attraction", 250, 4.3),
    ("Saladin Citadel", "Cairo", "attraction", 200, 4.6),
    ("Memphis Open Air Museum", "Cairo", "attraction", 150, 4.3),
    ("Ben Ezra Synagogue", "Cairo", "attraction", 0, 4.2),
    ("Hanging Church", "Cairo", "attraction", 0, 4.5),
    ("Mosque of Ibn Tulun", "Cairo", "attraction", 0, 4.5),
    ("Al-Muizz Street", "Cairo", "attraction", 0, 4.7),
    ("Bab Zuweila Gate", "Cairo", "attraction", 50, 4.3),
    ("Al-Azhar Park", "Cairo", "attraction", 30, 4.5),
    ("Nilometer on Rhoda Island", "Cairo", "attraction", 30, 4.1),
    ("Wekalet El Ghouri", "Cairo", "attraction", 0, 4.2),
    ("Cairo Opera House", "Cairo", "attraction", 300, 4.5),
    ("El-Moez Bab Al-Nasr Cemetery", "Cairo", "attraction", 0, 4.0),
    ("Fustat Archaeological Park", "Cairo", "attraction", 50, 4.0),

    # ── CAIRO · Religious ─────────────────────────────────────────────────────
    ("Al-Azhar Mosque", "Cairo", "religious", 0, 4.6),
    ("Sultan Hassan Mosque", "Cairo", "religious", 100, 4.6),
    ("Al-Rifa'i Mosque", "Cairo", "religious", 100, 4.5),
    ("Mosque of Amr ibn al-As", "Cairo", "religious", 0, 4.3),
    ("Al-Hussein Mosque", "Cairo", "religious", 0, 4.4),
    ("Church of St. Sergius and Bacchus", "Cairo", "religious", 0, 4.3),
    ("Church of the Virgin Mary - Zeitoun", "Cairo", "religious", 0, 4.2),
    ("St. Mark Cathedral - Abbassia", "Cairo", "religious", 0, 4.1),

    # ── CAIRO · Cinemas ───────────────────────────────────────────────────────
    ("Cineplex - Mall of Arabia", "Cairo", "cinema", 180, 4.2),
    ("Vox Cinemas - Cairo Festival City", "Cairo", "cinema", 200, 4.4),
    ("Cineplex - City Stars", "Cairo", "cinema", 180, 4.1),
    ("Cine Rotana - Heliopolis", "Cairo", "cinema", 160, 4.0),
    ("Renaissance Cinema - Nile City Towers", "Cairo", "cinema", 190, 4.2),
    ("Galaxy Cinema - El Haram", "Cairo", "cinema", 120, 3.9),
    ("Odeon Cinema - Downtown", "Cairo", "cinema", 100, 3.8),

    # ── CAIRO · Malls & Shopping ──────────────────────────────────────────────
    ("Mall of Arabia", "Cairo", "mall", 0, 4.4),
    ("City Stars Mall", "Cairo", "mall", 0, 4.4),
    ("Cairo Festival City Mall", "Cairo", "mall", 0, 4.5),
    ("Mall of Egypt", "Cairo", "mall", 0, 4.3),
    ("Citystars Heliopolis", "Cairo", "mall", 0, 4.3),
    ("Point 90 Mall", "Cairo", "mall", 0, 4.1),
    ("Dandy Mega Mall", "Cairo", "mall", 0, 4.0),
    ("Khan el-Khalili Bazaar", "Cairo", "mall", 0, 4.4),
    ("Arkadia Mall", "Cairo", "mall", 0, 3.9),
    ("Genena Mall - Nasr City", "Cairo", "mall", 0, 3.8),
    ("Downtown Cairo Market Street", "Cairo", "mall", 0, 4.1),

    # ── CAIRO · Cafes ─────────────────────────────────────────────────────────
    ("Zamalek Riverside Cafe", "Cairo", "cafe", 150, 4.1),
    ("Cafe Riche - Downtown", "Cairo", "cafe", 120, 4.3),
    ("The Smokery - Zamalek", "Cairo", "cafe", 200, 4.2),
    ("Sequoia - Zamalek", "Cairo", "cafe", 250, 4.5),
    ("Cilantro Cafe - Maadi", "Cairo", "cafe", 130, 4.0),
    ("The Tap West - 6th of October", "Cairo", "cafe", 180, 4.1),
    ("Beanos Cafe - Heliopolis", "Cairo", "cafe", 100, 4.0),
    ("Costa Coffee - City Stars", "Cairo", "cafe", 150, 4.1),
    ("Kazoku - New Cairo", "Cairo", "cafe", 200, 4.3),
    ("Lucille's - Zamalek", "Cairo", "cafe", 220, 4.2),
    ("Roastery Cafe - Maadi", "Cairo", "cafe", 160, 4.2),
    ("Koshk Al Ahram Cafe - Giza", "Cairo", "cafe", 60, 3.9),
    ("Trianon Patisserie - Heliopolis", "Cairo", "cafe", 110, 4.1),

    # ── CAIRO · Dining ────────────────────────────────────────────────────────
    ("Nile Dinner Cruise", "Cairo", "dining", 1200, 4.5),
    ("Koshary El Tahrir", "Cairo", "dining", 40, 4.6),
    ("Abou El Sid - Zamalek", "Cairo", "dining", 450, 4.5),
    ("Zitouni - Four Seasons Nile Plaza", "Cairo", "dining", 800, 4.6),
    ("Sabaya - Semiramis Intercontinental", "Cairo", "dining", 700, 4.4),
    ("Felfela Restaurant - Downtown", "Cairo", "dining", 200, 4.3),
    ("Kebdet El Prince - Downtown", "Cairo", "dining", 80, 4.4),
    ("Andrea Restaurant - Giza", "Cairo", "dining", 350, 4.4),
    ("Naguib Mahfouz Cafe & Restaurant", "Cairo", "dining", 300, 4.2),
    ("The Grill - Marriott Cairo", "Cairo", "dining", 900, 4.5),

    # ── CAIRO · Parks & Nature ────────────────────────────────────────────────
    ("Al-Azhar Park", "Cairo", "park", 30, 4.5),
    ("Fish Garden - Zamalek", "Cairo", "park", 10, 4.0),
    ("Orman Botanical Garden", "Cairo", "park", 15, 4.1),
    ("Aquarium Grotto Garden", "Cairo", "park", 10, 3.9),
    ("Pharaonic Village", "Cairo", "park", 350, 4.2),
    ("Cairo Zoo", "Cairo", "park", 10, 3.8),
    ("Family Park - New Cairo", "Cairo", "park", 50, 4.2),

    # ── CAIRO · Tours ─────────────────────────────────────────────────────────
    ("Islamic Cairo Walking Tour", "Cairo", "tour", 500, 4.4),
    ("Coptic Cairo Walking Tour", "Cairo", "tour", 400, 4.3),
    ("Felucca Ride on the Nile", "Cairo", "tour", 200, 4.5),
    ("Hot Air Balloon over Giza", "Cairo", "tour", 2500, 4.7),
    ("Sound and Light Show - Pyramids", "Cairo", "tour", 500, 4.3),
    ("Day Trip to Fayoum Oasis", "Cairo", "tour", 800, 4.5),
    ("Camel Ride at Giza Plateau", "Cairo", "tour", 300, 4.0),

    # ── CAIRO · Hotels ────────────────────────────────────────────────────────
    ("Marriott Mena House", "Cairo", "hotel", 4500, 4.7),
    ("Four Seasons Nile Plaza", "Cairo", "hotel", 6000, 4.8),
    ("Steigenberger Tahrir", "Cairo", "hotel", 2800, 4.5),
    ("Kempinski Nile Hotel", "Cairo", "hotel", 5500, 4.7),
    ("Semiramis Intercontinental", "Cairo", "hotel", 3500, 4.4),
    ("Novotel Cairo Airport", "Cairo", "hotel", 2000, 4.2),
    ("Ibis Cairo Citadel", "Cairo", "hotel", 900, 3.9),
    ("Hilton Cairo Heliopolis", "Cairo", "hotel", 3200, 4.4),
    ("JW Marriott Cairo", "Cairo", "hotel", 5800, 4.8),
    ("Sheraton Cairo Hotel", "Cairo", "hotel", 2600, 4.3),
    ("Conrad Cairo Hotel", "Cairo", "hotel", 4800, 4.6),
    ("Sofitel Cairo Nile El Gezirah", "Cairo", "hotel", 5200, 4.7),
    ("Le Meridien Cairo Airport", "Cairo", "hotel", 1800, 4.1),
    ("Fairmont Nile City", "Cairo", "hotel", 5000, 4.7),
    ("Cairo Marriott Hotel & Omar Khayyam Casino", "Cairo", "hotel", 4200, 4.5),
    # ── CAIRO · Mansions & Palaces ────────────────────────────────────────────
    ("Baron Palace Heliopolis", "Cairo", "hotel", 7500, 4.6),
    ("Al Sawy Palace Zamalek", "Cairo", "hotel", 6800, 4.5),
    ("Khedivial Palace - Shubra", "Cairo", "hotel", 5500, 4.3),
    ("Ain Helwan Palace Resort", "Cairo", "hotel", 4800, 4.4),
    ("Villa Belle Epoque - Heliopolis", "Cairo", "hotel", 8000, 4.7),

    # ── ALEXANDRIA · Museums ─────────────────────────────────────────────────
    ("Bibliotheca Alexandrina", "Alexandria", "museum", 100, 4.7),
    ("Alexandria National Museum", "Alexandria", "museum", 120, 4.2),
    ("Greco-Roman Museum", "Alexandria", "museum", 100, 4.3),
    ("Royal Jewelry Museum", "Alexandria", "museum", 75, 4.2),
    ("Cavafy Museum", "Alexandria", "museum", 50, 4.1),
    ("Fine Arts Museum Alexandria", "Alexandria", "museum", 40, 3.9),
    ("Hydrobiological Museum & Aquarium", "Alexandria", "museum", 40, 3.8),
    ("Anfoushi Museum", "Alexandria", "museum", 60, 4.0),

    # ── ALEXANDRIA · Historical & Attractions ────────────────────────────────
    ("Citadel of Qaitbay", "Alexandria", "attraction", 150, 4.5),
    ("Catacombs of Kom el Shoqafa", "Alexandria", "attraction", 200, 4.4),
    ("Roman Amphitheater - Kom el Dikka", "Alexandria", "attraction", 100, 4.1),
    ("Pompey's Pillar", "Alexandria", "attraction", 100, 4.0),
    ("Stanley Bridge", "Alexandria", "attraction", 0, 4.3),
    ("Montaza Palace", "Alexandria", "attraction", 50, 4.4),
    ("Ras El-Tin Palace", "Alexandria", "attraction", 50, 4.1),
    ("Abu Abbas El-Mursi Mosque", "Alexandria", "attraction", 0, 4.5),
    ("El-Nabi Daniel Mosque", "Alexandria", "attraction", 0, 4.0),
    ("Fort of Abukir", "Alexandria", "attraction", 30, 3.9),
    ("Abukir Bay Battlefield", "Alexandria", "attraction", 0, 4.0),
    ("Serapeum of Alexandria", "Alexandria", "attraction", 100, 4.1),
    ("Chatby Necropolis", "Alexandria", "attraction", 50, 3.8),
    ("Alexandria Corniche Waterfront", "Alexandria", "attraction", 0, 4.4),

    # ── ALEXANDRIA · Religious ────────────────────────────────────────────────
    ("Abu Abbas El-Mursi Mosque", "Alexandria", "religious", 0, 4.5),
    ("St. Mark Cathedral - Alexandria", "Alexandria", "religious", 0, 4.3),
    ("Church of St. Catherine", "Alexandria", "religious", 0, 4.1),
    ("El-Mursi Abul Abbas Complex", "Alexandria", "religious", 0, 4.4),

    # ── ALEXANDRIA · Cinemas ──────────────────────────────────────────────────
    ("Vox Cinemas - San Stefano", "Alexandria", "cinema", 200, 4.4),
    ("Cineplex - City Centre Alexandria", "Alexandria", "cinema", 180, 4.2),
    ("Green Plaza Cinema", "Alexandria", "cinema", 150, 4.0),
    ("Amir Cinema - Raml Station", "Alexandria", "cinema", 80, 3.7),

    # ── ALEXANDRIA · Malls & Shopping ─────────────────────────────────────────
    ("City Centre Alexandria", "Alexandria", "mall", 0, 4.4),
    ("San Stefano Grand Plaza", "Alexandria", "mall", 0, 4.3),
    ("Green Plaza Mall", "Alexandria", "mall", 0, 4.1),
    ("Zahran Mall", "Alexandria", "mall", 0, 4.0),
    ("Carrefour Alexandria City Centre", "Alexandria", "mall", 0, 4.1),
    ("Attarin Antiques Market", "Alexandria", "mall", 0, 4.2),

    # ── ALEXANDRIA · Cafes ────────────────────────────────────────────────────
    ("Alexandria Library Cafe", "Alexandria", "cafe", 90, 4.0),
    ("Trianon Cafe - Raml Station", "Alexandria", "cafe", 120, 4.4),
    ("Elite Cafe - Raml", "Alexandria", "cafe", 100, 4.2),
    ("Athineos Cafe - Raml Station", "Alexandria", "cafe", 110, 4.3),
    ("Sofianopoulos Coffee", "Alexandria", "cafe", 80, 4.1),
    ("Coffee Roastery - San Stefano", "Alexandria", "cafe", 150, 4.2),
    ("Cap D'Or Bar & Cafe", "Alexandria", "cafe", 130, 4.1),
    ("Delices Patisserie", "Alexandria", "cafe", 95, 4.3),
    ("White and Blue Cafe - Stanley", "Alexandria", "cafe", 160, 4.2),

    # ── ALEXANDRIA · Dining ───────────────────────────────────────────────────
    ("Fish Market Lunch - Abu Qir", "Alexandria", "dining", 400, 4.2),
    ("Kadoura Seafood Restaurant", "Alexandria", "dining", 350, 4.5),
    ("Tikka Grill - San Stefano", "Alexandria", "dining", 500, 4.3),
    ("The Greek Club Restaurant", "Alexandria", "dining", 400, 4.2),
    ("Samakmak Restaurant", "Alexandria", "dining", 300, 4.4),
    ("Mohamed Ahmed Ful & Falafel", "Alexandria", "dining", 30, 4.6),
    ("Taverna Restaurant - Stanley", "Alexandria", "dining", 450, 4.1),
    ("Costa Brava Seafood", "Alexandria", "dining", 380, 4.3),

    # ── ALEXANDRIA · Parks & Nature ───────────────────────────────────────────
    ("Montaza Palace Gardens", "Alexandria", "park", 50, 4.4),
    ("Antoniades Garden", "Alexandria", "park", 20, 4.0),
    ("Shallalat Garden", "Alexandria", "park", 10, 3.9),
    ("El-Mamoura Beach", "Alexandria", "park", 30, 4.2),
    ("Agami Beach", "Alexandria", "park", 20, 4.1),
    ("Miami Beach Alexandria", "Alexandria", "park", 20, 4.0),

    # ── ALEXANDRIA · Tours ────────────────────────────────────────────────────
    ("Alexandria City Highlights Tour", "Alexandria", "tour", 500, 4.4),
    ("Snorkeling at Abu Qir Bay", "Alexandria", "tour", 400, 4.3),
    ("Day Trip to El Alamein", "Alexandria", "tour", 700, 4.5),
    ("Corniche Bike Ride", "Alexandria", "tour", 100, 4.2),
    ("Sunset Felucca on the Mediterranean", "Alexandria", "tour", 250, 4.4),

    # ── ALEXANDRIA · Hotels ───────────────────────────────────────────────────
    ("Four Seasons Alexandria", "Alexandria", "hotel", 5200, 4.6),
    ("Helnan Palestine Hotel", "Alexandria", "hotel", 2200, 4.3),
    ("San Stefano Grand Plaza Hotel", "Alexandria", "hotel", 3000, 4.4),
    ("Sheraton Montazah Hotel", "Alexandria", "hotel", 2800, 4.3),
    ("Tolip Hotel Alexandria", "Alexandria", "hotel", 1500, 4.1),
    ("Ibis Alexandria Smoha", "Alexandria", "hotel", 850, 3.9),
    ("Hilton Alexandria Corniche", "Alexandria", "hotel", 3400, 4.5),
    ("Paradise Inn Beach Resort", "Alexandria", "hotel", 1800, 4.2),
    ("Steigenberger Cecil Alexandria", "Alexandria", "hotel", 2500, 4.4),
    ("Royal Crown Hotel Alexandria", "Alexandria", "hotel", 1200, 4.0),
    # ── ALEXANDRIA · Mansions & Palaces ───────────────────────────────────────
    ("Montaza Royal Palace Suite", "Alexandria", "hotel", 9000, 4.8),
    ("Ras El-Tin Palace Guest Residence", "Alexandria", "hotel", 8500, 4.7),
    ("Villa Ambron - Sidi Bishr", "Alexandria", "hotel", 6500, 4.5),
    ("Le Metropole Heritage Hotel", "Alexandria", "hotel", 4000, 4.4),
    ("Villa Aghion Boutique Stay", "Alexandria", "hotel", 5800, 4.6),
]


def init_db(path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS places (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT NOT NULL,
                category TEXT NOT NULL,
                price INTEGER NOT NULL,
                rating REAL NOT NULL
            )
            """
        )
        cur = conn.execute("SELECT COUNT(*) FROM places")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                """
                INSERT INTO places (name, city, category, price, rating)
                VALUES (?, ?, ?, ?, ?)
                """,
                SAMPLE_PLACES,
            )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database ready: {DB_PATH}")
