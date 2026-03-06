"""
VisionDX — WhatsApp Delivery Service (Twilio)

Sends blood test reports to patients via WhatsApp using the Twilio API.
Gracefully skips delivery if credentials are not configured.
"""
from __future__ import annotations

from pathlib import Path

from loguru import logger

from visiondx.config import settings


class WhatsAppService:
    """Send WhatsApp messages via Twilio."""

    def __init__(self) -> None:
        self._configured = bool(
            settings.twilio_account_sid
            and settings.twilio_auth_token
            and settings.twilio_account_sid != "your_twilio_account_sid"
        )
        if not self._configured:
            logger.warning(
                "WhatsApp service not configured — set TWILIO_ACCOUNT_SID and "
                "TWILIO_AUTH_TOKEN in .env to enable delivery"
            )

    def send_report_notification(
        self,
        patient_phone: str,
        patient_name: str,
        report_id: str,
        message_body: str,
        pdf_path: str | None = None,
    ) -> bool:
        """
        Send WhatsApp notification to the patient.

        Args:
            patient_phone: Patient's phone number in E.164 format (e.g., +919876543210)
            patient_name:  Patient's name
            report_id:     Report ID for reference
            message_body:  Pre-formatted message text
            pdf_path:      Optional local path to PDF (for media attachment)

        Returns:
            True if sent successfully, False otherwise.
        """
        if not self._configured:
            logger.info(
                f"[WhatsApp STUB] Would send to {patient_phone}: "
                f"Report {report_id} for {patient_name}"
            )
            return False

        try:
            from twilio.rest import Client

            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            to_number = f"whatsapp:{patient_phone}"

            message = client.messages.create(
                from_=settings.twilio_whatsapp_from,
                to=to_number,
                body=message_body,
            )

            logger.success(
                f"WhatsApp sent to {patient_phone}, SID: {message.sid}"
            )
            return True

        except Exception as e:
            logger.error(f"WhatsApp delivery failed for {patient_phone}: {e}")
            return False

    def send_doctor_access_link(
        self,
        doctor_phone: str,
        report_id: str,
        base_url: str,
    ) -> bool:
        """Send doctor a direct link to access the report."""
        link = f"{base_url}/doctor/report/{report_id}"
        body = (
            f"🏥 *VisionDX* — New Patient Report\n\n"
            f"Report ID: `{report_id}`\n"
            f"Access Report: {link}\n\n"
            f"_This report has been automatically processed by VisionDX AI._"
        )
        return self.send_report_notification(
            patient_phone=doctor_phone,
            patient_name="Doctor",
            report_id=report_id,
            message_body=body,
        )
