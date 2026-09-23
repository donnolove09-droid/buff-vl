import aiohttp
import asyncio

API_VISIT_BASE = "https://sowi-visit-api-today-api.vercel.app"
API_LIKE_BASE  = "https://like-api-by-ajay-one-last.vercel.app"
SPAM_API       = "https://new-spam-ind-six.vercel.app"

DEFAULT_REGION = "ind"   # đổi nếu bạn muốn region khác
TIMEOUT = aiohttp.ClientTimeout(total=40)


async def _get_json(url: str) -> dict:
    last_err = None
    for _ in range(2):
        try:
            async with aiohttp.ClientSession(timeout=TIMEOUT) as s:
                async with s.get(url) as r:
                    return await r.json(content_type=None)
        except Exception as e:
            last_err = e
            await asyncio.sleep(1)
    raise RuntimeError(str(last_err))


async def do_like(region: str, uid: str) -> dict:
    try:
        r = await _get_json(f"{API_LIKE_BASE}/like?uid={uid}&server_name={region}")
        ok = r.get("status") == 1
        return {
            "name": "LIKE",
            "ok": ok,
            "nickname": r.get("PlayerNickname", "-"),
            "detail": f"Before: {r.get('LikesbeforeCommand','-')} | "
                      f"After: {r.get('LikesafterCommand','-')} | "
                      f"Given: {r.get('LikesGivenByAPI','-')}",
        }
    except Exception as e:
        return {"name": "LIKE", "ok": False, "detail": f"Lỗi: {e}"}


async def do_visit(region: str, uid: str) -> dict:
    try:
        r = await _get_json(f"{API_VISIT_BASE}/visit?uid={uid}&region={region}")
        return {
            "name": "VISIT",
            "ok": True,
            "nickname": r.get("PlayerNickname", "-"),
            "detail": f"Success: {r.get('SuccessfulVisits',0)} | "
                      f"Failed: {r.get('FailedVisits',0)} | "
                      f"Total: {r.get('TotalVisits',0)}",
        }
    except Exception as e:
        return {"name": "VISIT", "ok": False, "detail": f"Lỗi: {e}"}


async def do_spam(region: str, uid: str) -> dict:
    try:
        r = await _get_json(f"{SPAM_API}/spam?uid={uid}&server_name={region}")
        if not r or "friend_requests" not in r:
            return {"name": "SPAM", "ok": False, "detail": "Không tìm thấy UID"}
        fr = r["friend_requests"]
        return {
            "name": "SPAM",
            "ok": True,
            "nickname": r.get("PlayerNickname", uid),
            "detail": f"Success: {fr.get('successful',0)} | "
                      f"Failed: {fr.get('failed',0)} | "
                      f"Total: {fr.get('total',0)}",
        }
    except Exception as e:
        return {"name": "SPAM", "ok": False, "detail": f"Lỗi: {e}"}


async def buff_all(region: str, uid: str) -> dict:
    """Chạy cả 3 cùng lúc."""
    like, visit, spam = await asyncio.gather(
        do_like(region, uid),
        do_visit(region, uid),
        do_spam(region, uid),
    )
    nickname = next((x["nickname"] for x in (like, visit, spam)
                     if x.get("nickname") and x["nickname"] != "-"), uid)
    return {
        "uid": uid,
        "region": region.upper(),
        "nickname": nickname,
        "results": [like, visit, spam],
    }
