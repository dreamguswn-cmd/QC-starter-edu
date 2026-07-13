/**
 * k6 성능·부하 테스트
 * 문서 기준: vus=3, duration=10s, 대상=/health
 * setup() → default() → teardown() 라이프사이클 사용
 *
 * 실행: k6 run performance/k6_test.js
 */
import http from 'k6/http';
import { check, sleep } from 'k6';

// ── 옵션 (문서 기준: vus=3, duration=10s) ─────────────────────
export const options = {
  vus: 20,
  duration: '10s',
  thresholds: {
    http_req_failed:   ['rate<0.01'],   // 오류율 1% 이하
    http_req_duration: ['p(95)<1000'],  // p95 1000ms 이하
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// ── 1단계: setup() — 테스트 준비 ────────────────────────────────
export function setup() {
  console.log('=== [setup] 성능 테스트 시작 준비 ===');
  const res = http.get(`${BASE_URL}/health`);
  if (res.status !== 200) {
    console.error(`서버 응답 이상: ${res.status}`);
  } else {
    console.log(`서버 상태 확인 완료: ${res.status} OK`);
  }
  return { base_url: BASE_URL };
}

// ── 2단계: default() — 부하 테스트 (health API 대상) ────────────
export default function (data) {
  // 문서 기준: health API를 대상으로 응답시간·성공률·실패율 측정
  const res = http.get(`${data.base_url}/health`);

  check(res, {
    'status 200':          (r) => r.status === 200,
    'status is ok':        (r) => r.json('status') === 'ok',
    'response time < 1s':  (r) => r.timings.duration < 1000,
  });

  sleep(0.1);  // 초당 약 10 req/VU → 3VU × 10s = 약 31건 예상
}

// ── 3단계: teardown() — 종료 처리 ───────────────────────────────
export function teardown(data) {
  console.log('=== [teardown] 성능 테스트 종료 ===');
  console.log(`대상 서버: ${data.base_url}`);
  console.log('결과: performance/results/ 에 저장하세요.');
}
