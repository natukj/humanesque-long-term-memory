import json
from datetime import datetime

import utils

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def format_cluster(cluster):
    start_time = datetime.fromtimestamp(min(msg['timestamp_ms']/1000 for msg in cluster))
    end_time = datetime.fromtimestamp(max(msg['timestamp_ms']/1000 for msg in cluster))
    
    topics = utils.extract_topics(cluster)
    
    return {
        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
        'duration': str(end_time - start_time),
        'messages': cluster,
        'topics': topics
    }

file_path = input("Enter the path to the chat .json/.txt: ")

if file_path.endswith('.json'): # ig/fb
    data = load_json(file_path)
elif file_path.endswith('.txt'): # wa
    data = utils.parse_txt_to_dict(file_path)
else:
    raise ValueError("File must be a .json or .txt file")

messages = data['messages']

messages.sort(key=lambda x: x['timestamp_ms'])

clusters = utils.create_dynamic_clusters(messages)
formatted_clusters = [format_cluster(cluster) for cluster in clusters]

for i, cluster in enumerate(formatted_clusters, 1):
    print(f"Cluster {i}:")
    print(f"Start time: {cluster['start_time']}")
    print(f"End time: {cluster['end_time']}")
    print(f"Duration: {cluster['duration']}")
    print(f"Number of messages: {len(cluster['messages'])}")
    print("Topics:", ', '.join(cluster['topics']))
    print()


    print("Messages:")
    for msg in cluster['messages']:
        if utils.include_message(msg):
            print(f"  - {utils.format_message(msg)}")
    print()
