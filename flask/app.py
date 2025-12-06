#!/usr/bin/env python3
"""
Flask API for IoT IDS Data Processing
Processes MQTT messages and forwards logs to Loki and InfluxDB
"""

import os
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import paho.mqtt.client as mqtt
import requests
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # Enable CORS for traffic monitoring dashboard

# Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mosquitto')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
LOKI_URL = os.getenv('LOKI_URL', 'http://loki:3100/loki/api/v1/push')

# InfluxDB Configuration
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', 'iot-ids-admin-token-change-in-production')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'iot-ids')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'iot-data')

# Initialize InfluxDB client
influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MQTT Client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = lambda client, userdata, flags, rc: logger.info(f"Connected to MQTT broker with result code {rc}")
mqtt_client.on_message = lambda client, userdata, msg: process_mqtt_message(msg)

def process_mqtt_message(msg):
    """Process incoming MQTT messages and send to Loki"""
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        # Try to parse as JSON
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = {"raw": payload}
        
        # Create log entry for Loki
        log_entry = {
            "streams": [{
                "stream": {
                    "topic": topic,
                    "source": "mqtt"
                },
                "values": [[
                    str(int(datetime.now().timestamp() * 1000000000)),  # Nanoseconds
                    json.dumps({
                        "topic": topic,
                        "message": data,
                        "timestamp": datetime.now().isoformat()
                    })
                ]]
            }]
        }
        
        # Send to Loki
        try:
            response = requests.post(LOKI_URL, json=log_entry)
            if response.status_code == 204:
                logger.info(f"Log sent to Loki for topic: {topic}")
            else:
                logger.warning(f"Failed to send log to Loki: {response.status_code}")
        except Exception as e:
            logger.error(f"Loki error: {e}")
        
        # Send to InfluxDB
        try:
            point = Point("mqtt_messages") \
                .tag("topic", topic) \
                .tag("source", "mqtt") \
                .field("message_count", 1) \
                .time(datetime.utcnow())
            
            # Add numeric fields if present
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        point = point.field(key, value)
                    elif isinstance(value, str) and len(value) < 256:
                        point = point.tag(key, value)
            
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
            logger.info(f"Data sent to InfluxDB for topic: {topic}")
        except Exception as e:
            logger.error(f"InfluxDB error: {e}")
            
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "flask-api"}), 200

@app.route('/api/data', methods=['POST'])
def receive_data():
    """Receive data from external sources"""
    try:
        data = request.get_json()
        logger.info(f"Received data: {data}")
        
        # Process and forward to Loki
        log_entry = {
            "streams": [{
                "stream": {
                    "source": "api"
                },
                "values": [[
                    str(int(datetime.now().timestamp() * 1000000000)),
                    json.dumps({
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    })
                ]]
            }]
        }
        
        # Send to Loki
        try:
            response = requests.post(LOKI_URL, json=log_entry)
            loki_status = response.status_code
        except Exception as e:
            logger.error(f"Loki error: {e}")
            loki_status = None
        
        # Send to InfluxDB
        try:
            point = Point("api_data") \
                .tag("source", "api") \
                .field("message_count", 1) \
                .time(datetime.utcnow())
            
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        point = point.field(key, value)
            
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
            influx_status = "success"
        except Exception as e:
            logger.error(f"InfluxDB error: {e}")
            influx_status = "error"
        
        return jsonify({
            "status": "received",
            "loki_status": loki_status,
            "influxdb_status": influx_status
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing API data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get processing statistics"""
    return jsonify({
        "mqtt_broker": MQTT_BROKER,
        "mqtt_port": MQTT_PORT,
        "loki_url": LOKI_URL,
        "influxdb_url": INFLUXDB_URL,
        "influxdb_bucket": INFLUXDB_BUCKET,
        "status": "operational"
    }), 200

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get metrics from InfluxDB for traffic monitoring"""
    try:
        query_api = influx_client.query_api()
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -1h)
        |> filter(fn: (r) => r["_measurement"] == "mqtt_messages")
        |> aggregateWindow(every: 1m, fn: count, createEmpty: false)
        |> yield(name: "count")
        '''
        
        result = query_api.query(org=INFLUXDB_ORG, query=query)
        
        metrics = []
        for table in result:
            for record in table.records:
                metrics.append({
                    "time": record.get_time().isoformat(),
                    "value": record.get_value(),
                    "topic": record.values.get("topic", "unknown")
                })
        
        return jsonify({"metrics": metrics}), 200
    except Exception as e:
        logger.error(f"Error querying InfluxDB: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/traffic')
def traffic_dashboard():
    """Redirect to traffic monitoring dashboard"""
    return '<html><head><meta http-equiv="refresh" content="0; url=http://localhost:8080"></head><body>Redirecting to <a href="http://localhost:8080">Traffic Dashboard</a></body></html>', 200

def connect_mqtt():
    """Connect to MQTT broker and subscribe to topics"""
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        # Subscribe to all topics (use specific topics in production)
        mqtt_client.subscribe("#")
        mqtt_client.loop_start()
        logger.info("MQTT client connected and subscribed")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")

if __name__ == '__main__':
    # Connect to MQTT on startup
    connect_mqtt()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)

