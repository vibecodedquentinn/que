from app.integrations import fritzbox as fb


async def list_fritz_hosts() -> str:
    return await fb.list_hosts()


async def fritz_internet_status() -> str:
    return await fb.internet_status()


async def fritz_guest_wifi(action: str) -> str:
    return await fb.guest_wifi(action)
