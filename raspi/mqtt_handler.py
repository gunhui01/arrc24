import paho.mqtt.client as mqtt
import time

# MQTT 연결 및 메시지 처리 콜백 함수 정의
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("jetson/command")
    print("Userdata on connect:", userdata)

def on_message(client, userdata, msg):
    if msg.payload:
        message = msg.payload.decode("utf-8")
        cmd, ps = message.split(':')

        ## start: ##
        if cmd == "start":
            if ps == "light":
                userdata.get("light_on", lambda: None)()
            elif ps == "obstacle_publisher_process":
                obstacle_publisher_process = userdata.get("obstacle_publisher_process")
                if not obstacle_publisher_process.is_alive():
                    obstacle_publisher_process.start()
            elif ps == "video_recorder_process":
                video_recorder_process = userdata.get("video_recorder_process")
                if not video_recorder_process.is_alive():
                    video_recorder_process.start()
            elif ps == "apple_count_subscriber_process":
                userdata.get("apple_count_subscriber_process").start()
        ## restart: ##
        elif cmd == "restart":
            if ps == "video_recorder_process":
                userdata.get("video_recorder_event").clear()
        ## end: ##
        elif cmd == "end":
            if ps == "light":
                userdata.get("light_off", lambda: None)()
            elif ps == "video_recorder_process":
                print("Area termination signal detected.")
                video_recorder_event = userdata.get("video_recorder_event")
                video_recorder_event.set() # Save recorded video file
                time.sleep(1)
                while not video_recorder_event.is_set(): # Wait for the event to clear
                    time.sleep(1)
                client.publish("raspi/video_process_status", "video_recorder_process ended")
        ## screen: ##
        elif cmd == "screen":
            userdata.get("command_share_queue").put(message)

# MQTT 클라이언트를 생성하고 실행하는 함수 정의
def mqtt_handler(userdata):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.user_data_set(userdata)
    client.connect("192.168.0.2", port=1883, keepalive=60)
    client.loop_forever()  # MQTT 메시지를 지속적으로 처리