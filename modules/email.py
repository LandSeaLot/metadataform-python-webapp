from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP
from html import escape
from config import *
import logging


logger = logging.getLogger("landsealot_form")


def send_email(upload_results, warning=None):
    subject = "LANDSEALOT Zenodo uploader notification"

    try:
        email_addr_from = EMAIL_CREDENTIALS["email"]
        smtp_server = EMAIL_CREDENTIALS["smtp_server"]
        smtp_port = EMAIL_CREDENTIALS.get("smtp_port", 587)
        password = EMAIL_CREDENTIALS["password"]

        if not EMAIL_RECIPIENTS:
            logger.warning("No email recipients configured")
            return

        successful_uploads = [
            r for r in upload_results
            if r["success"]
        ]

        failed_uploads = [
            r for r in upload_results
            if not r["success"]
        ]

        success_rows = ""
        for r in successful_uploads:
            rec_id = r["response"].get("id", "-")

            record_url = (
                r["response"]
                .get("links", {})
                .get("html", "")
            )
            record_link = (
                f'<a href="{escape(record_url)}">Open record</a>'
                if record_url
                else "-"
            )

            success_rows += f"""
            <tr>
                <td>{escape(str(r['sensor_id']))}</td>
                <td>{rec_id}</td>
                <td>{record_link}</td>
            </tr>
            """

        failed_rows = ""
        for r in failed_uploads:
            error = r["response"].get("error", "Unknown error")

            failed_rows += f"""
            <tr>
                <td>{escape(str(r['sensor_id']))}</td>
                <td>{escape(str(error))}</td>
            </tr>
            """

        warning_block = ""

        if warning:
            warning_block = f"""
            <div style="
                border:1px solid #f0ad4e;
                background-color:#fcf8e3;
                padding:10px;
                margin-bottom:20px;
            ">
                <h3>Warning</h3>
                <p>{escape(str(warning))}</p>
            </div>
            """

        html = f"""
        <html>
        <body>
            <h2>LANDSEALOT Zenodo Upload Report</h2>

            {warning_block}

            <p>
                Successful uploads: {len(successful_uploads)}<br>
                Failed uploads: {len(failed_uploads)}
            </p>

            {"<h3>Successful uploads</h3>" if success_rows else ""}
            {
                f'''
                <table border="1" cellpadding="5" cellspacing="0">
                    <tr>
                        <th>Sensor ID</th>
                        <th>Zenodo Record ID</th>
                    </tr>
                    {success_rows}
                </table>
                '''
                if success_rows else ""
            }

            {"<h3>Failed uploads</h3>" if failed_rows else ""}
            {
                f'''
                <table border="1" cellpadding="5" cellspacing="0">
                    <tr>
                        <th>Sensor ID</th>
                        <th>Error</th>
                    </tr>
                    {failed_rows}
                </table>
                '''
                if failed_rows else ""
            }

        </body>
        </html>
        """

        successful = []
        failed = []

        for email_addr_to in EMAIL_RECIPIENTS:

            try:
                with SMTP(smtp_server, smtp_port, timeout=10) as server:

                    server.starttls()
                    server.login(email_addr_from, password)

                    msg = MIMEMultipart("alternative")
                    msg["From"] = email_addr_from
                    msg["To"] = email_addr_to
                    msg["Subject"] = subject

                    msg.attach(
                        MIMEText(html, "html", "utf-8")
                    )

                    server.sendmail(
                        email_addr_from,
                        email_addr_to,
                        msg.as_bytes(),
                    )

                successful.append(email_addr_to)

            except Exception as e:
                logger.error(
                    f"Error sending email to {email_addr_to}: {e}"
                )
                failed.append(email_addr_to)

        logger.info(
            f"Upload report sent to {len(successful)} recipients"
        )

        if failed:
            logger.warning(
                f"Failed recipients: {', '.join(failed)}"
            )

    except Exception as e:
        logger.error(f"Error sending email: {e}")