from datetime import datetime
import numpy as np
from sklearn.cluster import DBSCAN
from scipy.signal import find_peaks
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from collections import defaultdict
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

import utils
from .add_stop_words import additional_stop_words

nltk.download('punkt')
nltk.download('stopwords')

def validate_clusters(clustered_messages):
    validated_clusters = []
    for cluster in clustered_messages:
        senders = set(msg['sender_name'] for msg in cluster)
        if len(senders) < 2:
            # merge with the next cluster if possible
            if validated_clusters:
                validated_clusters[-1].extend(cluster)
            else:
                validated_clusters.append(cluster)
        else:
            validated_clusters.append(cluster)
    return validated_clusters

def create_dynamic_clusters(messages):
    if not messages:
        return []

    # calculate intervals where the sender changes
    sender_changes = [0]
    last_sender = messages[0]['sender_name']
    for i in range(1, len(messages)):
        if messages[i]['sender_name'] != last_sender:
            sender_changes.append(i)
            last_sender = messages[i]['sender_name']
    sender_changes.append(len(messages))

    timestamps = np.array([messages[i]['timestamp_ms'] for i in sender_changes[:-1]])
    intervals = np.diff(timestamps)

    # normalize intervals
    if np.max(intervals) == np.min(intervals):
        intervals_normalized = intervals
    else:
        intervals_normalized = (intervals - np.min(intervals)) / (np.max(intervals) - np.min(intervals))
    
    # create artificial timestamps for clustering
    artificial_timestamps = np.cumsum(np.insert(intervals_normalized, 0, 0)).reshape(-1, 1)

    eps = np.mean(intervals_normalized) * 2
    dbscan = DBSCAN(eps=eps, min_samples=2)
    clusters = dbscan.fit_predict(artificial_timestamps)

    clustered_messages = defaultdict(list)
    for i, cluster_id in enumerate(clusters):
        if cluster_id != -1:
            for msg_index in range(sender_changes[i], sender_changes[i + 1]):
                clustered_messages[cluster_id].append(messages[msg_index])
    
    initial_clusters = list(clustered_messages.values())
    validated_clusters = validate_clusters(initial_clusters)
    
    return validated_clusters

def extract_topics(messages, num_topics=3, num_words=100, min_docs=2):
    preprocessed_docs = []
    for msg in messages:
        if utils.include_message(msg):
            formatted_msg = utils.format_message(msg)
            if formatted_msg:
                preprocessed_docs.append(preprocess_text(formatted_msg))
    
    if len(preprocessed_docs) < min_docs:
        return [""]
    elif len(preprocessed_docs) >= 30:
        num_topics = round(len(preprocessed_docs) / 10)
    try:
        #vectorizer = TfidfVectorizer(max_df=0.95, min_df=1)
        vectorizer = CountVectorizer(max_df=0.95, min_df=1)
        doc_term_matrix = vectorizer.fit_transform(preprocessed_docs)
        
        feature_names = vectorizer.get_feature_names_out()

        lda = LatentDirichletAllocation(n_components=num_topics, random_state=42)
        lda.fit(doc_term_matrix)
        
        unique_topics = set()
        for topic in lda.components_:
            top_words_idx = topic.argsort()[:-num_words - 1:-1]
            top_words = [feature_names[i] for i in top_words_idx]
            unique_topics.update(top_words)

        final_topics = list(unique_topics)[:num_words]

        return final_topics
    except ValueError:
        return [""]

def preprocess_text(text):
    # remove sender name from the text
    text = ': '.join(text.split(': ')[1:])
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    stop_words.update(additional_stop_words)
    tokens = [token for token in tokens if token.isalpha() and token not in stop_words]
    return ' '.join(tokens)