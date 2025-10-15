# MD2_SleepCode

Transfinitte MongoDB 2 SOLUTION - MongoDB Index Optimization Tool

## Required Software
- Python 3.x
- MongoDB (running on localhost:27017)

## Python Dependencies
```sh
pip install flask flask_cors pymongo
```

## How to Run
1. Start MongoDB on your system
2. Run the application:
```sh
python app.py
```
3. Access the web interface by opening `index.html` in your browser

## Features
- Analyzes MongoDB index usage
- Detects unused indexes
- Suggests optimizations based on query patterns
- Estimates storage and performance trade-offs
- Simple web interface for interaction

## API Endpoints

### Get Index Analysis
```
GET /optimize/indexes
```

### Add New Index
```
POST /add_index
Body: {"fields": ["field1", "field2"]}
```

### Remove Index
```
POST /remove_index
Body: {"index_name": "index_name_here"}
```

## Project Files
- `app.py` - Backend server code
- `index.html` - Frontend interface
- `script.js` - Frontend logic
