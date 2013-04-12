from django.contrib import admin

from chris.mailer.models import Message, DontSendEntry, MessageLog
from chris.mailer.engine import get_connection, EMAIL_BACKEND, socket_error, smtplib, logging

def send_mails(modeladmin, request, queryset):
    connection = None
    for message in queryset:
        if connection == None:
            connection = get_connection(backend=EMAIL_BACKEND)
        try:
            logging.info("sending message '%s' to %s" % (message.subject.encode("utf-8"), u", ".join(message.to_addresses).encode("utf-8")))
            email = message.email
            email.connection = connection
            email.send()
            message.delete()
        except (socket_error, smtplib.SMTPSenderRefused, smtplib.SMTPRecipientsRefused, smtplib.SMTPAuthenticationError), err:
            message.defer()
            logging.info("message deferred due to failure: %s" % err)
            MessageLog.objects.log(message, 3, log_message=str(err)) # @@@ avoid using literal result code
send_mails.short_description = u"Enviar e-mails"

class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "to_addresses", "subject", "when_added", "priority"]

    actions = (send_mails,)


class DontSendEntryAdmin(admin.ModelAdmin):
    list_display = ["to_address", "when_added"]


class MessageLogAdmin(admin.ModelAdmin):
    list_display = ["id", "to_addresses", "subject", "when_attempted", "result"]


admin.site.register(Message, MessageAdmin)
admin.site.register(DontSendEntry, DontSendEntryAdmin)
admin.site.register(MessageLog, MessageLogAdmin)
