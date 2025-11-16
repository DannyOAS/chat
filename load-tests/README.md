# Load Testing with k6

This directory contains load testing scripts for ShoshChat AI using [k6](https://k6.io/).

## Installation

```bash
# macOS
brew install k6

# Linux
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Windows
choco install k6
```

## Running Tests

### Chat API Load Test

Tests the chat message endpoint with concurrent users:

```bash
k6 run chat-api.js

# With custom API URL
k6 run --env API_URL=https://api.shoshchat.ai chat-api.js
```

**Test Configuration:**
- Ramp up to 50 users over 1 minute
- Stay at 50 users for 3 minutes
- Ramp up to 100 users over 1 minute
- Stay at 100 users for 3 minutes
- Ramp down over 1 minute

**Thresholds:**
- 95% of requests complete in <500ms
- Less than 1% error rate

### Knowledge Upload Load Test

Tests the knowledge upload endpoint:

```bash
# Requires authentication token
k6 run --env AUTH_TOKEN=your_jwt_token knowledge-upload.js

# With custom API URL
k6 run --env API_URL=https://api.shoshchat.ai --env AUTH_TOKEN=your_jwt_token knowledge-upload.js
```

**Test Configuration:**
- Ramp up to 10 users over 30 seconds
- Stay at 10 users for 2 minutes
- Ramp down over 30 seconds

**Thresholds:**
- 95% of requests complete in <2000ms
- Less than 5% error rate

## Results

Results are saved to `load-test-results.json` and printed to stdout.

### Interpreting Results

**Key Metrics:**
- `http_req_duration`: Request response time
- `http_reqs`: Total number of requests
- `http_req_failed`: Failed request rate
- `checks`: Validation checks pass rate
- `vus`: Virtual users (concurrent load)

**Example Output:**
```
checks.........................: 100.00%
data_received..................: 1.2 MB
data_sent......................: 450 KB
http_req_duration..............: avg=234ms p(95)=420ms
http_reqs......................: 5432
vus............................: 100
```

## Cloud Testing

Run load tests from k6 Cloud for global distributed testing:

```bash
k6 cloud chat-api.js
```

## CI/CD Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/load-test.yml
name: Load Tests
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6
      - name: Run load tests
        run: k6 run load-tests/chat-api.js
```

## Performance Benchmarks

### Expected Performance

**Chat API:**
- Response time (p95): <500ms
- Throughput: 100+ req/s
- Concurrent users: 100+
- Error rate: <1%

**Knowledge Upload:**
- Response time (p95): <2000ms
- Throughput: 10+ req/s
- Concurrent users: 10+
- Error rate: <5%

### Bottleneck Identification

If tests fail thresholds, check:

1. **Database**: Add indexes, optimize queries
2. **Cache**: Ensure Redis is configured
3. **Application**: Profile with py-spy or cProfile
4. **Network**: Check for bandwidth limits
5. **Resources**: Scale workers, increase memory

## Custom Tests

Create custom load tests:

```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
};

export default function () {
  const res = http.get('http://localhost:8000/api/v1/endpoint/');
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
}
```
