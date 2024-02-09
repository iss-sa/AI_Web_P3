## channel.py - a simple message channel
##

from flask import Flask, request, render_template, jsonify
import datetime
import random
import json
import requests

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'


    #Flas Sql settings??
# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

#variable nummer!!
Number_to_guess = random.randint(0,50)
Beginning_Game = True


HUB_URL = 'http://localhost:5555'
HUB_AUTHKEY = '1234567890'
CHANNEL_AUTHKEY = '0987654321'
CHANNEL_NAME = "Number Guessing Game"
CHANNEL_ENDPOINT = "http://localhost:5001" # don't forget to adjust in the bottom of the file
CHANNEL_FILE = 'messages.json'


@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # send a POST request to server /channels
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             data=json.dumps({
            "name": CHANNEL_NAME,
            "endpoint": CHANNEL_ENDPOINT,
            "authkey": CHANNEL_AUTHKEY}))

    if response.status_code != 200:
        print("Error creating channel: "+str(response.status_code))
        return

def check_authorization(request):
    global CHANNEL_AUTHKEY
    # check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    global CHANNEL_NAME
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME}),  200

# GET: Return list of messages
@app.route('/', methods=['GET'])
def home_page():
    if not check_authorization(request):
        return "Invalid authorization", 400
    # fetch channels from server

    return jsonify(read_messages())

# POST: Send a message
@app.route('/', methods=['POST'])
def send_message():
    # fetch channels from server
    # check authorization header
    if not check_authorization(request):
        return "Invalid authorization", 400
    
    # check if message is present
    message = request.json
    

    if not message:
        return "No message", 400
    if not 'content' in message:
        return "No content", 400
    if not 'sender' in message:
        return "No sender", 400
    if not 'timestamp' in message:
        return "No timestamp", 400
    

    #get chat bot answer
    answer = bot(message)
    # add message to messages
    messages = read_messages()

    messages.append({'content':message['content'], 'sender':message['sender'], 'timestamp':message['timestamp']})
    messages.append(answer)

    save_messages(messages)
    return "OK", 200


def read_messages():

    global Beginning_Game
    global CHANNEL_FILE

    try:
        f = open(CHANNEL_FILE, 'r')
    except FileNotFoundError:
        return []
    try:
        messages = json.load(f)
        if Beginning_Game == True:
            
            answer_bot = "Heyloo. You have entered my guessing game. Enter a number between 0 and 50. Happy Playing :)"

            time_stamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
            response = {'content':answer_bot, 'sender':'Bot: ILSANI', 'timestamp':time_stamp}

            messages.append(response)
            save_messages(messages)

            Beginning_Game = False
    except json.decoder.JSONDecodeError:
        messages = []
    f.close()
    return messages

def save_messages(messages):
    global CHANNEL_FILE
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f)


#our guessing game
def bot(message):

    global Number_to_guess
    
    content = message['content']
    
    try:
        content = int(content)
        if content < 50 and content > 0:
            if content < Number_to_guess:
                answer_bot = "Your guess is too low. Take another guess."
            elif content > Number_to_guess:
                answer_bot = "Your guess is too high. Take another guess."
            elif content == Number_to_guess:
                answer_bot = "Yeah! You guessed my number. Lucky you. Start a new game."
                Number_to_guess = random.randint(0, 50)
            else:
                answer_bot = "Try again, pleaseee"
        else:
            answer_bot = "Your number is out of bound."
    except ValueError:
        answer_bot = "Your input is not valid. Please enter a number"

    #convert timestamp using datetime.datetime and converting to string 
    time_stamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

    response = {'content':answer_bot, 'sender':'Bot: ILSANI', 'timestamp':time_stamp}
    return response

# Start development web server
if __name__ == '__main__':
    app.run(port=5001, debug=True)
