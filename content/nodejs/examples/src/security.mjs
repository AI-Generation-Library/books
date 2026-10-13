import { randomBytes, scrypt as scryptCallback, timingSafeEqual, createHash } from 'node:crypto';
import { promisify } from 'node:util';
import { HttpError } from './errors.mjs';
const scrypt = promisify(scryptCallback);
// scrypt-v1: N=2^15, r=8, p=3. 저장 포맷 버전으로 향후 재해시를 구분한다.
const options = { N: 32768, r: 8, p: 3, maxmem: 64 * 1024 * 1024 };
let hashing = 0;
async function derive(password, salt) {
  if (hashing >= 2) throw new HttpError(503, 'AUTH_BUSY', '잠시 후 다시 시도하세요.');
  hashing++;
  try { return await scrypt(password, salt, 64, options); }
  finally { hashing--; }
}
export function credentials(body) {
  const email = body?.email;
  const password = body?.password;
  if (typeof email !== 'string' || email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ||
      typeof password !== 'string' || [...password].length < 12 || Buffer.byteLength(password) > 128) {
    throw new HttpError(400, 'INVALID_CREDENTIALS', '이메일과 12자 이상, 128바이트 이하 비밀번호가 필요합니다.');
  }
  return { email: email.trim().toLowerCase(), password };
}
export async function hashPassword(password) {
  const salt = randomBytes(16).toString('hex');
  const key = await derive(password, salt);
  return `scrypt-v1:${salt}:${key.toString('hex')}`;
}
export async function checkPassword(password, hash) {
  const [format, salt, encoded] = hash.split(':');
  if (format !== 'scrypt-v1') throw new Error('Unsupported password hash');
  const actual = await derive(password, salt);
  const expected = Buffer.from(encoded, 'hex');
  return expected.length === actual.length && timingSafeEqual(expected, actual);
}
export const tokenHash = token => createHash('sha256').update(token).digest('hex');
export const newToken = () => randomBytes(32).toString('base64url');

// 메모리 데모용 제한기. 여러 인스턴스에서는 공유 저장소/게이트웨이로 대체한다.
export function limiter({ max = 100, windowMs = 60_000, maxKeys = 10_000 } = {}) {
  const windows = new Map();
  return (req, res, next) => {
    const now = Date.now();
    for (const [key, entry] of windows) if (entry.until <= now) windows.delete(key);
    const key = req.ip;
    let entry = windows.get(key);
    if (!entry) {
      if (windows.size >= maxKeys) return next(new HttpError(503, 'LIMITER_CAPACITY', '잠시 후 다시 시도하세요.'));
      entry = { count: 0, until: now + windowMs }; windows.set(key, entry);
    }
    if (++entry.count > max) {
      res.set('Retry-After', String(Math.max(1, Math.ceil((entry.until - now) / 1000))));
      return next(new HttpError(429, 'RATE_LIMIT', '요청이 너무 많습니다.'));
    }
    next();
  };
}
