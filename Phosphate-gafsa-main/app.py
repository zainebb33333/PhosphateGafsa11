from flask import Flask, jsonify, request, render_template
import sqlite3
import requests

app = Flask(__name__)


# Initialize the database
def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    # Create reports table
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY,
        content TEXT,
        created_at TEXT,
        city TEXT,
        environmental_info TEXT
    )''')
    # Create phosphate opinions table
    c.execute('''CREATE TABLE IF NOT EXISTS phosphate_opinions (
        id INTEGER PRIMARY KEY,
        opinion TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()


@app.route('/')
def home():
    return render_template('index.html')


def fetch_weather_data():
    API_KEY = "7b025f38abc4219df7e046cf9d8e23cf"  # Your API key
    city = "Gafsa"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Convert temperature from Kelvin to Celsius and return the data
            return {
                "temperature": round(data["main"]["temp"] - 273.15, 2),
                "humidity": data["main"]["humidity"],
                "conditions": data["weather"][0]["description"]
            }
        else:
            print(f"Error fetching data: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None


@app.route('/weather', methods=['GET'])
def get_weather():
    weather_data = fetch_weather_data()
    if weather_data:
        # Returning the data in JSON format
        return jsonify({
            "city": "Gafsa",
            "temperature": f"{weather_data['temperature']}°C",
            "humidity": f"{weather_data['humidity']}%",
            "conditions": weather_data["conditions"]
        })
    else:
        # Error handling if weather data couldn't be fetched
        return jsonify({"error": "Could not fetch weather data"}), 500


@app.route('/get_reports', methods=['GET'])
def get_reports():
    try:
        # Use a context manager for handling the database connection
        with sqlite3.connect('data.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM reports")
            rows = c.fetchall()

        # Structure the data in a more readable format
        reports = [{
            "id": row[1],
            "content": row[1],
            "city": row[3],
            "environmental_info": row[4],
            "created_at": row[2]
        } for row in rows]

        return jsonify(reports)

    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/add_phosphate_opinion', methods=['POST'])
def add_phosphate_opinion():
    # Ensure the content type is application/json
    if not request.is_json:
        return jsonify({"error": "Request must be in JSON format"}), 400

    # Get opinion from the JSON body of the request
    opinion = request.json.get('opinion')

    if not opinion:
        return jsonify({"error": "Opinion is required"}), 400

    try:
        # Connect to the database
        conn = sqlite3.connect('data.db')
        c = conn.cursor()

        # Insert the opinion into the database
        c.execute("INSERT INTO phosphate_opinions (opinion, created_at) VALUES (?, datetime('now'))", (opinion,))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        # Return success response
        return jsonify({"message": "Phosphate opinion added successfully!"}), 201

    except sqlite3.Error as e:
        # If there's a database error, return an error message
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/get_phosphate_opinions', methods=['GET'])
def get_phosphate_opinions():
    try:
        # Using 'with' to ensure the connection is properly closed
        with sqlite3.connect('data.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM phosphate_opinions ORDER BY created_at DESC")
            rows = c.fetchall()

        # Preparing the opinions data
        opinions = [{"id": row[0], "opinion": row[1], "created_at": row[2]} for row in rows]

        # Return the opinions as JSON
        return jsonify(opinions)

    except sqlite3.Error as e:
        # In case of database error
        return jsonify({"error": str(e)}), 500
@app.route('/add_report', methods=['POST'])
def add_report():
        # Get JSON data from the request
        content = request.json.get('content')
        city = request.json.get('city', 'Gafsa')  # Default to 'Gafsa' if not provided
        environmental_info = request.json.get('environmental_info', '')  # Default to empty string if not provided

        # Input validation: Check if 'content' is provided
        if not content:
            return jsonify({"error": "Content is required"}), 400

        # Connect to the SQLite database
        try:
            conn = sqlite3.connect('data.db')  # Replace with your database file
            c = conn.cursor()

            # Insert data into the 'reports' table
            c.execute(
                "INSERT INTO reports (content, city, environmental_info, created_at) VALUES (?, ?, ?, datetime('now'))",
                (content, city, environmental_info)
            )
            conn.commit()

        except sqlite3.Error as e:
            # Handle database errors
            conn.rollback()  # Rollback if there is an error
            return jsonify({"error": f"Database error: {str(e)}"}), 500

        finally:
            # Close the database connection
            conn.close()

        # Return a success message
        return jsonify({"message": "Report added successfully!"}), 201


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
