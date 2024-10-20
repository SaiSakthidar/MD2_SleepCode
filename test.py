from pymongo import MongoClient
from flask import Flask, jsonify
from flask_cors import CORS
import time
import random
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client['sai']
collection = db['companies']

app = Flask(__name__)
CORS(app) 

def generate_random_query():
    fields = [
        "name", "permalink", "crunchbase_url", "homepage_url", "blog_url",
        "blog_feed_url", "twitter_username", "category_code", "number_of_employees",
        "founded_year", "founded_month", "founded_day", "deadpooled_year",
        "tag_list", "alias_list", "email_address", "phone_number", "description",
        "created_at", "updated_at", "overview"
    ]
    
    def random_value(field):
        if field in ["number_of_employees", "founded_year", "founded_month", "founded_day", "deadpooled_year"]:
            return random.randint(1, 1000)
        elif field in ["created_at", "updated_at"]:
            return datetime.now()
        else:
            return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10))
    
    query = {
        "$and": [
            {random.choice(fields): random_value(random.choice(fields))},
            {random.choice(fields): random_value(random.choice(fields))},
            {
                "$or": [
                    {random.choice(fields): random_value(random.choice(fields))},
                    {random.choice(fields): random_value(random.choice(fields))}
                ]
            },
            {
                "$and": [
                    {random.choice(fields): random_value(random.choice(fields))},
                    {random.choice(fields): random_value(random.choice(fields))}
                ]
            }
        ]
    }
    return query

def execute_random_queries(n=1000):
    for _ in range(n):
        query = generate_random_query()
        collection.find_one(query)


def create_test_indexes():
    collection.create_index([("name", 1)])
    collection.create_index([("permalink", 1)])
    collection.create_index([("crunchbase_url", 1)])
    collection.create_index([("homepage_url", 1)])
    collection.create_index([("name", 1), ("category_code", 1)])  # Equality on name, category_code
    collection.create_index([("founded_year", 1), ("number_of_employees", 1)])  # Equality on founded_year, range on number_of_employees
    collection.create_index([("homepage_url", 1), ("updated_at", -1)])  # Equality on homepage_url, sort on updated_at descending
    collection.create_index([("email_address", 1), ("created_at", 1)])  # Equality on email_address, range on created_at
    collection.create_index([("twitter_username", 1), ("founded_month", 1), ("founded_day", 1)])  # Equality on twitter_username, sort on founded_month, range on founded_day

def get_index_stats(collection_name):
    collection = db[collection_name]
    stats = collection.aggregate([{'$indexStats': {}}])
    stats_list = list(stats)
    return stats_list

def detect_unused_indexes(collection_name):
    index_stats = get_index_stats(collection_name)
    # Sort indexes by their access count
    sorted_indexes = sorted(index_stats, key=lambda x: x['accesses']['ops'])
    least_used_indexes = [index['name'] for index in sorted_indexes[:15]]
    unused_indexes = [index['name'] for index in index_stats if index['accesses']['ops'] == 0]
    combined_unused_indexes = list(set(unused_indexes + least_used_indexes))
    return combined_unused_indexes

def get_slow_queries():
    db.command("profile", 2, slowms=0)  # Log all queries
    slow_queries = db.system.profile.find({'millis': {'$gt': 1}})  
    slow_queries_list = list(slow_queries)
    return slow_queries_list

def suggest_indexes_from_queries(slow_queries):
    suggested_indexes = []
    for query in slow_queries:
        if 'command' in query and 'filter' in query['command']:
            filter_fields = query['command']['filter']
            equality_fields = []
            sort_fields = []
            range_fields = []
            
            for key, value in filter_fields.items():
                if isinstance(value, dict):
                    if '$eq' in value:
                        equality_fields.append(key)
                    elif any(op in value for op in ['$gt', '$gte', '$lt', '$lte']):
                        range_fields.append(key)
                elif isinstance(value, list) and key in ['$or', '$and']:
                    for sub_query in value:
                        for sub_key, sub_value in sub_query.items():
                            if isinstance(sub_value, dict):
                                if '$eq' in sub_value:
                                    equality_fields.append(sub_key)
                                elif any(op in sub_value for op in ['$gt', '$gte', '$lt', '$lte']):
                                    range_fields.append(sub_key)
                            else:
                                equality_fields.append(sub_key)
                else:
                    equality_fields.append(key)
            
            # Assuming sort fields are part of the query command
            if 'sort' in query['command']:
                sort_fields = list(query['command']['sort'].keys())
            
            # Combine fields following the ESR rule
            fields = equality_fields + sort_fields + range_fields
            fields = [field for field in fields if field not in ['$or', '$and']]  # Remove logical operators
            
            if fields:
                suggested_indexes.append({"fields": list(set(fields))})
    return suggested_indexes

# Placeholder dummy
def estimate_tradeoffs(index_suggestions):
    tradeoffs = []
    for suggestion in index_suggestions:
        tradeoffs.append({
            "fields": suggestion["fields"],
            "storage_cost": "estimated_storage_cost",
            "performance_gain": "estimated_performance_gain"
        })
    return tradeoffs

#Placeholder dummy
def estimate_tradeoffs(index_suggestions, unused_indexes):
    tradeoffs = []

    # Estimate trade-offs for removing unused indexes
    for index in unused_indexes:
        tradeoffs.append({
            "index": index,
            "action": "remove",
            "storage_cost": "reclaimed_storage_cost",
            "performance_gain": "write_performance_gain"
        })

    # Estimate trade-offs for adding suggested indexes
    for suggestion in index_suggestions:
        fields = suggestion["fields"]
        storage_cost = len(fields) * 100  # Example: 100 bytes per field
        
        # Placeholder logic for performance gain estimation
        performance_gain = len(fields) * 10  # Example: 10% improvement per field
        
        # Placeholder logic for write performance impact
        write_performance_impact = len(fields) * 5  # Example: 5% degradation per field
        
        tradeoffs.append({
            "fields": fields,
            "action": "add",
            "storage_cost": f"{storage_cost} bytes",
            "performance_gain": f"{performance_gain}%",
            "write_performance_impact": f"{write_performance_impact}%"
        })
    return tradeoffs

@app.route('/optimize/indexes', methods=['GET'])
def optimize_indexes():
    execute_random_queries(1000)  # Execute random queries to generate profiling  /
    create_test_indexes() 
    slow_queries = get_slow_queries()
    slow_query_count = len(slow_queries)
    unused_indexes = detect_unused_indexes('companies')
    suggested_indexes = suggest_indexes_from_queries(slow_queries)
    tradeoffs = estimate_tradeoffs(suggested_indexes, unused_indexes)
    
    index_stats = get_index_stats('companies')
    used_indexes = {index['name']: index['accesses']['ops'] for index in index_stats if index['accesses']['ops'] > 0}
    
    return jsonify({
        "slow_queries": slow_query_count,
        "used_indexes": used_indexes,
       "unused_indexes": unused_indexes,
        "suggested_indexes": suggested_indexes,
         "tradeoffs": tradeoffs
    })

if __name__ == '__main__':
    app.run(debug=True)