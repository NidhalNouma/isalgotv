
from profile_user.models import Notification

def send_notification(_from, _to, message, url):
    Notification.objects.create(user = _to, message="reply on your result")