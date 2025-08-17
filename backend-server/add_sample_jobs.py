#!/usr/bin/env python3
"""Add sample job data to the database for testing"""

import sys
import os
import uuid
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def add_sample_jobs():
    """Add sample job data to the database"""
    try:
        from app.core.database import get_database
        from app.models.job import Job
        
        db = next(get_database())
        
        # Sample job data
        sample_jobs = [
            {
                "title": "Senior Software Engineer",
                "company": "TechCorp Inc",
                "location": "San Francisco, CA",
                "remote_type": "hybrid",
                "description": "We are looking for a Senior Software Engineer to join our team. You will work on cutting-edge web applications using Python, React, and cloud technologies.",
                "requirements": ["Python", "React", "AWS", "5+ years experience"],
                "qualifications": ["Bachelor's degree in Computer Science", "Experience with microservices", "Strong problem-solving skills"],
                "salary_min": 120000,
                "salary_max": 180000,
                "salary_currency": "USD",
                "employment_type": "full-time",
                "experience_level": "senior",
                "industry": "Technology",
                "source": "sample_data",
                "external_id": "tech_001"
            },
            {
                "title": "Frontend Developer",
                "company": "StartupXYZ",
                "location": "Remote",
                "remote_type": "remote",
                "description": "Join our fast-growing startup as a Frontend Developer. Work with modern JavaScript frameworks and create amazing user experiences.",
                "requirements": ["JavaScript", "React", "CSS", "HTML", "3+ years experience"],
                "qualifications": ["Experience with modern frontend frameworks", "Knowledge of responsive design", "Git proficiency"],
                "salary_min": 80000,
                "salary_max": 120000,
                "salary_currency": "USD",
                "employment_type": "full-time",
                "experience_level": "mid",
                "industry": "Technology",
                "source": "sample_data",
                "external_id": "startup_001"
            },
            {
                "title": "Data Scientist",
                "company": "DataCorp Analytics",
                "location": "New York, NY",
                "remote_type": "onsite",
                "description": "We're seeking a Data Scientist to analyze large datasets and build machine learning models to drive business insights.",
                "requirements": ["Python", "Machine Learning", "SQL", "Statistics", "4+ years experience"],
                "qualifications": ["PhD or Master's in Data Science/Statistics", "Experience with TensorFlow/PyTorch", "Strong analytical skills"],
                "salary_min": 100000,
                "salary_max": 150000,
                "salary_currency": "USD",
                "employment_type": "full-time",
                "experience_level": "senior",
                "industry": "Technology",
                "source": "sample_data",
                "external_id": "data_001"
            },
            {
                "title": "DevOps Engineer",
                "company": "CloudTech Solutions",
                "location": "Austin, TX",
                "remote_type": "hybrid",
                "description": "Looking for a DevOps Engineer to manage our cloud infrastructure and CI/CD pipelines.",
                "requirements": ["AWS", "Docker", "Kubernetes", "CI/CD", "3+ years experience"],
                "qualifications": ["Experience with cloud platforms", "Infrastructure as Code", "Monitoring and logging"],
                "salary_min": 90000,
                "salary_max": 140000,
                "salary_currency": "USD",
                "employment_type": "full-time",
                "experience_level": "mid",
                "industry": "Technology",
                "source": "sample_data",
                "external_id": "devops_001"
            },
            {
                "title": "Product Manager",
                "company": "InnovateCorp",
                "location": "Seattle, WA",
                "remote_type": "hybrid",
                "description": "We need a Product Manager to lead product strategy and work with cross-functional teams to deliver innovative solutions.",
                "requirements": ["Product Management", "Agile", "Analytics", "5+ years experience"],
                "qualifications": ["MBA or equivalent experience", "Experience with product analytics", "Strong communication skills"],
                "salary_min": 110000,
                "salary_max": 160000,
                "salary_currency": "USD",
                "employment_type": "full-time",
                "experience_level": "senior",
                "industry": "Technology",
                "source": "sample_data",
                "external_id": "pm_001"
            },
            {
                "title": "Junior Web Developer",
                "company": "WebDev Studio",
                "location": "Remote",
                "remote_type": "remote",
                "description": "Great opportunity for a Junior Web Developer to learn and grow with our team. Work on diverse web projects.",
                "requirements": ["HTML", "CSS", "JavaScript", "1+ years experience"],
                "qualifications": ["Portfolio of web projects", "Basic understanding of responsive design", "Eagerness to learn"],
                "salary_min": 50000,
                "salary_max": 70000,
                "salary_currency": "USD",
                "employment_type": "full-time",
                "experience_level": "entry",
                "industry": "Technology",
                "source": "sample_data",
                "external_id": "junior_001"
            }
        ]
        
        jobs_added = 0
        
        for job_data in sample_jobs:
            # Check if job already exists
            existing_job = db.query(Job).filter(
                Job.external_id == job_data["external_id"],
                Job.source == job_data["source"]
            ).first()
            
            if not existing_job:
                job = Job(
                    job_id=str(uuid.uuid4()),
                    posted_date=datetime.utcnow() - timedelta(days=1),
                    scraped_at=datetime.utcnow(),
                    is_active=True,
                    **job_data
                )
                
                db.add(job)
                jobs_added += 1
        
        db.commit()
        
        print(f"✅ Added {jobs_added} sample jobs to the database")
        print(f"Total jobs in database: {db.query(Job).count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding sample jobs: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Adding sample job data...")
    success = add_sample_jobs()
    
    if success:
        print("\n🎉 Sample jobs added successfully!")
        print("Now the job discovery system has data to work with.")
    else:
        print("\n💥 Failed to add sample jobs")