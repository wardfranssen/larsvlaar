# from email.mime.multipart import MIMEMultipart
# from email.mime.image import MIMEImage
# import main
# import smtplib
# import random
#
# emails = main.config["EMAILS"]
# smtp_connections = {}
#
# for email_data in emails:
#     email_address = email_data["EMAIL_ADDRESS"]
#     password = email_data["PASSWORD"]
#
#     smtp_connections[email_address] = smtplib.SMTP_SSL('smtp.gmail.com', 465)
#     smtp_connections[email_address].login(email_address, password)
#
#
# # Pre-load equation image
# with open('../../static/snake/images/lars_is_dik.png', 'rb') as img:
#     img_data = img.read()
#     lars_is_dik_img = MIMEImage(img_data, name='lars.png')
#     # equation_image.add_header('Content-ID', '<formula_image>')
#
#
# receiver = "118765@minkemacollege.nl"
# subject = "larsvlaar.nl"
# content = ""
#
#
# # MIME Message Setup
# mime_message = MIMEMultipart()
# mime_message['From'] = "Wax Flame🔥"
# mime_message['To'] = random.choice(main.boodschappen_lijstje).replace(" ", "_")
# mime_message['Subject'] = subject
#
# mime_message.attach(lars_is_dik_img)
#
# for i in range(1000):
#     # Send Email
#     sender_email = random.choice(list(smtp_connections.keys()))
#     smtp_connection = smtp_connections[sender_email]
#
#     try:
#         smtp_connection.sendmail("Wax Flame🔥", receiver, mime_message.as_string())
#     except smtplib.SMTPSenderRefused:
#         for email_data in emails:
#             if email_data["EMAIL_ADDRESS"] == sender_email:
#                 smtp_connections[sender_email] = smtplib.SMTP_SSL('smtp.gmail.com', 465)
#                 smtp_connections[sender_email].login(sender_email, email_data["PASSWORD"])
#
#         smtp_connection.sendmail("Wax Flame🔥", receiver, mime_message.as_string())
#
#     print(f"Send email to: {receiver}")

import main

print(main.redis_client.hget(f"larsvlaar-games-one_vs_one", None))
