from flask import Flask, render_template, request, jsonify
import openai
import os

app = Flask(__name__)

# Configure OpenAI API key
openai.api_key = 'YOUR_OPENAI_API_KEY'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form['message']
    
    # Call OpenAI API to get a response
    try:
        response = openai.Completion.create(
            engine="davinci-codex",
            prompt=user_message,
            max_tokens=150
        )
        response_text = response.choices[0].text.strip()
    except Exception as e:
        response_text = "Sorry, I'm having trouble responding right now. Please try again later."

    return jsonify({"response": response_text})

if __name__ == '__main__':
    app.run(debug=True)
