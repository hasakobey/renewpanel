from contextvars import ContextVar

current_user_id=ContextVar("current_user_id",default=None)
current_username=ContextVar("current_username",default="SYSTEM")
current_ip=ContextVar("current_ip",default="")
