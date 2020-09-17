from flask import Flask, request, g
import os
from flask_cors import CORS
from redisearch import Client, Query
import redis

server_port = os.getenv("SERVER_PORT", "8087");
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379");
redis_index = os.getenv("REDIS_INDEX", "idx:movie");

app = Flask(__name__)
CORS(app)


@app.before_request
def before_request():

    print("Configuration Index: "+redis_index+" - redisUrl: "+redis_url);

    g.redis = redis.from_url(redis_url);
    g.movieIdx = Client(
        redis_index,
        conn=g.redis
    );


@app.route('/')
def home():
    return {"status" : "Python REST Servicve is UP", "api" : "/api/1.0/search"}


@app.route('/api/1.0/movies/search')
def search():
    offset = 0;
    limit = 10;
    queryString = "";
    
    if (request.args.get('offset')):
        offset = int(request.args.get('offset'));

    if (request.args.get('limit')):
        limit = int(request.args.get('limit'));

    if (request.args.get('q')):
        queryString = request.args.get('q');


    q = Query(queryString).with_scores().paging(offset, limit);

    if (request.args.get('sortby')):
        ascending = True;
        if (request.args.get('ascending')):
            ascending = (request.args.get('ascending').lower() == "true" or request.args.get('ascending') == "1");
        
        q.sort_by(request.args.get('sortby'),asc=ascending);  


    searchResult = g.movieIdx.search(q);

    dictResult = {
        "meta" : {
            "totalResults" : getattr(searchResult, "total"), 
            "offset" : offset, 
            "limit" : limit, 
            "queryString" : queryString },
        "docs" : docs_to_dict(searchResult.docs)
        };
    
    return dictResult;

def docs_to_dict(docs):
    reslist = []
    for doc in docs:
        meta = { "id" : getattr(doc, "id"), "score" : getattr(doc, "score") }
        fields = {}
        for field in dir(doc):
            if (field.startswith('__') or field == 'id' or field == 'score'  ):
                continue
            fields.update({ field : getattr(doc, field) })
        ddict = { "meta" : meta , "fields" : fields };
        reslist.append(ddict)
    return reslist



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=server_port);



