import firebase_admin
from firebase_admin import credentials, messaging
from app.core.settings import get_settings

settings = get_settings()

# Firebase'ni sozlash
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": settings.FIREBASE_TYPE,
        "project_id": settings.FIREBASE_PROJECT_ID,
        "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
        "private_key": settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
        "client_email": settings.FIREBASE_CLIENT_EMAIL,
        "client_id": settings.FIREBASE_CLIENT_ID,
        "auth_uri": settings.FIREBASE_AUTH_URI,
        "token_uri": settings.FIREBASE_TOKEN_URI,
        "auth_provider_x509_cert_url": settings.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
        "client_x509_cert_url": settings.FIREBASE_CLIENT_X509_CERT_URL,
        "universe_domain": settings.FIREBASE_UNIVERSE_DOMAIN
    })
    firebase_admin.initialize_app(cred)

# Push notification yuborish
def send_push_notification(
    registration_token: str, title: str, body: str, image: str = ""
):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body, image=image),
        token=registration_token,
    )
    return messaging.send(message)

# Topic'ga notification yuborish
def send_push_notification_to_topic(topic: str, title: str, body: str, image: str = ""):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body, image=image),
        topic=topic,
    )
    return messaging.send(message)
