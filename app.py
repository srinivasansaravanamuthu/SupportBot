from flask import Flask, render_template, request, jsonify
import openai
import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

app = Flask(__name__)

# Configure OpenAI API key. Can be overridden from the settings dialog
openai.api_key = os.environ.get("OPENAI_API_KEY", "")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form['message']
    
    # Call OpenAI API to get a response
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}],
            max_tokens=150,
        )
        response_text = response.choices[0].message["content"].strip()
    except Exception as e:
        response_text = "Sorry, I'm having trouble responding right now. Please try again later."

    return jsonify({"response": response_text})


def scrape_geojson(url):
    """Return a list of GeoJSON links and descriptions from the provided URL."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for tag in soup.find_all(["a", "script", "link"]):
        for attr in ["href", "src", "data-src"]:
            link = tag.get(attr)
            if not link:
                continue
            if link.lower().endswith(".geojson") or link.lower().endswith(".json"):
                full_url = urljoin(url, link)
                desc = tag.get("title") or tag.get("alt") or tag.get("aria-label") or tag.text.strip()
                results.append({"url": full_url, "description": desc})
    return results


@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    target_url = data.get("url")
    api_key = data.get("api_key")
    if api_key:
        openai.api_key = api_key
    files = scrape_geojson(target_url)
    if not files:
        return jsonify({"success": False, "files": []})
    return jsonify({"success": True, "files": files})


@app.route("/recheck", methods=["POST"])
def recheck():
    data = request.get_json()
    files = data.get("files", [])
    target_url = data.get("url")
    api_key = data.get("api_key")
    if api_key:
        openai.api_key = api_key
    prompt = (
        "We scraped the following GeoJSON links from {url}:\n{files}\n"
        "Did we capture all geospatial data? Provide a short critique.".format(
            url=target_url, files="\n".join(f["url"] for f in files)
        )
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        critique = response.choices[0].message["content"].strip()
    except Exception:
        critique = "Unable to verify with ChatGPT at this time."
    return jsonify({"critique": critique})

if __name__ == '__main__':
    app.run(debug=True)
