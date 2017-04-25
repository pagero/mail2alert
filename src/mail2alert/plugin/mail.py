import logging
import re

from mail2alert.actions import Actions
from mail2alert.rules import Rule


class Manager:
    """
    mail.Manager objects are handed mail messages.

    Based on the mail2alert configuration and mail content,
    they determine what to do with the mail message.
    """

    def __init__(self, conf):
        logging.info('Started {}'.format(self.__class__))
        self.conf = conf

    def rules(self, rule_list):
        for rule in rule_list:
            yield MailRule(rule)

    @property
    def rule_funcs(self):
        return {'mail': Mail()}

    def wants_message(self, mail_from, rcpt_tos, content):
        """
        Determine whether the manager is interested in a certain message.
        """
        wanted = self.conf['messages-we-want']
        wanted_to = wanted.get('to')
        wanted_from = wanted.get('from')
        logging.debug('We vant to: {} or from: {}'.format(wanted_to, wanted_from))
        logging.debug('We got to: {} and from: {}'.format(rcpt_tos, mail_from))
        if wanted_to:
            return wanted_to in rcpt_tos
        if wanted_from:
            return wanted_from == mail_from

    def process_message(self, mail_from, rcpt_tos, binary_content):
        logging.debug('process_message("{}", {}, {})'.format(mail_from, rcpt_tos, binary_content))
        recipients = []
        msg = Message(binary_content)
        logging.debug('Extracted message %s' % msg)
        for rule in self.rules(self.conf['rules']):
            logging.debug('Check %s' % rule)
            actions = Actions(rule.check(msg, self.rule_funcs))
            recipients.extend(actions.mailto)
        return mail_from, recipients, binary_content


class Mail:
    def in_subject(self, *words):
        def words_in_subject(msg):
            return all(word.lower() in msg['subject'].lower() for word in words)

        return words_in_subject


class Message(dict):
    def __init__(self, content):
        super().__init__()
        subject_pattern = re.compile(r'Subject:(.+)$', re.M)
        mo = subject_pattern.search(content.decode())
        self['subject'] = mo.group(1).strip()


class MailRule(Rule):
    pass

