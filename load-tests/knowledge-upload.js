import http from 'k6/http';
import { check, sleep } from 'k6';
import { SharedArray } from 'k6/data';

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';

// Sample knowledge content
const sampleContent = new SharedArray('content', function () {
  return [
    'Our company operates from 9 AM to 5 PM, Monday through Friday.',
    'We offer a 30-day money-back guarantee on all products.',
    'Free shipping is available on orders over $50.',
    'Customer support is available via email and phone.',
    'We accept all major credit cards and PayPal.',
  ];
});

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '2m', target: 10 },   // Stay at 10 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% under 2s (uploads can be slower)
    http_req_failed: ['rate<0.05'],    // Less than 5% errors
  },
};

export default function () {
  const content = sampleContent[Math.floor(Math.random() * sampleContent.length)];

  const payload = JSON.stringify({
    title: `Test Knowledge ${__VU}-${Date.now()}`,
    content: content,
    source_type: 'text',
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${AUTH_TOKEN}`,
    },
  };

  const res = http.post(`${BASE_URL}/api/v1/knowledge/sources/`, payload, params);

  check(res, {
    'status is 201': (r) => r.status === 201,
    'has source id': (r) => r.json('id') !== undefined,
  });

  sleep(2); // Wait 2 seconds between uploads
}
