# crispy-garbanzo-tracker
A small and simple email open tracker that generates tracking pixels for email campaigns.

## Features
- Generate unique tracking pixels for emails
- Track email opens with timestamp and IP information
- MongoDB integration for data storage
- Docker support for easy deployment
- Environment-based configuration

## Prerequisites
- Python 3.8+
- MongoDB
- Docker (optional)

## Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/crispy-garbanzo-tracker.git
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up MongoDB locally or use a remote instance

4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update MongoDB connection details

5. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000` with endpoints:
- POST `/track-email/`: Track email opens
- GET `/`: Welcome message




