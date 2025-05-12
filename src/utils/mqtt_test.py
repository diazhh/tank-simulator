"""
Utility module for testing MQTT communication with ThingsBoard.
"""
import os
import sys
import time
import json
import argparse
from typing import Dict, List, Optional

import paho.mqtt.client as mqtt

# Add parent directory to path to allow importing from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.config_loader import ConfigLoader


class MQTTTest:
    """
    Class for testing MQTT communication with ThingsBoard.
    
    Attributes:
        client (mqtt.Client): MQTT client
        config (Dict): Communication configuration
        connected (bool): Connection status
        messages (List[Dict]): List of received messages
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the MQTT test client.
        
        Args:
            config_path: Path to the communication configuration file
        """
        # Load configuration
        config_loader = ConfigLoader(os.path.dirname(config_path))
        self.config = config_loader.load_config(os.path.basename(config_path).split('.')[0])
        
        # Create MQTT client
        self.client = mqtt.Client(client_id=f"mqtt_test_{int(time.time())}")
        self.connected = False
        self.messages = []
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Set up authentication if provided
        if 'username' in self.config['mqtt'] and 'password' in self.config['mqtt']:
            self.client.username_pw_set(
                self.config['mqtt']['username'],
                self.config['mqtt']['password']
            )
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            print("Connected to MQTT broker")
            self.connected = True
        else:
            print(f"Failed to connect to MQTT broker with code {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker."""
        print(f"Disconnected from MQTT broker with code {rc}")
        self.connected = False
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received."""
        try:
            # Parse JSON payload
            payload = json.loads(msg.payload.decode())
            
            # Add message to list
            self.messages.append({
                'topic': msg.topic,
                'payload': payload,
                'timestamp': time.time()
            })
            
            # Print message
            print(f"Received message on topic {msg.topic}:")
            print(json.dumps(payload, indent=2))
            print("-" * 40)
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def connect(self) -> bool:
        """
        Connect to the MQTT broker.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            self.client.connect(
                self.config['mqtt']['broker'],
                self.config['mqtt']['port'],
                self.config['mqtt']['connection']['keep_alive']
            )
            self.client.loop_start()
            
            # Wait for connection to establish
            timeout = 5
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            return self.connected
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
    
    def subscribe(self, topic: str) -> bool:
        """
        Subscribe to an MQTT topic.
        
        Args:
            topic: Topic to subscribe to
            
        Returns:
            True if subscription was successful, False otherwise
        """
        if not self.connected:
            print("Not connected to MQTT broker")
            return False
        
        result = self.client.subscribe(topic, qos=self.config['mqtt']['qos'])
        if result[0] == mqtt.MQTT_ERR_SUCCESS:
            print(f"Subscribed to topic {topic}")
            return True
        else:
            print(f"Failed to subscribe to topic {topic}: {result}")
            return False
    
    def publish(self, topic: str, payload: Dict) -> bool:
        """
        Publish a message to an MQTT topic.
        
        Args:
            topic: Topic to publish to
            payload: Message payload
            
        Returns:
            True if publish was successful, False otherwise
        """
        if not self.connected:
            print("Not connected to MQTT broker")
            return False
        
        try:
            result = self.client.publish(
                topic,
                json.dumps(payload),
                qos=self.config['mqtt']['qos'],
                retain=self.config['mqtt']['retain']
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Published message to topic {topic}")
                return True
            else:
                print(f"Failed to publish message: {result}")
                return False
        except Exception as e:
            print(f"Error publishing message: {e}")
            return False


def main():
    """Main entry point for MQTT test utility."""
    parser = argparse.ArgumentParser(description='MQTT Test Utility')
    parser.add_argument('--config', type=str, default='../config/communication.yaml',
                        help='Path to communication configuration file')
    parser.add_argument('--action', type=str, choices=['subscribe', 'publish'], required=True,
                        help='Action to perform')
    parser.add_argument('--topic', type=str,
                        help='MQTT topic (defaults to ThingsBoard base topic)')
    parser.add_argument('--payload-file', type=str,
                        help='Path to JSON file containing payload (for publish action)')
    parser.add_argument('--monitor-time', type=int, default=60,
                        help='Time to monitor for messages in seconds (for subscribe action)')
    args = parser.parse_args()
    
    # Create MQTT test client
    test_client = MQTTTest(args.config)
    
    # Connect to broker
    print(f"Connecting to MQTT broker at {test_client.config['mqtt']['broker']}:{test_client.config['mqtt']['port']}...")
    if not test_client.connect():
        print("Error: Failed to connect to MQTT broker")
        sys.exit(1)
    
    try:
        # Get default topic if not specified
        if not args.topic:
            if args.action == 'subscribe':
                # Subscribe to all messages
                args.topic = test_client.config['mqtt']['thingsboard']['base_topic'] + "/#"
            else:
                # Publish to telemetry topic
                args.topic = (
                    test_client.config['mqtt']['thingsboard']['base_topic'] + "/" +
                    test_client.config['mqtt']['thingsboard']['telemetry_topic']
                )
        
        if args.action == 'subscribe':
            # Subscribe to topic
            if not test_client.subscribe(args.topic):
                sys.exit(1)
            
            # Monitor for messages
            print(f"Monitoring for messages on topic {args.topic} for {args.monitor_time} seconds...")
            time.sleep(args.monitor_time)
            
            # Print summary
            print(f"Received {len(test_client.messages)} messages")
        
        elif args.action == 'publish':
            # Check if payload file is provided
            if not args.payload_file:
                print("Error: Payload file is required for publish action")
                sys.exit(1)
            
            # Load payload from file
            try:
                with open(args.payload_file, 'r') as file:
                    payload = json.load(file)
            except Exception as e:
                print(f"Error loading payload file: {e}")
                sys.exit(1)
            
            # Publish message
            if not test_client.publish(args.topic, payload):
                sys.exit(1)
    
    finally:
        # Disconnect from broker
        test_client.disconnect()


if __name__ == '__main__':
    main()
