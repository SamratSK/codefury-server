from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import hashlib
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'


with open('data/disaster_data.json') as f:
    disaster_data = json.load(f)


def get_db_connection():
    conn = sqlite3.connect('userdata.db')
    conn.row_factory = sqlite3.Row
    return conn


conn = get_db_connection()
conn.execute('''
CREATE TABLE IF NOT EXISTS userdata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL
)
''')
conn.commit()
conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@app.route('/')
def index():
    return render_template('index.html')
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')


    responses = {
        "hello": "Hello! How can I assist you with disaster information today?",
        "help": "Sure, I can help! You can ask about safety tips or specific disasters.",
        "flood": "Floods are dangerous. Make sure to move to higher ground and avoid floodwaters.",
        "earthquake": "In case of an earthquake, drop, cover, and hold on. Stay indoors if you are already inside, and move to an open area away from buildings if you are outside.",
        "cyclone": "Hurricanes bring strong winds and flooding. Secure your home and evacuate if recommended.",
        "tsunami": "If you’re near the coast and feel an earthquake, move to higher ground immediately as tsunamis can follow.",
        "bye": "Goodbye! Stay safe.",
        "thank you": "You're welcome! Let me know if you need more information."
    }

    bot_response = responses.get(user_message.lower(),
                                 "Sorry, I didn't understand that. Can you please ask something else?")

    return jsonify({"response": bot_response})

@app.route('/updates')
def updates():
    return render_template('updates.html', disaster_data=disaster_data)

@app.route('/safety_tips')
def safety_tips():
    return render_template('safety_tips.html')

@app.route('/disaster_info/<disaster_type>')
def disaster_info(disaster_type):
    info = disaster_data.get(disaster_type, {})
    return render_template('disaster_info.html', info=info, disaster_type=disaster_type.capitalize())

@app.route('/api/disaster_data')
def disaster_data_api():
    return jsonify(disaster_data)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hash_password(password)

        conn = get_db_connection()
        conn.execute('INSERT INTO userdata (username, password_hash) VALUES (?, ?)',
                     (username, password_hash))
        conn.commit()
        conn.close()

        flash('Registration successful!')
        return redirect(url_for('register'))

    return render_template('register.html')


if __name__ == '__main__':
    app.run(debug=True)
