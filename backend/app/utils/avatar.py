import hashlib

def get_gravatar_url(email: str) -> str:
    """
    根据邮箱生成 Gravatar 头像链接 (Identicon 风格)
    """
    # 1. 去除空格并转小写
    clean_email = email.strip().lower()
    # 2. 计算 MD5
    email_hash = hashlib.md5(clean_email.encode('utf-8')).hexdigest()
    # 3. 拼接 URL (d=identicon 表示生成几何图案，s=200 表示尺寸)
    return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon&s=200"