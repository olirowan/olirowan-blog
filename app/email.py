import sendgrid
from flask import render_template
from app import app
from sendgrid.helpers.mail import Content, Email, Mail

sg = sendgrid.SendGridAPIClient(app.config['SENDGRID_API_KEY'])


def send_password_reset_email(user):

    token = user.get_reset_password_token()

    subject = "[olirowanxyz] Reset Your Password"

    from_email = Email(
        app.config['ADMINS'][0]
    )
    to_email = Email(
        [user.email][0]
    )

    html_body = render_template(
        'email/reset_password.html',
        user=user,
        token=token
    )

    content = Content("text/html", html_body)
    mail = Mail(from_email, subject, to_email, content)

    response = sg.client.mail.send.post(request_body=mail.get())

    app.logger.info("Password Reset Requested by: " + user.email)
    app.logger.info("Response Status: " + str(response.status_code))
