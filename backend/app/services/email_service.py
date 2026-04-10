import logging

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    """Send email - logs to console for demo purposes."""
    logger.info(f"[EMAIL] To: {to} | Subject: {subject}")
    logger.info(f"[EMAIL] Body: {body}")
    return True


def send_appointment_confirmation(to: str, doctor_name: str, date_time: str) -> bool:
    subject = "Confirmare Programare"
    body = (
        f"Programarea dumneavoastră cu Dr. {doctor_name} "
        f"pe data de {date_time} a fost confirmată."
    )
    return send_email(to, subject, body)


def send_appointment_reminder(to: str, doctor_name: str, date_time: str) -> bool:
    subject = "Reminder Programare"
    body = (
        f"Vă reamintim că aveți o programare cu Dr. {doctor_name} "
        f"pe data de {date_time}."
    )
    return send_email(to, subject, body)


def send_welcome_email(to: str, name: str, role: str) -> bool:
    subject = "Bine ați venit!"
    body = f"Bună ziua {name}, contul dumneavoastră de {role} a fost creat cu succes."
    return send_email(to, subject, body)
