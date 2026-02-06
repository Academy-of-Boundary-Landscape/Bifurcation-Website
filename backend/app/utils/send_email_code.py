# 发送邮件验证码


async def send_email_code(email: str, code: str) -> None:
    """
    模拟发送邮件验证码的功能。在生产环境中，应集成实际的邮件服务。
    """
    # 模拟发送邮件的逻辑
    try:
        print(f"Sending email to {email} with code: {code}")
        # 这里可以集成实际的邮件发送服务，例如 SMTP、SendGrid、Amazon SES 等
    except Exception as e:
        print(f"Failed to send email to {email}: {e}")
        raise