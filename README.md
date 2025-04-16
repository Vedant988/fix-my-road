# FixMyRoad

A Flask-based web application that bridges the gap between citizens and government authorities to address India's road infrastructure problems, particularly potholes and related hazards.

## Problem Statement

Across India, poor road infrastructure—from potholes to broken pavements and incomplete repairs—continues to be a major civic challenge. Every monsoon season, the problem escalates, leading to traffic chaos, public frustration, and more tragically, thousands of avoidable accidents.

Official data reports over 11,000 road accidents annually caused by potholes and related road hazards. These aren't just cracks in concrete—they're cracks in the system.

At the heart of the issue lies a breakdown in coordination. Civil departments often operate in silos. Communication between the public, government agencies, and elected representatives is fragmented. Complaints are either delayed, dismissed, or lost in red tape.

## Solution Overview

FixMyRoad creates a transparent ecosystem connecting citizens with civic authorities through:

- **ML-Verified Complaint Submission**: Image analysis confirms genuine road issues
- **Geographic Visualization**: Map-based interface shows problem density
- **Intelligent Prioritization**: Algorithm weighs multiple factors to highlight urgent issues
- **Community Engagement**: Social features allow public oversight of reported problems
- **End-to-End Tracking**: Complete visibility from submission to resolution

## Project Structure

```
FIXMYROAD/
│
├── models/                # Machine learning models
│
├── static/
│   ├── css/              # CSS stylesheets
│   ├── images/           # Image assets
│   ├── js/               # JavaScript files
│   ├── scss/             # SCSS source files
│   ├── vendor/           # Third-party libraries
│   └── style.css         # Main stylesheet
│
├── templates/
│   ├── admin_home.html           # Admin dashboard
│   ├── admin_resolved.html       # Admin resolved complaints view
│   ├── file_complaint.html       # Complaint submission form
│   ├── hom.html                  # Alternative homepage
│   ├── home.html                 # Main homepage
│   ├── login.html                # User login page
│   ├── piyush.html               # Developer page
│   ├── predict_bridge.html       # Bridge prediction tool
│   ├── register.html             # User registration page
│   ├── Report.html               # Reports interface
│   ├── view_complaints.html      # Community complaints feed
│   ├── view_on_map.html          # Map visualization interface
│   └── your_complaint_status.html # User complaint tracking page
│
├── .gitattributes        # Git attributes file
├── app.py                # Main Flask application
├── README.md             # Project documentation
└── requirements.txt      # Package dependencies
```

## Features

### 1. Complaint Management System
- Image-based pothole reporting with ML verification
- Geolocation tagging and mapping
- Detailed complaint tracking from submission to resolution

### 2. Geographic Visualization
- Interactive map using Leaflet to display reported issues
- Heatmap view of problem density across regions
- Location-based filtering and navigation

### 3. Community Feed
- Public visibility of verified complaints
- Social engagement through upvoting/downvoting
- Comment functionality for additional information sharing

### 4. User Dashboard
- Personalized view of active and resolved complaints
- Status tracking and notifications
- Historical record of user contributions

### 5. Bridge Prediction Tool
- XGBoost regression model for bridge life expectancy prediction
- Preventative maintenance recommendations
- Engineering parameters analysis

### 6. Administrative Interface
- Complaint verification workflow
- Resolution tracking and management
- Performance analytics and reporting

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript
- **Map Visualization**: Leaflet.js
- **Machine Learning**: Roboflow (for image analysis), XGBoost (for prediction)

## Installation and Setup

### Prerequisites
- Python 3.8+
- MongoDB
- Git

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/fixmyroad.git
cd fixmyroad

# Create and activate virtual environment
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt


# Run the application
python app.py
```

The application will be available at `http://localhost:5000`.

## Usage

1. **Register/Login**: Create an account or log in to access the system
2. **Report Issues**: Submit road problem reports with photos and location
3. **Track Progress**: Follow the status of your reports through the resolution process
4. **Community Engagement**: View and interact with other reported issues
5. **Bridge Prediction**: Use the prediction tool for infrastructure planning

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments
- This project was created to address the critical infrastructure challenges in India
- Thanks to Team (Yash Saini, Piyush Gupta, Anuj Soni)
