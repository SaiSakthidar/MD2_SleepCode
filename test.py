from pymongo import MongoClient
from flask import Flask, jsonify, request
from flask_cors import CORS
import time
import random
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client['sai']
collection = db['companies']

app = Flask(__name__)
CORS(app)  # Enable CORS

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
    collection.create_index([("blog_url", 1)])
    collection.create_index([("blog_feed_url", 1)])
    collection.create_index([("twitter_username", 1)])
    collection.create_index([("category_code", 1)])
    collection.create_index([("number_of_employees", 1)])
    collection.create_index([("founded_year", 1)])
    collection.create_index([("founded_month", 1)])
    collection.create_index([("founded_day", 1)])
    collection.create_index([("deadpooled_year", 1)])
    collection.create_index([("tag_list", 1)])
    collection.create_index([("alias_list", 1)])
    collection.create_index([("email_address", 1)])
    collection.create_index([("phone_number", 1)])
    collection.create_index([("description", 1)])
    collection.create_index([("created_at", 1)])
    collection.create_index([("updated_at", 1)])
    collection.create_index([("overview", 1)])
    
    # Compound indexes following the ESR Rule
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

def get_index_storage_size(collection_name):
    coll_stats = db.command("collStats", collection_name)
    index_sizes = coll_stats.get("indexSizes", {})
    return index_sizes

def detect_unused_indexes(collection_name):
    index_stats = get_index_stats(collection_name)
    index_sizes = get_index_storage_size(collection_name)
    
    # Sort indexes by their access count
    sorted_indexes = sorted(index_stats, key=lambda x: x['accesses']['ops'])
    least_used_indexes = [index['name'] for index in sorted_indexes[:6]]
    unused_indexes = [index['name'] for index in index_stats if index['accesses']['ops'] == 0]
    combined_unused_indexes = list(set(unused_indexes + least_used_indexes))
    
    # Calculate usage-to-storage ratio using access count
    usage_to_storage_ratio = {}
    for index in index_stats:
        index_name = index['name']
        access_count = index['accesses']['ops']
        storage_size = index_sizes.get(index_name, 0) / 1024  # Convert bytes to KB
        if access_count > 0:
            ratio = storage_size / access_count
        else:
            ratio = storage_size  # If access count is zero, use storage size directly
        usage_to_storage_ratio[index_name] = ratio
    
    # Normalize the ratio to be in the range of 1-10
    min_ratio = min(usage_to_storage_ratio.values())
    max_ratio = max(usage_to_storage_ratio.values())
    for index_name in usage_to_storage_ratio:
        if max_ratio != min_ratio:
            normalized_ratio = 1 + 9 * (usage_to_storage_ratio[index_name] - min_ratio) / (max_ratio - min_ratio)
        else:
            normalized_ratio = 1  # If all ratios are the same, set to 1
        usage_to_storage_ratio[index_name] = normalized_ratio
    
    return combined_unused_indexes, usage_to_storage_ratio

def get_slow_queries():
    db.command("profile", 2, slowms=100)  # Log queries taking longer than 100 milliseconds
    slow_queries = db.system.profile.find({'millis': {'$gt':0.85}})  # Filter for queries taking longer than 100 milliseconds
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

def estimate_index_storage(index_fields):
    # Generate a sample query that would use the new index
    sample_query = {field: {"$exists": True} for field in index_fields}
    
    # Use the explain command to get the query plan
    explain_plan = collection.find(sample_query).explain()
    
    # Extract the estimated index size from the query plan
    index_size = explain_plan.get('executionStats', {}).get('totalKeysExamined', 0)
    
    # Convert the index size to KB
    index_size_kb = index_size / 1024
    
    return index_size_kb

def estimate_tradeoffs(index_suggestions, unused_indexes, usage_to_storage_ratio, index_sizes):
    tradeoffs = []

    # Estimate trade-offs for removing unused indexes
    for index in unused_indexes:
        storage_size = index_sizes.get(index, 0) / 1024  # Convert bytes to KB
        ratio = usage_to_storage_ratio.get(index, 0)
        tradeoffs.append({
            "index": index,
            "action": "remove",
            "storage_saved": f"{storage_size:.2f} KB",  # Format to 2 decimal places
            "performance_measure": f"{ratio:.6f}"  # Only the normalized ratio number
        })

    # Estimate trade-offs for adding suggested indexes
    for suggestion in index_suggestions:
        fields = suggestion["fields"]
        
        # Estimate storage cost using the estimate_index_storage function
        storage_cost = estimate_index_storage(fields)
        
        # Estimate performance gain based on the number of fields and their types
        performance_gain = len(fields) * 5  # Example: 5% improvement per field
        
        tradeoffs.append({
            "index": ", ".join(fields),
            "action": "add",
            "storage_extra_required": f"{storage_cost:.2f} KB",  # Format to 2 decimal places
            "performance_measure": f"estimated performance gain: {performance_gain}%"
        })
    return tradeoffs

@app.route('/optimize/indexes', methods=['GET'])
def optimize_indexes():
    execute_random_queries(1000)  # Execute random queries to generate profiling data
    create_test_indexes()  # Create additional indexes for testing
    
    slow_queries = get_slow_queries()
    slow_query_count = len(slow_queries)  # Count of slow queries
    unused_indexes, usage_to_storage_ratio = detect_unused_indexes('companies')
    index_sizes = get_index_storage_size('companies')
    suggested_indexes = suggest_indexes_from_queries(slow_queries)
    tradeoffs = estimate_tradeoffs(suggested_indexes, unused_indexes, usage_to_storage_ratio, index_sizes)
    
    index_stats = get_index_stats('companies')
    used_indexes = {index['name']: index['accesses']['ops'] for index in index_stats if index['accesses']['ops'] > 0}
    
    return jsonify({
        "slow_queries": slow_query_count,
        "used_indexes": used_indexes,
        "unused_indexes": unused_indexes,
        "suggested_indexes": suggested_indexes,
        "tradeoffs": tradeoffs  # Include tradeoffs in the response
    })

@app.route('/add_index', methods=['POST'])
def add_index():
    data = request.json
    fields = data.get('fields')
    if fields:
        collection.create_index([(field, 1) for field in fields])
        return jsonify({"status": "success", "message": "Index added successfully"}), 200
    return jsonify({"status": "error", "message": "Invalid fields"}), 400

@app.route('/remove_index', methods=['POST'])
def remove_index():
    data = request.json
    index_name = data.get('index_name')
    if index_name:
        collection.drop_index(index_name)
        return jsonify({"status": "success", "message": "Index removed successfully"}), 200
    return jsonify({"status": "error", "message": "Invalid index name"}), 400

if __name__ == '__main__':
    app.run(debug=True)