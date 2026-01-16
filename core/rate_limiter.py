import time
from fastapi import HTTPException, Request, status
from core.redis import redis_client

# Lua script for atomic Token Bucket implementation
# KEYS[1]: Redis key for the user
# ARGV[1]: Refill rate (tokens per second)
# ARGV[2]: Bucket capacity
# ARGV[3]: Current timestamp
# ARGV[4]: TTL for the key (seconds)
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local refill_rate = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local ttl = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_updated')
local tokens = tonumber(bucket[1])
local last_updated = tonumber(bucket[2])

if not tokens then
    tokens = capacity
    last_updated = now
else
    local delta = math.max(0, now - last_updated)
    tokens = math.min(capacity, tokens + (delta * refill_rate))
    last_updated = now
end

if tokens >= 1 then
    tokens = tokens - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_updated', last_updated)
    redis.call('EXPIRE', key, ttl)
    return 1
else
    redis.call('HMSET', key, 'tokens', tokens, 'last_updated', last_updated)
    redis.call('EXPIRE', key, ttl)
    return 0
end
"""

class RateLimiter:
    def __init__(self, requests_per_minute: int, capacity: int = None):
        self.refill_rate = requests_per_minute / 60.0
        self.capacity = capacity or requests_per_minute
        self.ttl = 3600  # 1 hour idle timeout

    async def __call__(self, request: Request):
        if not redis_client:
            return  # Skip rate limiting if Redis is not available
            
        # Use client IP as the key. You could also use user ID if authenticated.
        client_ip = request.client.host
        key = f"rate_limit:{request.url.path}:{client_ip}"
        
        try:
            # Execute Lua script
            allowed = await redis_client.eval(
                TOKEN_BUCKET_LUA, 
                1, 
                key, 
                self.refill_rate, 
                self.capacity, 
                time.time(), 
                self.ttl
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later."
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            print(f"ERROR: Rate limiter Redis error: {e}")
            return # Fail open on Redis errors

# Convenience aliases for common limits
signup_limiter = RateLimiter(requests_per_minute=5)
login_limiter = RateLimiter(requests_per_minute=5)
otp_limiter = RateLimiter(requests_per_minute=3)
verify_limiter = RateLimiter(requests_per_minute=10)
password_limiter = RateLimiter(requests_per_minute=5)
