import time
import string
import bot_token
import requests
import wikipedia
import aiml
import os
from slackclient import SlackClient
from nltk.tokenize import word_tokenize
from yahoo_finance import Share

bot_name = 'batbot'
bot_id = ''
sc_bot = SlackClient(bot_token.bottoken)

intro_templates = ['hello', 'hi', 'hey', 'hi there', 'hello there', 'what\'s up', 'hey there', 'what can you do', 'what can you do for me', 'how can you help me', 'how can you be helpful', 'tell me about yourself', 'who are you', 'who is this', 'Good Morning', 'Good Afternoon', 'Good Evening', 'knock knock']

intro_text = 'Hello! Here is what I can do for you: \n1. I can get you share price of any company you ask. \n2. Enter any query keyword and I can find you information about it!\nFor example try entering name of your favourite superhero! :)'


def list_channels():
    channels_call = sc_bot.api_call('channels.list')
    channels = channels_call['channels']
    if channels_call.get('ok'):
        print 'Channels: '
        for ch in channels:
            print ch['name'] + ', ' + ch['id']
    return channels


def is_intro(command):
    command_words = word_tokenize(command, language='english')
    command_words = [i.lower() for i in command_words if i not in string.punctuation]
    for template in intro_templates:
        template_words = word_tokenize(template, language='english')
        template_words.sort()
        command_words.sort()
        clen = len(command_words)
        tlen = len(template_words)
        hlen = clen if clen > tlen else tlen
        if abs(clen - tlen) <= 0.4 * hlen:
            diff = len([i for i in command_words if i in template_words])
            if diff >= 0.6 * hlen:
                return True
    return False


def process_input(command, channel):
    if is_intro(command):
        response = intro_text
        sc_bot.rtm_send_message(channel, response)
    else:
        results = wikipedia.search(command)
        response = ''
        count = 0
        flag = 0
        for result in results:
            try:
                page = wikipedia.page(result)
                response = page.url
                response += '\n'
                count += 1
            except wikipedia.exceptions.DisambiguationError as de:
                print 'Disambiguation Error'
                for opt in de.options:
                    try:
                        page = wikipedia.page(opt)
                        response = page.url
                        response += '\n'
                        count += 1
                    except Exception:
                        print 'Exception'
                    sc_bot.rtm_send_message(channel, response)
                    flag = 1
                    if count >= 5:
                        break

            except wikipedia.exceptions.PageError:
                print 'Page Error'
            if not flag == 1:
                sc_bot.rtm_send_message(channel, response)
                flag = 0
            if count >= 3:
                break


def get_symbol(symbol):
    url = "http://d.yimg.com/aq/autoc?query="+symbol+"&region=US&lang=en-US&callback="
    result = requests.get(url)
    data = result.json()
    print data
    if len(data['ResultSet']['Result']) > 0:
        return data['ResultSet']['Result'][0]['symbol'], data['ResultSet']['Result'][0]['name']
    else:
        return None, None


def get_price(name):
    symbol, name = get_symbol(name)
    if symbol and name:
        sdata = Share(symbol)
        return sdata.get_price(), name
    else:
        return None, None


def send_slack_response(response, channel):
    sc_bot.rtm_send_message(channel, response)

if __name__ == '__main__':

    kernel = aiml.Kernel()

    if os.path.isfile("bot_brain.brn"):
        os.remove("bot_brain.brn")
        kernel.bootstrap(learnFiles="std-startup.xml", commands="init")
        kernel.saveBrain("bot_brain.brn")
    else:
        kernel.bootstrap(learnFiles="std-startup.xml", commands="init")
        kernel.saveBrain("bot_brain.brn")

    users_call = sc_bot.api_call('users.list')
    if users_call['ok']:
        for user in users_call['members']:
            if user['name'] == bot_name:
                bot_id = user['id']
                print 'BotID: ' + bot_id
    else:
        print 'Error in API-Call!'
        exit(1)

    if sc_bot.rtm_connect():
        while True:
            rtm_read_data = sc_bot.rtm_read()
            if len(rtm_read_data) > 0:
                for ip in rtm_read_data:
                    #print ip
                    if ip.has_key('text') and ip.has_key('user') and ip['user'] != bot_id:
                        command = ip['text']
                        channel = ip['channel']
                        print 'Command: ' + command
                        response = kernel.respond(command)
                        if "SP" in response:
                            response = response.replace("SP", "")
                            price, name = get_price(response)
                            if price and name:
                                send_slack_response("Share price of " + name + " is " + price, channel)
                            else:
                                send_slack_response("I doubt if " + response + " is a public company!", channel)
                        else:
                            process_input(command, channel)
            time.sleep(1)
    else:
        print 'Connection Failed, invalid token?'
        exit(1)
