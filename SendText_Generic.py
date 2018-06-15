from __future__ import print_function

import subprocess
import glob
import os
import datetime
import sys
import requests

from twilio.rest import Client

"""
Add the information from your own Twilio account, and rename this program to SendText.py
"""

default_message = "No message has been defined"

def Send_Text(MESSAGE):
	accountSID = ""
	authToken = ""

	twilioCli = Client(accountSID, authToken)
	myTwilioNumber = ""
	myCellPhone = ""

	message = twilioCli.messages.create(body=str(MESSAGE), from_=myTwilioNumber, to=myCellPhone)

if __name__ == '__main__':
	Send_Text(str(default_message))