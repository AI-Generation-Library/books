import http from 'k6/http';
import { check, sleep } from 'k6';

// Run only against the local mock. A valid token must be supplied by the learner.
export const options = {
  scenarios: {
    questions: {
      executor: 'constant-arrival-rate',
      rate: 2,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 10,
      maxVUs: 20,
    },
  },
  thresholds: { checks: ['rate>0.95'] },
};

export default function () {
  if (!__ENV.HUB_TOKEN || !__ENV.RUN_ID) {
    throw new Error('Set HUB_TOKEN and a unique RUN_ID');
  }
  const root = 'http://127.0.0.1:8000';
  const headers = {
    Authorization: `Bearer ${__ENV.HUB_TOKEN}`,
    'Content-Type': 'application/json',
    'Idempotency-Key': `${__ENV.RUN_ID}-${__VU}-${__ITER}`,
  };
  const response = http.post(`${root}/jobs`, JSON.stringify({ question: 'FastAPI' }), { headers });
  if (!check(response, { accepted: (r) => r.status === 202 })) return;
  const id = response.json('id');
  let terminal = false;
  for (let i = 0; i < 30; i++) {
    const status = http.get(`${root}/jobs/${id}`, { headers });
    const state = status.json('status');
    if (state === 'succeeded') { terminal = true; break; }
    if (state === 'failed') break;
    sleep(0.1);
  }
  check(terminal, { completed: (value) => value });
}
