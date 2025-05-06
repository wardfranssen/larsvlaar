from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import src.snake.main as main
import src.snake.app as app
import random
import smtplib

config = main.config
titles = [
    "Bewaker van Lars' digitale heiligdom",
    "Lars' daddy",
    "Grondlegger van Lars' online bekendheid",
    "Aanbidder van Lars",
    "Het meesterbrein achter larsvlaar.nl",
    "Bijnaam: Ward Franssen",
    "Lars' geselecteerde erfgenaam (hij weet het nog niet)",
    "Officieel testpersoon voor Lars' overgebleven eten (ik hoef niks te doen)",
    "Verlosser van zij die nog niet weten wie Lars is",
    "Just a chill guy"
]

emails = config["EMAILS"]
smtp_connections = {}
for i, email_address in enumerate(emails):
    password = emails[email_address]

    smtp_connections[email_address] = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
    smtp_connections[email_address].login(email_address, password)

    break


def get_smtp_connection(email: str, password: str):
    """Get or create an SMTP connection for the given email."""
    if email in smtp_connections:
        for i in range(10):
            print(f"Try: {i}")
            try:
                # Check if the connection is still alive
                smtp_connections[email].noop()
                return smtp_connections[email]
            except smtplib.SMTPServerDisconnected as e:
                print("smtplib.SMTPServerDisconnected: ", str(e))
                # If the connection is dead, close it and create a new one
                smtp_connections[email].close()

                # Create a new SMTP connection
                smtp_connections[email] = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
                smtp_connections[email].login(email, password)
    return smtp_connections[email]


def register_verify_email(verification_code: str, username: str, receiver: str):
    subject = "Registeren: Het is zo belangrijk!"

    content = f"""\
    <!DOCTYPE html>
    <html lang="nl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Je verificatiecode</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                color: #333;
                margin: 0;
                padding: 0;
            }}
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                text-align: center;
                font-size: 24px;
                color: #444;
            }}
            p {{
                font-size: 16px;
                line-height: 1.6;
            }}
            .highlight {{
                font-weight: bold;
                color: #d9534f;
            }}
            .verification-code {{
                font-size: 20px;
                font-weight: bold;
                color: #5cb85c;
                text-align: center;
                margin: 20px 0;
            }}
            .footer {{
                font-size: 14px;
                color: #777;
                text-align: center;
                margin-top: 20px;
            }}
            .title {{
                font-size: 12px;
            }}
            .link {{
                text-align: center;
                margin: auto;
                color: #5cb85c;
                font-size: 25px
            }}
            .a {{
                text-decoration: none;
            }}
            .a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <h1>Lars heeft JOUW hulp nodig!</h1>
            
            <p>Beste {username}, ja jij daar!</p>
            
            <p>Gefeliciteerd! Je hebt een account aangemaakt op larsvlaar.nl. Maar eerst moet je je e-mailadres verifiëren, want het is zo belangrijk dat ik zeker weet dat jij de eigenaar van dit e-mailadres bent.</p>
            <p>Nu je hier toch bent kun je Lars even helpen. De laatste tijd gaat het niet goed met Lars, hij heeft recentelijk de <span class="highlight">130 kilo</span> gehaald en is daarmee officieel <span class="highlight">morbide obees</span>. Dit heeft heftige gevolgen, want hij moet al dat eten wel betalen en dat lukt niet meer. Daarom heb ik een <span class="highlight">GoFundMe</span> opgezet voor Lars:</p>
            <div class='link'><a class='a' href="https://gofundme.com/larsvlaar">Help Lars zijn boodschappen te betalen!</a></div>
            <p><strong>Doneer zodat Lars nooit meer naar de voedselbank hoeft.</strong></p>
            <p>Nu we het toch over de voedselbank hebben: de regionale omroepen houden een inzameling voor de voedselbank op <span class="highlight">vrijdag 19 december</span>. Dus schrijf je in en neem zoveel mogelijk mee en zorg dat het niet over datum is:</p>
            <div class='link'><a class='a' href="https://partiful.com/e/xI04bsrZOZ19g2ocRZtd">Schrijf je nu in!</a></div>
            <p>Als je dan eindelijk hebt gedoneerd en je hebt ingeschreven voor de inzameling, kun je je account activeren door deze code in te voeren:</p>
            <div class="verification-code"><strong>{verification_code}</strong></div>
            <p>Vergeet niet te doneren!</p>
            <p class="footer">
                Met morbide obese groet,<br>Wax Flame🔥<br>
                <span class="title">{random.choice(titles)}</span>
            </p>
        </div>
    </body>
    </html>
    """

    # MIME Message Setup
    mime_message = MIMEMultipart()
    mime_message['From'] = "Wax Flame🔥"
    mime_message['To'] = random.choice(main.boodschappen_lijstje).replace(" ", "_")
    mime_message['Subject'] = subject

    mime_message.attach(MIMEText(content, 'html'))  # Set to 'html' format

    # Send Email
    sender_email = random.choice(list(smtp_connections.keys()))
    smtp_connection = get_smtp_connection(sender_email, emails[sender_email])

    try:
        smtp_connection.sendmail("Wax Flame🔥", receiver, mime_message.as_string())
    except smtplib.SMTPServerDisconnected:
        smtp_connections[sender_email].close()
        smtp_connection = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_connection.login(sender_email, emails[sender_email])
        smtp_connections[sender_email] = smtp_connection

        smtp_connection.sendmail("Wax Flame🔥", receiver, mime_message.as_string())


def login_verification_email(verification_code: str, username:str, receiver: str):
    subject = "Login poging: We hebben een verificatiecode!"

    # HTML Email Content
    content = f"""\
    <!DOCTYPE html>
    <html lang="nl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Je verificatiecode</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                color: #333;
                margin: 0;
                padding: 0;
            }}
            .email-container {{
                margin: 20px auto;
                max-width: 600px;
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                text-align: center;
                font-size: 24px;
                color: #444;
            }}
            p {{
                font-size: 16px;
                line-height: 1.6;
            }}
            .highlight {{
                font-weight: bold;
                color: #d9534f;
            }}
            .verification-code {{
                font-size: 20px;
                font-weight: bold;
                color: #5cb85c;
                text-align: center;
                margin: 20px 0;
            }}
            .footer {{
                font-size: 14px;
                color: #777;
                text-align: center;
                margin-top: 20px;
            }}
            .title {{
                font-size: 12px;
            }}
            .link {{
                text-align: center;
                margin: auto;
                color: #5cb85c;
                font-size: 22px
            }}
            .a {{
                text-decoration: none;
            }}
            .a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <h1>Iemand probeert in te loggen op larsvlaar.nl!</h1>
            
            <p>Beste {username},</p>
            
            <p>Iemand probeert in te loggen op larsvlaar.nl, en laten we eerlijk zijn, dat is waarschijnlijk de beste beslissing die je vandaag hebt genomen.</p>
            <p>Maar voordat je weer volledig kunt opgaan in Flappy Bird en Snake, moeten we zeker weten dat jij het echt bent en niet een mysterieuze entiteit met een existentiële crisis die Lars' slang van dichtbij wil bewonderen.</p>
            <p>Wacht niet te lang, want als je deze code niet snel invoert, eet Lars je account op.</p>
            <div class="verification-code"><strong>{verification_code}</strong></div>
            <p>Mocht je de poging niet herkennen, no worries. Je kunt je rustig terugtrekken met een foto van Lars en een keukenrol voor de mentale support.</p>
            <p>Als dat niet helpt kan je altijd nog van deze playlist genieten:</p>
            <div class='link'><a class='a' href="https://www.youtube.com/playlist?list=PL10FS-k9CkGiCdqMYlVmvBmWHBbzBv2nY">Lars' favoriete playlist</a></div>
            <p>Ik zeg niet dat het altijd helpt, maar het is wel het enige wat je kunt doen. (Of stuur me een mailtje als je echt iets wilt vragen/vertellen/weten)</p>
            <p>Succes en veel plezier!</p>
            <p class="footer">
                Met dikke groet,<br>Wax Flame🔥<br>
                <span class="title">{random.choice(titles)}</span>
            </p>
        </div>
    </body>
    </html>
    """

    # MIME Message Setup
    mime_message = MIMEMultipart()
    mime_message['From'] = "Wax Flame🔥"
    mime_message['To'] = random.choice(main.boodschappen_lijstje).replace(" ", "_")
    mime_message['Subject'] = subject

    # mime_message.attach(equation_image)
    mime_message.attach(MIMEText(content, 'html'))  # Set to 'html' format

    # Send Email
    sender_email = random.choice(list(smtp_connections.keys()))
    smtp_connection = get_smtp_connection(sender_email, emails[sender_email])

    try:
        smtp_connection.sendmail("Wax Flame🔥", receiver, mime_message.as_string())
    except smtplib.SMTPServerDisconnected:
        smtp_connections[sender_email].close()
        smtp_connection = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_connection.login(sender_email, emails[sender_email])
        smtp_connections[sender_email] = smtp_connection  # Update the dict with the new connection

        smtp_connection.sendmail("Wax Flame🔥", receiver, mime_message.as_string())


def account_created(user_name: str, receiver: str):
    subject = "Account aangemaakt: De heilige wereld van Lars' Onlyfans "

    # HTML Email Content
    content = f"""\
    <!DOCTYPE html>
    <html lang="nl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welkom op larsvlaar.nl</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                color: #333;
                margin: 0;
                padding: 0;
            }}
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                text-align: center;
                font-size: 24px;
                color: #444;
            }}
            p {{
                font-size: 16px;
                line-height: 1.6;
            }}
            .highlight {{
                font-weight: bold;
                color: #d9534f;
            }}
            .footer {{
                font-size: 14px;
                color: #777;
                text-align: center;
                margin-top: 20px;
            }}
            .link {{
                text-align: center;
                margin: auto;
                color: #5cb85c;
                font-size: 25px
            }}
            .a {{
                text-decoration: none;
            }}
            .a:hover {{
                text-decoration: underline;
            }}
            .strikethrough {{
                text-decoration: line-through;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <h1>Welkom op larsvlaar.nl!</h1>
            <p>Beste {user_name},</p>
            <p>Gefeliciteerd! Je hebt nu een officieel account op <span class="highlight">larsvlaar.nl</span>, dé website waar je fantastische spelletjes en met Lars' kunt spelen.</p>
            <p>Nu je je volledig hebt toegewijd aan Lars, wil je misschien wel iets meer van hem zien. En Lars is misschien aan de zware kant, maar dat betekent alleen maar dat er meer is om van te houden. En Lars is misschien niet de slimste, maar hij is wel heel <span class="strikethrough">mooi</span> dik. Wil jij nou graag meer van Lars zien en zijn vetrolletjes tellen? Dat kan nu op zijn officiële OnlyFans:</p>
            <div class='link'><a class='a' href="https://onlyfans.com/larsvlaar">Lars' Onlyfans</a></div>
            
            <p>Op deze fabuleuze pagina laat Lars alles van hem zien (als het op de foto past).</p>
            
            <p>Nu je toch Lars aan het bewonderen bent kun je hem misschien ook even een leuk cadeautje geven. Ik heb een boodschappenlijstje samengesteld met wat dingen waarvan ik denk dat Lars ze wil/nodig heeft:</p>
            <div class='link'><a class='a' href="https://amazon.nl/hz/wishlist/ls/18TED529M91OT">Boodschappenlijstje</a></div>
            <p>Lars apprecieert elk cadeautje.</p>
            
            <p>Geniet van je tijd op OnlyFans en larsvlaar.nl, want Lars is 130 in een miljoen (kilo).</p>
            <p class="footer">
                Met seksueel getinte,<br>Wax Flame🔥<br>
                <span class="title">{random.choice(titles)}</span>
            </p>
        </div>
    </body>
    </html>
    """

    # MIME Message Setup
    mime_message = MIMEMultipart()
    mime_message['From'] = "Wax Flame🔥"
    mime_message['To'] = random.choice(main.boodschappen_lijstje).replace(" ", "_")
    mime_message['Subject'] = subject

    mime_message.attach(MIMEText(content, 'html'))  # Set to 'html' format

    # Send Email
    sender_email = random.choice(list(smtp_connections.keys()))
    smtp_connection = get_smtp_connection(sender_email, emails[sender_email])

    try:
        smtp_connection.sendmail("Wax Flame🔥", receiver, mime_message.as_string())
    except smtplib.SMTPServerDisconnected:
        smtp_connections[sender_email].close()
        smtp_connection = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_connection.login(sender_email, emails[sender_email])
        smtp_connections[sender_email] = smtp_connection

        smtp_connection.sendmail("Wax Flame🔥", receiver, mime_message.as_string())


def change_password(user_id: str, reset_token: str, username: str, receiver: str):
    subject = "Wachtwoord reset! "

    # HTML Email Content
    content = f"""\
    <!DOCTYPE html>
    <html lang="nl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Je verificatiecode</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                color: #333;
                margin: 0;
                padding: 0;
            }}
            .email-container {{
                max-width: 600px;
                margin: auto;
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                text-align: center;
                font-size: 24px;
                color: #444;
            }}
            p {{
                text-align: center;
                font-size: 16px;
                line-height: 1.6;
            }}
            .highlight {{
                font-weight: bold;
                color: #d9534f;
            }}
            .verification-code {{
                font-size: 20px;
                font-weight: bold;
                color: #5cb85c;
                text-align: center;
                margin: 20px 0;
            }}
            .footer {{
                font-size: 14px;
                color: #777;
                text-align: center;
                margin-top: 20px;
            }}
            .title {{
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <h1>larsvlaar.nl login</h1>
            <p>Joehoe {username},</p>
            <p>Zal weer eens niet, je bent je wachtwoord zeker vergeten hè? En dat moet ik dan zeker weer oplossen? Oké, voor deze ene keer.</p>
            <p>Voer deze code in en claim weer toegang tot de enige website die ertoe doet. Een plek waar je Flappy Bird en Snake kunt spelen terwijl je nadenkt over de diepe levensvragen, zoals: Wat kost hier watermeloen? Of wat het antwoord is op dit wiskundige meesterwerk:</p>
            <div class="formula"><img src="cid:formula_image"></div>

            <p>Maar wacht niet te lang! Als je deze code niet invoert kan het zijn dat Lars je account opeet.</p>
            <p>Mocht je de poging niet herkennen, no worries. Je kunt je rustig terugtrekken met groente of fruit in blik, een paar chocoladerepen en wat toiletpapier voor de mentale support. Als dat niet helpt kun je altijd nog van deze playlist genieten: https://www.youtube.com/playlist?list=PL10FS-k9CkGiCdqMYlVmvBmWHBbzBv2nY Ik zeg niet dat het altijd helpt, maar het is wel het enige wat je kunt doen.(Of stuur me een mailtje als me iets wilt vragen/vertellen)</p>

            <div class="verification-code"><strong>https://dev.larsvlaar.nl/change_password?token={reset_token}&user_id={user_id}</strong></div>
            <p>Succes en veel plezier!</p>
            <p class="footer">
                Met dikke groet,<br>Wax Flame🔥<br>
                <span class="title">{random.choice(titles)}</span>
            </p>
        </div>
    </body>
    </html>
    """

    # MIME Message Setup
    mime_message = MIMEMultipart()
    mime_message['From'] = "Wax Flame🔥"
    mime_message['To'] = random.choice(main.boodschappen_lijstje).replace(" ", "_")
    mime_message['Subject'] = subject

    mime_message.attach(MIMEText(content, 'html'))  # Set to 'html' format

    # Send Email
    sender_email = random.choice(list(smtp_connections.keys()))
    smtp_connection = get_smtp_connection(sender_email, emails[sender_email])

    try:
        smtp_connection.sendmail("Wax Flame🔥", receiver, mime_message.as_string())
    except smtplib.SMTPServerDisconnected:
        smtp_connections[sender_email].close()
        smtp_connection = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_connection.login(sender_email, emails[sender_email])
        smtp_connections[sender_email] = smtp_connection

        smtp_connection.sendmail("Wax Flame🔥", receiver, mime_message.as_string())
