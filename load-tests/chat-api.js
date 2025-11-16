import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Ramp up to 50 users
    { duration: '3m', target: 50 },   // Stay at 50 users
    { duration: '1m', target: 100 },  // Ramp up to 100 users
    { duration: '3m', target: 100 },  // Stay at 100 users
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],     // Less than 1% errors
    errors: ['rate<0.1'],               // Less than 10% errors
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

// Generate test user ID
const userId = `load-test-user-${__VU}-${Date.now()}`;

export default function () {
  // Test chat endpoint
  const chatPayload = JSON.stringify({
    message: 'What are your business hours?',
    user_id: userId,
  });

  const chatParams = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const chatRes = http.post(`${BASE_URL}/api/v1/chat/message/`, chatPayload, chatParams);

  const chatSuccess = check(chatRes, {
    'chat status is 200': (r) => r.status === 200,
    'chat response time < 500ms': (r) => r.timings.duration < 500,
    'chat has response': (r) => r.json('response') !== undefined,
  });

  errorRate.add(!chatSuccess);

  sleep(1); // Wait 1 second between iterations
}

export function handleSummary(data) {
  return {
    'load-test-results.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function textSummary(data, options) {
  // Generate summary text
  const indent = options.indent || '';
  const enableColors = options.enableColors || false;

  let summary = '\n';
  summary += `${indent}checks.........................: ${formatPercentage(data.metrics.checks.values.passes / data.metrics.checks.values.count)}\n`;
  summary += `${indent}data_received..................: ${formatBytes(data.metrics.data_received.values.count)}\n`;
  summary += `${indent}data_sent......................: ${formatBytes(data.metrics.data_sent.values.count)}\n`;
  summary += `${indent}http_req_duration..............: avg=${formatDuration(data.metrics.http_req_duration.values.avg)} p(95)=${formatDuration(data.metrics.http_req_duration.values['p(95)'])}\n`;
  summary += `${indent}http_reqs......................: ${data.metrics.http_reqs.values.count}\n`;
  summary += `${indent}vus............................: ${data.metrics.vus.values.value}\n`;

  return summary;
}

function formatPercentage(value) {
  return `${(value * 100).toFixed(2)}%`;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

function formatDuration(ms) {
  return `${ms.toFixed(2)}ms`;
}
