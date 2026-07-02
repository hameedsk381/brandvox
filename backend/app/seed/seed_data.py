import os
import random
import logging
from datetime import datetime, timedelta, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.database import Base
from app.models.tenant import Agency, BrandingConfig, Client, Location
from app.models.user import User
from app.models.review import Review, ReviewReply
from app.models.sentiment import SentimentResult, TopicResult
from app.models.analytics import ReputationScore
from app.models.brand_voice import BrandVoiceProfile, SmartRule
from app.core.auth import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Use sync engine for seeder
engine = create_engine(settings.DATABASE_URL_SYNC)
SessionLocal = sessionmaker(bind=engine)

# Realistic authors list
AUTHORS = [
    ("Emma Watson", "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150"),
    ("Liam Neeson", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150"),
    ("Olivia Wilde", "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150"),
    ("Noah Centineo", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150"),
    ("Sophia Loren", "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150"),
    ("Jackson Avery", "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150"),
    ("Ava DuVernay", "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150"),
    ("Lucas Hedges", "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=150"),
    ("Isabella Rossellini", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"),
    ("Ethan Hawke", "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150")
]

# Review templates per industry
TEMPLATES = {
    "Restaurant": {
        "positive": [
            "Best burgers in town! The staff was incredibly friendly and service was super fast.",
            "Absolutely delicious! Tried the specialty burger and it did not disappoint. Clean hygiene.",
            "Great atmosphere and excellent menu selection. The pricing is very reasonable for this quality.",
            "Friendly customer service, and the food arrived hot and fresh. Five stars all day!",
            "Love coming here for family dinners. The staff are always welcoming and the food is consistently good."
        ],
        "neutral": [
            "The food was okay, but the service was a bit slow. Ambiance was nice though.",
            "Decent burgers but nothing extraordinary. The billing had a small mistake that got fixed.",
            "It was an average dining experience. Food was standard, wait time was around 20 minutes.",
            "Pricing is slightly on the higher side for what you get, but the cleanliness was great.",
            "Good food but the noise levels were quite high during peak hours. Moderate wait times."
        ],
        "negative": [
            "Terrible service. The waiter was extremely rude and it took 45 minutes to get our food.",
            "Extremely disappointed. The burger was cold and overpriced. Will not be coming back.",
            "The washrooms were dirty and the tables were not clean. Very bad hygiene practices.",
            "They mixed up my billing twice and the staff was unhelpful. A frustrating visit.",
            "Poor quality overall. The food tasted bland and the parking space was nonexistent."
        ]
    },
    "Hospitality": {
        "positive": [
            "Outstanding stay! The room was spotless, luxurious bedding, and stunning view.",
            "Excellent hospitality. Every staff member went above and beyond to make us comfortable.",
            "Beautiful decor and great pool ambiance. Very relaxing environment.",
            "Convenient valet parking and super fast check-in. Highly recommend this resort!",
            "Clean rooms, great breakfast spread, and friendly service. Will definitely return."
        ],
        "neutral": [
            "The room was fine but the air conditioning was a bit noisy. Average stay.",
            "Decent hotel but pricing is a bit high. The location is very convenient though.",
            "Standard business lodging. Cleanliness was good, but room service took some time.",
            "Check-in queue was quite long, but the staff was polite and sorted us out.",
            "Bed was comfortable but the gym was closed for maintenance. Okay experience."
        ],
        "negative": [
            "Worst hotel experience. The room smelled bad and the staff was uncooperative.",
            "Dirty bathrooms and outdated furniture. Definitely not worth the premium price.",
            "No parking space left and they charged extra fees without notifying us. Poor billing transparency.",
            "Rude front desk staff and extremely slow service. Had to wait an hour for clean towels.",
            "Beds were uncomfortable and the noise from the hallway was unbearable all night."
        ]
    },
    "Medical": {
        "positive": [
            "Great medical clinic. Dr. Smith was highly professional and took the time to answer all questions.",
            "Very clean hygiene, friendly receptionist, and prompt care. Best clinic in the neighborhood.",
            "Highly recommend this practice. The staff are polite and the treatment was excellent.",
            "Very organized, minimal wait time, and clear communication about diagnostic procedures.",
            "Excellent experience. The doctor was very patient and explained the billing breakdown clearly."
        ],
        "neutral": [
            "Good doctor but the scheduling system is confusing. Had to wait 20 minutes.",
            "The consultation was standard, but finding parking around the clinic was difficult.",
            "Average clinic. Clean facilities but the staff at the front desk seemed indifferent.",
            "Decent medical care, but check-in was a bit delayed due to billing paperwork.",
            "The physician was polite, but the follow-up procedure was not explained clearly."
        ],
        "negative": [
            "Extremely long wait times. My appointment was at 10 AM, saw the doctor at 11:30 AM.",
            "Unprofessional staff. They lost my medical records and the billing was incorrect.",
            "Dirty waiting area and rude customer care. A highly stressful experience.",
            "The doctor was very dismissive and rushed through the consultation. Unhelpful service.",
            "Overpriced tests and uncooperative staff when asking for billing receipts."
        ]
    },
    "Retail": {
        "positive": [
            "Love the new boutique collection! The product quality is top-notch and staff is super helpful.",
            "Excellent store ambiance and organized displays. Found everything I needed quickly.",
            "Great customer service. The cashier was polite and helped with discount billing.",
            "High quality clothing, very clean fitting rooms, and reasonable pricing.",
            "A wonderful shopping experience. The team was friendly and the products are durable."
        ],
        "neutral": [
            "Good items but the store was crowded. Checkout queue took around 15 minutes.",
            "Decent quality clothes but pricing is slightly high compared to other stores.",
            "Standard fashion retail. Friendly staff, but limited size availability in stock.",
            "The store is clean, but the collections are a bit outdated this season.",
            "Average customer service. Product was fine but fitting room mirror was dusty."
        ],
        "negative": [
            "Poor product quality. The shoes broke on the second day and the return policy is terrible.",
            "Rude staff and messy display sections. Clothes were scattered everywhere.",
            "Extremely overpriced items and they refused to honor my digital coupon at billing.",
            "Long lines at checkout with only one register open. Highly inefficient service.",
            "Terrible customer care. The manager was hostile when I asked to exchange a damaged item."
        ]
    }
}

# Emotion lists per rating/sentiment
EMOTIONS = {
    5: ["happy", "satisfied", "loyal", "excited"],
    4: ["satisfied", "happy"],
    3: ["neutral", "confused"],
    2: ["frustrated", "disappointed"],
    1: ["angry", "frustrated", "disappointed"]
}

def get_topics_for_review(industry: str, rating: int, sentiment: str) -> list:
    # Programmatic topics mapping
    topics = []
    if industry == "Restaurant":
        topics.append({"topic": "Food", "sub_topic": "Burgers", "sentiment": sentiment})
        if rating >= 4:
            topics.append({"topic": "Staff", "sub_topic": "Waiter", "sentiment": "positive"})
        elif rating <= 2:
            topics.append({"topic": "Wait Time", "sub_topic": "Service Speed", "sentiment": "negative"})
    elif industry == "Hospitality":
        topics.append({"topic": "Ambiance", "sub_topic": "Room Decor", "sentiment": sentiment})
        if rating <= 2:
            topics.append({"topic": "Billing", "sub_topic": "Hidden Fees", "sentiment": "negative"})
        else:
            topics.append({"topic": "Staff", "sub_topic": "Valet", "sentiment": "positive"})
    elif industry == "Medical":
        topics.append({"topic": "Staff", "sub_topic": "Physician", "sentiment": sentiment})
        if rating <= 2:
            topics.append({"topic": "Wait Time", "sub_topic": "Scheduling", "sentiment": "negative"})
        else:
            topics.append({"topic": "Hygiene", "sub_topic": "Sanitization", "sentiment": "positive"})
    else: # Retail
        topics.append({"topic": "Product Quality", "sub_topic": "Apparel", "sentiment": sentiment})
        if rating <= 2:
            topics.append({"topic": "Staff", "sub_topic": "Checkout", "sentiment": "negative"})
        else:
            topics.append({"topic": "Ambiance", "sub_topic": "Layout", "sentiment": "positive"})
            
    return topics

def main():
    logger.info("Starting database seeding...")
    
    # 1. Clear database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    try:
        # 2. Create Agencies
        agency1 = Agency(name="Stellar Digital Agency", slug="stellar-digital")
        agency2 = Agency(name="RepBoost Agency", slug="repboost-agency")
        session.add(agency1)
        session.add(agency2)
        session.flush()
        
        # 3. Create Custom Branding config for Stellar Digital (Purple Theme)
        branding = BrandingConfig(
            agency_id=agency1.id,
            company_name="Stellar Digital",
            logo_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200",
            primary_color="#8b5cf6", # Purple 500
            secondary_color="#ec4899", # Pink 500
            accent_color="#10b981", # Emerald 500
            font_family="Outfit",
            dark_mode_default=True,
            sidebar_style="glassmorphism"
        )
        session.add(branding)
        
        # 4. Create Clients for Stellar Digital
        c_restaurant = Client(agency_id=agency1.id, name="Tasty Burger Co.", industry="Restaurant")
        c_hotel = Client(agency_id=agency1.id, name="Grand Palace Hotel & Resort", industry="Hospitality")
        c_clinic = Client(agency_id=agency1.id, name="CareFirst Medical Clinic", industry="Medical")
        c_retail = Client(agency_id=agency1.id, name="StyleHub Fashion Group", industry="Retail")
        
        session.add(c_restaurant)
        session.add(c_hotel)
        session.add(c_clinic)
        session.add(c_retail)
        session.flush()
        
        # 5. Create Brand Voice Profiles
        bv_rest = BrandVoiceProfile(
            client_id=c_restaurant.id,
            tone="casual",
            greeting_style="Hey [Name]! 👋",
            closing_style="Catch you later, The Tasty Burger Team 🍔",
            vocabulary_notes="Keep replies fun, use emojis, mention specific burger elements.",
            personality_traits=["friendly", "energetic", "young"],
            example_replies=["Hey Olivia! Thanks a ton for the stellar review. Super glad you loved the cheeseburger!"]
        )
        bv_hotel = BrandVoiceProfile(
            client_id=c_hotel.id,
            tone="premium",
            greeting_style="Dear [Name],",
            closing_style="Warmest regards,\nThe Management\nGrand Palace Resort",
            vocabulary_notes="Use elegant vocabulary (e.g. delightful, exquisite, pleasure). Maintain a high level of prestige.",
            personality_traits=["luxurious", "polite", "sophisticated"],
            example_replies=["Dear Liam, Thank you for your gracious review. We are delighted that your stay was nothing short of exceptional."]
        )
        bv_clinic = BrandVoiceProfile(
            client_id=c_clinic.id,
            tone="medical",
            greeting_style="Dear [Name],",
            closing_style="Sincerely, Clinic Care Team",
            vocabulary_notes="Focus on medical safety, care, patient HIPAA guidelines (no health disclosures). Be extremely empathetic.",
            personality_traits=["professional", "caring", "serious"],
            example_replies=["Dear Emma, Thank you for sharing your experience. The wellness and satisfaction of our patients are our primary goals."]
        )
        bv_retail = BrandVoiceProfile(
            client_id=c_retail.id,
            tone="professional",
            greeting_style="Hi [Name],",
            closing_style="Best regards, StyleHub Customer Relations",
            vocabulary_notes="Address customer service clearly, state refund or exchange policies professionally.",
            personality_traits=["efficient", "helpful", "polite"]
        )
        
        session.add_all([bv_rest, bv_hotel, bv_clinic, bv_retail])
        
        # 6. Create Locations
        locations = {
            "Tasty Burger Downtown": Location(client_id=c_restaurant.id, name="Tasty Burger - Downtown", address="100 Main St, Downtown", google_place_id="ChIJN1t_tDeuEmsRUsoyG83A0_0"),
            "Tasty Burger Westside": Location(client_id=c_restaurant.id, name="Tasty Burger - Westside", address="456 West Blvd, Westside", google_place_id="ChIJN1t_tDeuEmsRUsoyG83A0_1"),
            "Grand Palace Resort": Location(client_id=c_hotel.id, name="Grand Palace Resort", address="777 Beachside Dr, Resort Area", google_place_id="ChIJN1t_tDeuEmsRUsoyG83A0_2"),
            "Grand Palace Express": Location(client_id=c_hotel.id, name="Grand Palace Express", address="12 Airport Way, Transit Hub", google_place_id="ChIJN1t_tDeuEmsRUsoyG83A0_3"),
            "CareFirst Heights": Location(client_id=c_clinic.id, name="CareFirst Clinic - Medical Heights", address="500 Doctor Row, Heights", google_place_id="ChIJN1t_tDeuEmsRUsoyG83A0_4"),
            "CareFirst CareCenter": Location(client_id=c_clinic.id, name="CareFirst Emergency Center", address="911 Rescue Rd, Suburbia", google_place_id="ChIJN1t_tDeuEmsRUsoyG83A0_5"),
            "StyleHub Boutique": Location(client_id=c_retail.id, name="StyleHub Boutique - SoHo", address="22 Fashion Ave, SoHo", google_place_id="ChIJN1t_tDeuEmsRUsoyG83A0_6"),
            "StyleHub Mall": Location(client_id=c_retail.id, name="StyleHub - Galleria Mall", address="9000 Galleria Pkwy, Mall Level 2", google_place_id="ChIJN1t_tDeuEmsRUsoyG83A0_7")
        }
        
        for loc in locations.values():
            session.add(loc)
        session.flush()
        
        # 7. Create Users for role verification
        users = [
            User(email="admin@reputationos.ai", hashed_password=hash_password("demo1234"), name="Super Admin User", role="super_admin"),
            User(email="agency@stellar.digital", hashed_password=hash_password("demo1234"), name="Stellar Admin", role="agency_admin", agency_id=agency1.id),
            User(email="manager@tastyburger.com", hashed_password=hash_password("demo1234"), name="Tasty Burger Manager", role="client_admin", agency_id=agency1.id, client_id=c_restaurant.id),
            User(email="support@tastyburger.com", hashed_password=hash_password("demo1234"), name="Support Staff", role="customer_support", agency_id=agency1.id, client_id=c_restaurant.id, location_id=locations["Tasty Burger Downtown"].id),
            User(email="staff@tastyburger.com", hashed_password=hash_password("demo1234"), name="Staff ReadOnly", role="read_only", agency_id=agency1.id, client_id=c_restaurant.id),
            
            # Additional managers for hotel/medical/retail
            User(email="manager@grandpalace.com", hashed_password=hash_password("demo1234"), name="Hotel GM", role="client_admin", agency_id=agency1.id, client_id=c_hotel.id),
            User(email="doctor@carefirst.com", hashed_password=hash_password("demo1234"), name="Chief Doctor", role="client_admin", agency_id=agency1.id, client_id=c_clinic.id),
            User(email="retail@stylehub.com", hashed_password=hash_password("demo1234"), name="Retail Ops Manager", role="client_admin", agency_id=agency1.id, client_id=c_retail.id)
        ]
        for u in users:
            session.add(u)
        session.flush()
        
        # 8. Create default Smart Rules
        for loc in locations.values():
            rules = [
                SmartRule(location_id=loc.id, min_rating=5, max_rating=5, action="auto_reply"),
                SmartRule(location_id=loc.id, min_rating=4, max_rating=4, action="auto_reply"),
                SmartRule(location_id=loc.id, min_rating=3, max_rating=3, action="approval_required"),
                SmartRule(location_id=loc.id, min_rating=2, max_rating=2, action="escalate"),
                SmartRule(location_id=loc.id, min_rating=1, max_rating=1, action="never_auto"),
            ]
            session.add_all(rules)
            
        # 9. Create 200+ Reviews spanning last 90 days
        logger.info("Generating 200+ reviews, sentiment, topics, and replies...")
        review_count = 0
        review_date_start = datetime.utcnow() - timedelta(days=90)
        
        # We will loop through locations and generate reviews programmatically
        for loc_name, loc in locations.items():
            # Determine industry based on client association
            if loc.client_id == c_restaurant.id:
                ind = "Restaurant"
            elif loc.client_id == c_hotel.id:
                ind = "Hospitality"
            elif loc.client_id == c_clinic.id:
                ind = "Medical"
            else:
                ind = "Retail"
                
            # Generate 25 reviews per location (8 * 25 = 200 reviews total)
            for j in range(26):
                review_count += 1
                
                # Alternate ratings to build a nice distribution (Average ~ 4.1 stars)
                rating = random.choice([5, 5, 5, 4, 4, 3, 2, 1])
                
                # Match sentiment based on rating
                if rating >= 4:
                    sentiment = "positive"
                elif rating == 3:
                    sentiment = "neutral" if random.random() > 0.5 else "mixed"
                else:
                    sentiment = "negative"
                    
                # Select template
                template_list = TEMPLATES[ind]["positive" if sentiment == "positive" else ("negative" if sentiment == "negative" else "neutral")]
                review_text = random.choice(template_list)
                
                # Add slight text variation
                review_text += " " + random.choice(["Highly recommend!", "Would go again.", "Overall fine.", "Be cautious.", "Needs improvement."])
                
                # Pick author
                author_name, author_img = random.choice(AUTHORS)
                author_name = f"{author_name} {random.randint(1, 99)}" # avoid unique constraints if any or duplicates
                
                # Spread reviews over the last 90 days
                review_date = review_date_start + timedelta(
                    days=random.randint(0, 89), 
                    hours=random.randint(0, 23), 
                    minutes=random.randint(0, 59)
                )
                
                # Add review
                review = Review(
                    location_id=loc.id,
                    source="google",
                    source_review_id=f"google_rev_{loc.id}_{review_count}",
                    author_name=author_name,
                    author_image_url=author_img,
                    rating=rating,
                    text=review_text,
                    review_date=review_date
                )
                session.add(review)
                session.flush() # Yield review.id
                
                # Add sentiment result
                sent_result = SentimentResult(
                    review_id=review.id,
                    sentiment=sentiment,
                    confidence=round(random.uniform(0.75, 0.99), 2),
                    emotions=EMOTIONS[rating]
                )
                session.add(sent_result)
                
                # Add topic results
                topics = get_topics_for_review(ind, rating, sentiment)
                for topic in topics:
                    top_res = TopicResult(
                        review_id=review.id,
                        topic=topic["topic"],
                        sub_topic=topic["sub_topic"],
                        sentiment=topic["sentiment"]
                    )
                    session.add(top_res)
                    
                # Generate mock replies for approximately 70% of positive reviews, 
                # and leave others in draft/unreplied for dashboard demonstration.
                if rating >= 4 and random.random() < 0.7:
                    # Posted reply
                    reply = ReviewReply(
                        review_id=review.id,
                        content=f"Thank you for the review, {author_name}! We appreciate you sharing your experience at {loc.name}.",
                        status="posted",
                        generated_by="ai",
                        approved_by=users[2].id
                    )
                    session.add(reply)
                elif rating == 3 and random.random() < 0.5:
                    # Draft options waiting for manager
                    reply_opt1 = ReviewReply(
                        review_id=review.id,
                        content=f"Dear {author_name}, Thank you for your review. We are happy your experience was satisfactory and will take your feedback to improve.",
                        status="draft",
                        generated_by="ai"
                    )
                    reply_opt2 = ReviewReply(
                        review_id=review.id,
                        content=f"Hi {author_name}, thanks for the rating! We're constantly working on improving our speed and hope to get a 5-star next time.",
                        status="draft",
                        generated_by="ai"
                    )
                    session.add_all([reply_opt1, reply_opt2])
                    
        # 10. Generate 90 Days of Reputation Scores per location for history chart
        logger.info("Computing 90-day daily reputation scores snapshots...")
        for loc in locations.values():
            for d_idx in range(90):
                score_date = (date.today() - timedelta(days=d_idx))
                
                # Daily variations to show nice graph trend lines
                variation = random.uniform(-4, 4)
                base_score = 76.0
                if "Downtown" in loc.name:
                    base_score = 82.0
                elif "Resort" in loc.name:
                    base_score = 89.0
                elif "Heights" in loc.name:
                    base_score = 80.0
                    
                overall_score = max(0.0, min(100.0, base_score + variation))
                
                # Mock elements
                score = ReputationScore(
                    location_id=loc.id,
                    score_date=score_date,
                    overall_score=round(overall_score, 1),
                    avg_rating=round(random.uniform(4.0, 4.7), 2),
                    review_volume=random.randint(15, 60),
                    sentiment_score=round(random.uniform(0.70, 0.95), 2),
                    response_rate=round(random.uniform(0.70, 0.99), 2),
                    components={
                        "rating_score": round(overall_score * 0.4, 1),
                        "sentiment_score": round(overall_score * 0.3, 1),
                        "response_score": round(overall_score * 0.3, 1)
                    }
                )
                session.add(score)

        session.commit()
        logger.info(f"Database successfully seeded! Created {review_count} reviews and completed configurations.")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
