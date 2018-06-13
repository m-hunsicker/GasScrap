#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 11 22:58:42 2018

@author: mitch
"""

from datetime import datetime
import os
import requests
import private_data


#Emails for booking notification
SUPPORT_EMAIL = private_data.SUPPORT_EMAIL

def send_html_email(receiver, subject, text, inline_file):
    """
    Envoi d'email via mailgun
    """
    key = private_data.KEY
    sandbox = private_data.SANDBOX

    request_url = 'https://api.mailgun.net/v3/{0}/messages'.format(sandbox)

    #Transform text into readable  html
    text = text.replace("\n", "<br>")

    data = {
        'from': 'Gasprice_bot@mailgun.org',
        'to': receiver,
        'subject': subject,
        "html": f'<html><body><p>{text}</p><img src="cid:'+\
                f'{os.path.basename(inline_file)}" alt="Gas curve"></body></html>'}

    request = requests.post(request_url, auth=('api', key),
                            files=[("inline", open(inline_file, 'rb'))],
                            data=data)
    log_print('Email status: {0}'.format(request.status_code))



def send_email(receiver, subject, text):
    """
    Envoi d'email via mailgun
    """
    key = private_data.KEY
    sandbox = private_data.SANDBOX

    request_url = 'https://api.mailgun.net/v3/{0}/messages'.format(sandbox)

    data = {'from': 'Gasprice_bot@mailgun.org',
            'to': receiver,
            'subject': subject,
            'text': text}

    request = requests.post(request_url, auth=('api', key), data=data)
    log_print('Email status: {0}'.format(request.status_code))




def log_print(text):
    """
    Impression à l'écran avec l'horodatage préfixée.
    """
    print((datetime.now()).strftime("%Y-%m-%dT%H:%M:%S"), ": ", text)
    