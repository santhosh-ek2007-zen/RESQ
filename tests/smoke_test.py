from app import create_app
import json

app = create_app()
print("App created OK")

client = app.test_client()

# Test /api/city
r = client.get('/api/city')
d = json.loads(r.data)
print(f"GET /api/city -> status={r.status_code}, nodes={len(d['nodes'])}, edges={len(d['edges'])}")

# Test /api/search with astar
r2 = client.post('/api/search',
    data=json.dumps({"algorithm":"astar","start":"A","destination":"K"}),
    content_type='application/json')
d2 = json.loads(r2.data)
print(f"POST /api/search astar A->K -> status={r2.status_code}, result_status={d2['status']}, cost={d2['total_cost']}, route={d2['route']}")

# Test /api/search with bfs
r3 = client.post('/api/search',
    data=json.dumps({"algorithm":"bfs","start":"A","destination":"K"}),
    content_type='application/json')
d3 = json.loads(r3.data)
print(f"POST /api/search bfs A->K -> status={r3.status_code}, result_status={d3['status']}, cost={d3['total_cost']}")

# Test block road
r4 = client.post('/api/roads/block',
    data=json.dumps({"source":"E","target":"H"}),
    content_type='application/json')
d4 = json.loads(r4.data)
print(f"POST /api/roads/block E-H -> status={r4.status_code}, version={d4['version']}")

# Test /api/optimise
r5 = client.post('/api/optimise',
    data=json.dumps({"algorithm":"simulated_annealing","base":"A","locations":["C","H","D"],"seed":42}),
    content_type='application/json')
d5 = json.loads(r5.data)
print(f"POST /api/optimise SA A base C,H,D -> status={r5.status_code}, result_status={d5['status']}, cost={d5['total_cost']}")

# Test unknown algorithm
r6 = client.post('/api/search',
    data=json.dumps({"algorithm":"unknown","start":"A","destination":"K"}),
    content_type='application/json')
print(f"POST /api/search unknown_algo -> status={r6.status_code}")

# Test /api/results.csv before benchmark
r7 = client.get('/api/results.csv')
print(f"GET /api/results.csv (no benchmark yet) -> status={r7.status_code}")

print("\nAll API smoke tests passed!")

