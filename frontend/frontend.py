from flask import Flask, request, jsonify
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import redis
import requests
import os

app = Flask(__name__)
redis_client = redis.StrictRedis(host=os.environ.get('REDIS_HOST', 'localhost'),
                                port=int(os.environ.get('REDIS_PORT', 6379)),
                                db=0)

# Prometheus counters
create_counter = Counter('requests_create_total', 'Total number of create requests')
modify_counter = Counter('requests_modify_total', 'Total number of modify requests')
delete_counter = Counter('requests_delete_total', 'Total number of delete requests')
redis_set_failure_counter = Counter('redis_set_failure_total', 'Total number of Redis set failures')
backend_request_failure_counter = Counter('backend_request_failure_total', 'Total number of backend request failures')
missing_user_id_counter = Counter('missing_user_id_total', 'Total number of requests with missing user_id')
missing_data_value_counter = Counter('missing_data_valte_total', 'Total number of requests with missing data_value')

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5001/update')

def send_to_backend(payload):
    try:
        response = requests.post(BACKEND_URL, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        # Increment Prometheus counter for successful backend request
    except requests.exceptions.RequestException as e:
        # Handle request failures and increment failure counter
        backend_request_failure_counter.inc()
        return jsonify({"error": f"Backend request error: {str(e)}"}), 500

    return jsonify({"message": "Backend request processed successfully"}), 200

def write_to_redis(user_id, data_value):
    try:
        # Attempt to set the value in Redis
        redis_client.set(user_id, data_value)
        # Increment Prometheus counter for successful Redis set
    except redis.exceptions.ConnectionError as e:
        # Handle connection errors and increment failure counter
        redis_set_failure_counter.inc()
        return jsonify({"error": f"Error connecting to Redis: {str(e)}"}), 500
    except Exception as e:
        # Handle other Redis-related errors and increment failure counter
        redis_set_failure_counter.inc()
        return jsonify({"error": f"Redis error: {str(e)}"}), 500

    return None  # Indicates successful write to Redis

def parse(data):
    user_id = data.get("user")
    data_value = data.get("data")
    request_type = data.get("type")

    if user_id is None:
        # Increment Prometheus counter for missing user_id
        missing_user_id_counter.inc()
        return jsonify({"error": "Missing 'user_id' in the request"}), 400


    if data_value is None:
        # Increment Prometheus counter for missing user_id
        missing_data_value_counter.inc()
        return jsonify({"error": "Missing 'data_value' in the request"}), 400

    write_result = write_to_redis(user_id, data_value)
    if write_result is not None:
        return write_result

    # Send a request to the backend
    payload = {"type": request_type, "id": user_id}
    return send_to_backend(payload)

@app.route('/control', methods=['POST'])
def control():
    try:
        data = request.get_json()
        return parse(data)
    except Exception as e:
        # Increment Prometheus counter for other failures
        return jsonify({"error": str(e)}), 500

@app.route('/metrics', methods=['GET'])
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

