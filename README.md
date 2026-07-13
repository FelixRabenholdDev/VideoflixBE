# Videoflix Backend

Videoflix is a Netflix-inspired video streaming platform. This repository contains the **backend**, built with Django and Django REST Framework. The backend exposes a REST API for user authentication (email-based, with email verification), password reset, and video streaming via HLS (HTTP Live Streaming).

The frontend is developed separately and communicates with this backend exclusively through the REST API.

## Tech Stack

- **Python 3.12** / **Django 6.0**
- **Django REST Framework** – REST API
- **PostgreSQL** – primary database
- **Redis** – caching layer and message broker for background jobs
- **Django RQ** – background task processing (e.g. sending emails, video conversion)
- **djangorestframework-simplejwt** – JWT authentication via HttpOnly cookies
- **FFmpeg** – video transcoding into HLS format (multiple resolutions)
- **Pillow** – image handling (thumbnails)
- **Docker & Docker Compose** – containerized development and deployment
- **Gunicorn** – WSGI application server
- **Whitenoise** – static file serving

## Project Structure

```
Videoflix/
├── manage.py
├── requirements.txt
├── backend.Dockerfile
├── backend.entrypoint.sh
├── docker-compose.yml
├── .env
│
├── core/                      # Django project settings package
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── auth_app/                  # User accounts, authentication, email verification
│   ├── models.py               # CustomUser (email-based)
│   ├── managers.py
│   ├── utils.py                 # Token generation, email rendering, cookie handling
│   ├── jobs.py                  # RQ jobs (activation email, password reset email)
│   ├── authentication.py        # Cookie-based JWT authentication
│   ├── static/emails/           # Logo used in email templates
│   ├── templates/emails/        # HTML email templates
│   └── api/
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
│
├── video_app/                 # Video catalog and HLS streaming
│   ├── models.py                # Video model
│   ├── utils.py                 # HLS path helpers
│   ├── jobs.py                  # RQ job: FFmpeg conversion to HLS
│   ├── signals.py               # Triggers conversion on upload
│   └── api/
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
│
├── static/
└── media/
```

## Getting Started

This project is designed to run entirely via Docker. All dependencies (PostgreSQL, Redis, FFmpeg) are already configured in the provided Docker setup.

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose installed

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Videoflix
   ```

2. **Create your `.env` file**

   Copy the provided `.env.template` to `.env` and fill in your own values:
   ```bash
   cp .env.template .env
   ```

   | Variable | Description |
   |---|---|
   | `SECRET_KEY` | Django secret key |
   | `DEBUG` | `True` for development, `False` for production |
   | `ALLOWED_HOSTS` | Comma-separated list of allowed hosts |
   | `CSRF_TRUSTED_ORIGINS` | Comma-separated list of trusted frontend origins |
   | `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection |
   | `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_LOCATION` | Redis connection (used for caching and RQ) |
   | `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `DEFAULT_FROM_EMAIL` | SMTP configuration for sending emails |
   | `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` | Auto-created superuser on first start |

   For local development, an [SMTP testing service](https://mailtrap.io) is recommended for the email settings so no real emails are sent to real inboxes.

3. **Build and start the containers**
   ```bash
   docker compose up --build
   ```

   This starts three services:
   - `db` – PostgreSQL database
   - `redis` – Redis cache and message broker
   - `web` – Django application (migrations, static files, and superuser creation run automatically on startup; an RQ worker runs alongside the web server)

4. **The API is now available at**
   ```
   http://localhost:8000/api/
   ```

### Everyday Development

Once the images have been built, you don't need `--build` again unless `requirements.txt`, the `Dockerfile`, or the entrypoint script change:

```bash
docker compose up
```

Run management commands inside the running container, e.g.:
```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

## Authentication

Authentication uses **JWT tokens delivered as HttpOnly cookies** (`access_token` and `refresh_token`), not via the `Authorization` header. This keeps tokens inaccessible to client-side JavaScript, reducing XSS risk.

- Access tokens are short-lived; refresh tokens are used to obtain new access tokens via `/api/token/refresh/`.
- On logout, the refresh token is blacklisted so it can no longer be used.
- All error messages related to authentication (invalid credentials, inactive account, non-existent email) are intentionally generic to prevent account enumeration.

## API Endpoints

### Authentication & Account Management

| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| POST | `/api/register/` | Register a new user; sends an activation email | No |
| GET | `/api/activate/<uidb64>/<token>/` | Activate a user account | No |
| POST | `/api/login/` | Authenticate and receive JWT cookies | No |
| POST | `/api/logout/` | Blacklist the refresh token and clear cookies | Refresh token cookie |
| POST | `/api/token/refresh/` | Issue a new access token | Refresh token cookie |
| POST | `/api/password_reset/` | Request a password reset email | No |
| POST | `/api/password_confirm/<uidb64>/<token>/` | Set a new password | No |

### Video

| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| GET | `/api/video/` | List all available videos | JWT |
| GET | `/api/video/<movie_id>/<resolution>/index.m3u8` | HLS master playlist for a given resolution | JWT |
| GET | `/api/video/<movie_id>/<resolution>/<segment>/` | Individual HLS video segment (`.ts`) | JWT |

Supported resolutions: `480p`, `720p`, `1080p`.

## Video Processing (HLS)

When a new `Video` object is created (e.g. via the Django admin), a background job is automatically queued that converts the uploaded video file into multiple HLS resolutions using FFmpeg. Converted files are stored under:

```
media/hls/<video_id>/<resolution>/index.m3u8
media/hls/<video_id>/<resolution>/segment_XXX.ts
```

## Background Jobs (Django RQ)

The following tasks run asynchronously via Django RQ, backed by Redis:

- Sending the account activation email
- Sending the password reset email
- Converting uploaded videos to HLS format

A worker process is started automatically alongside the web server in the Docker setup.

## Running Tests

```bash
docker compose exec web python manage.py test
```

## License

This project is part of a training curriculum. The frontend is provided separately by the Developer Akademie and must not be redistributed outside its intended course context.
