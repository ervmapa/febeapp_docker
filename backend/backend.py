import logging
from flask import Flask, request, jsonify
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import os
import redis

app = Flask(__name__)

# Prometheus counters and gauge
update_counter = Counter('backend_requests_update_total', 'Total number of update requests')
other_request_counter = Counter('backend_requests_other_total', 'Total number of other requests')
cache_entries_counter = Gauge('backend_cache_entries_total', 'Total number of entries in the cache')
user_not_found_counter = Counter('backend_user_not_found_total', 'Total number of requests where user ID was not found in the cache')

# Initialize Redis connection
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6379))
redis_db = int(os.environ.get('REDIS_DB', 0))
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)

# Cache to store data for user IDs
cache = {}

def fetch_user_data_from_redis(user_id):
    # Modify this function to fetch user data from Redis
    # You may need to serialize/deserialize data depending on how you store it in Redis
    return redis_client.get(user_id)

def increment_user_not_found_counter():
    user_not_found_counter.inc()

def create_user(user_id, user_data):
    cache[user_id] = user_data
    cache_entries_counter.inc()

def delete_user(user_id):
    if user_id in cache:
        del cache[user_id]
        cache_entries_counter.dec()

        # Delete user data from Redis
        redis_client.delete(user_id)

def update_user(user_id):
    user_data = fetch_user_data_from_redis(user_id)

    if user_data is None:
        # User ID not found in Redis
        increment_user_not_found_counter()
        logging.warning(f"User ID {user_id} not found in Redis during an 'update' request.")
    else:
        # Update user data in the cache
        cache[user_id] = user_data
        cache_entries_counter.inc()

def process_request(user_id, request_type):
    try:
        if request_type == "create":
            # Attempt to fetch user data from Redis
            user_data = fetch_user_data_from_redis(user_id)

            if user_data is None:
                # User ID not found in the cache
                increment_user_not_found_counter()
                logging.warning(f"User ID {user_id} not found in the cache during a 'create' request.")
            else:
                # User ID found in the cache
                create_user(user_id, user_data)

        elif request_type == "delete":
            delete_user(user_id)

        elif request_type == "update":
            update_user(user_id)

        # Log user ID and cache entries to console using logging
        logging.info(f"Received {request_type} request for user ID: {user_id}. Cache entries: {len(cache)}")

        # Increment Prometheus counters based on the request type
        if request_type == "update":
            update_counter.inc()
        else:
            other_request_counter.inc()

        return jsonify({"message": f"{request_type.capitalize()} request processed successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()
    user_id = data.get("id")
    request_type = data.get("type")

    return process_request(user_id, request_type)

@app.route('/metrics', methods=['GET'])
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=5001)

