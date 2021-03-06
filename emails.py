from run import app, mail, config, markdown

from flask_mail import Message

from html2text import HTML2Text

text_maker = HTML2Text()
text_maker.ignore_links = True

default_sender = tuple(config['email']['default_sender'])
default_recipient = tuple(config['email']['default_recipient'])

from flaskext.markdown import Markdown
markdown_no_math = Markdown(app, extensions=['extra'])

import textwrap

def send_email(body_md, sender=None, recipients=None):
    body_md = body_md.strip()
    assert body_md.startswith('Subject: ')
    subject, _, body_md = body_md.partition('\n')
    _, _, subject = subject.partition(' ')
    if not sender:
        sender = default_sender
    if not recipients:
        recipients = [default_recipient]
    msg = Message(subject)
    msg.recipients = recipients
    msg.sender = sender
    msg.html = textwrap.fill(markdown_no_math(body_md), 990)
    msg.body = text_maker.handle(msg.html)
    mail.send(msg)
