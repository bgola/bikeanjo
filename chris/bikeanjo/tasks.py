# coding: utf-8
from celery import Celery
from chris.mailer.engine import get_connection, EMAIL_BACKEND, socket_error, smtplib, logging
from chris.mailer.models import Message
from chris.bikeanjo.models import Request, EmailMessage
from django.core.validators import email_re

from celery.task.schedules import crontab  
from celery.decorators import task  
  
from datetime import datetime, timedelta

import time

@task()  
def send_mails():
    messages = Message.objects.order_by('when_added')
    if messages.count() <= 0:
        return True
    connection = get_connection(backend=EMAIL_BACKEND)
    for message in messages:
        if not email_re.search(str(message.email)):
            message.delete()
            continue
        try:
            email = message.email
            email.connection = connection
            email.send()
            message.delete()
        except (socket_error, smtplib.SMTPSenderRefused, smtplib.SMTPRecipientsRefused, smtplib.SMTPAuthenticationError), err:
            message.defer()
            MessageLog.objects.log(message, 3, log_message=str(err))
    return True

@task
def notify_inactive_requests():
    # inactive for 10 days
    reqs_10_days = Request.objects.filter(last_modification__lt=datetime.today() - timedelta(days=9), 
                                         last_modification__gt=datetime.today() - timedelta(days=11),
                                         status="ONGOING")
    
    for req in reqs_10_days:
        # notifica bike anjo
        req.send_mail(email_msg=EmailMessage.objects.get(email="bikeanjo-nao-respondeu-pedido"))

    # inactive for 15 days or more
    reqs_15_days = Request.objects.filter(last_modification__lt=datetime.today() - timedelta(days=14), 
                                          #last_modification__gt=datetime.today() - timedelta(days=16),
                                          status="ONGOING")
    
    for req in reqs_15_days:
        req.send_mail(email_msg=EmailMessage.objects.get(email="pedido-encaminhado-a-outro-bikeanjo"))
        req.do_matching()

    """
    # inactive for 20 days
    reqs_20_days = Request.objects.filter(last_modification__lt=datetime.today() - timedelta(days=19), 
                                          status__in="ONGOING")

    for req in reqs_20_days:
        req.send_mail(EmailMessage.objects.get("pedido-encaminhado-a-outro-bikeanjo"))
        req.do_matching()
    """
