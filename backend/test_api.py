import requests
import json
import random
import string
import sys

class TreeStoryAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token = None
        self.user_info = None
        self.current_book_id = None
        self.current_node_id = None
        
        # 生成随机测试账号
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        self.email = f"admin@secret-sealing.club"
        self.password = "114514"
        self.username = f"BFV"
        
        print(f"[*] 初始化测试环境: {self.base_url}")
        print(f"[*] 准备测试用户: {self.email} / {self.username}")

    def log(self, message, is_success=True):
        status = "✅" if is_success else "❌"
        print(f"{status} {message}")
        if not is_success:
            sys.exit(1)

    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # ==========================
    # 1. 认证模块 (Auth)
    # ==========================

    def register(self):
        """注册新用户"""
        url = f"{self.base_url}/api/v1/auth/register"
        payload = {
            "email": self.email,
            "username": self.username,
            "password": self.password
        }
        resp = self.session.post(url, json=payload)
        
        if resp.status_code == 200:
            self.user_info = resp.json()
            self.log("注册成功")
        else:
            print(resp.text)
            self.log(f"注册失败: {resp.status_code}", False)

    def send_code(self):
        """发送验证码"""
        url = f"{self.base_url}/api/v1/auth/send-code"
        # 注意：这里只传 email 和 code 字段，但实际上请求体只需 email，
        # 不过根据 API 文档 schema 是 EmailVerify，包含 code。
        # 通常 send-code 不需要传 code，但为了符合文档 schema 我们传个空的或者 dummy
        payload = {"email": self.email, "code": "000000"} 
        resp = self.session.post(url, json=payload)
        
        if resp.status_code == 200:
            self.log("验证码发送请求成功 (Mock环境)")
        else:
            self.log(f"验证码发送失败: {resp.status_code}", False)

    def verify_email(self):
        """验证邮箱 (Mock验证码: 114514)"""
        url = f"{self.base_url}/api/v1/auth/verify-email"
        payload = {
            "email": self.email,
            "code": "114514"  # 文档指定的 Mock 验证码
        }
        resp = self.session.post(url, json=payload)
        
        if resp.status_code == 200:
            self.log("邮箱验证成功")
        else:
            self.log(f"邮箱验证失败: {resp.status_code}", False)

    def login(self):
        """登录获取 Token"""
        url = f"{self.base_url}/api/v1/auth/login"
        # OAuth2 form request 格式
        data = {
            "username": self.email,  # 文档指出：username 字段填 email
            "password": self.password
        }
        # 注意：这里通常 Content-Type 是 application/x-www-form-urlencoded
        resp = self.session.post(url, data=data)
        
        if resp.status_code == 200:
            data = resp.json()
            self.token = data["access_token"]
            self.log(f"登录成功，Token: {self.token[:10]}...")
        else:
            self.log(f"登录失败: {resp.status_code}", False)

    def get_me(self):
        """获取个人信息"""
        url = f"{self.base_url}/api/v1/auth/me"
        resp = self.session.get(url, headers=self._get_headers())
        if resp.status_code == 200:
            self.log("获取个人信息成功")
            # print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
        else:
            self.log(f"获取个人信息失败: {resp.status_code}", False)

    # ==========================
    # 2. 故事书模块 (Book)
    # ==========================

    def setup_book(self):
        """
        获取或创建故事书。
        注意：创建需要 Admin 权限。如果注册的用户是普通用户，
        这里会尝试创建失败，然后回退到读取现有列表。
        """
        # 尝试创建 (Admin Only)
        create_url = f"{self.base_url}/api/v1/story/books"
        payload = {
            "title": "API自动测试故事集",
            "description": "这是由自动化脚本创建或读取的测试集",
            "cover_image": "http://example.com/cover.jpg"
        }
        resp = self.session.post(create_url, json=payload, headers=self._get_headers())
        
        if resp.status_code == 200:
            book = resp.json()
            self.current_book_id = book['id']
            self.log(f"创建故事书成功 ID: {self.current_book_id}")
            return

        # 如果创建失败（可能是403权限不足），则尝试读取列表
        self.log(f"无法创建故事书 (Code {resp.status_code})，尝试读取现有列表...")
        
        get_url = f"{self.base_url}/api/v1/story/books?skip=0&limit=10"
        resp = self.session.get(get_url)
        
        if resp.status_code == 200:
            books = resp.json()
            if books:
                self.current_book_id = books[0]['id']
                self.log(f"读取到现有故事书 ID: {self.current_book_id}")
            else:
                self.log("系统中没有可用的故事书，无法进行后续测试", False)
        else:
            self.log("读取故事书列表失败", False)

    # ==========================
    # 3. 节点创作模块 (Node)
    # ==========================

    def create_node(self):
        """提交续写节点"""
        if not self.current_book_id:
            self.log("跳过节点创建：无 Book ID", False)
            return

        url = f"{self.base_url}/api/v1/story/node"
        payload = {
            "book_id": self.current_book_id,
            "parent_id": None, # 尝试创建根节点，或者你可以填具体的ID
            "title": f"测试章节 {random.randint(1, 1000)}",
            "content": "这是一个由Python自动化脚本生成的精彩故事片段，内容必须超过十个字符。",
            "branch_name": "主线"
        }
        
        resp = self.session.post(url, json=payload, headers=self._get_headers())
        
        if resp.status_code == 200:
            node = resp.json()
            self.current_node_id = node['id']
            self.log(f"创建节点成功 ID: {self.current_node_id} (Status: {node.get('status')})")
        elif resp.status_code == 422:
            # 可能是验证错误，比如 parent_id 必填或者无效
            # 如果是422，我们尝试获取一下树，找个节点挂载
            self.log("创建根节点可能受限或参数错误，尝试获取现有树寻找父节点...")
            self._try_create_child_node()
        else:
            self.log(f"创建节点失败: {resp.text}", False)

    def _try_create_child_node(self):
        """辅助方法：如果不能创建根节点，找一个现有的节点进行续写"""
        tree_url = f"{self.base_url}/api/v1/story/tree?book_id={self.current_book_id}"
        resp = self.session.get(tree_url, headers=self._get_headers()) # 需认证看全部，或不认证看公开
        
        # 这是一个简化处理，假设返回结构是列表或包含列表
        # 实际上根据 API 描述，这里可能返回一个树状结构或列表
        # 我们假设无法解析直接跳过，实际需要根据真实返回结构遍历
        self.log("尝试读取树结构以寻找父节点 (Mock逻辑，实际需解析JSON结构)", True)
        # 这里仅作演示，如果无法创建根节点，测试可能在此中断
        pass

    def get_node_detail(self):
        """获取节点详情"""
        if not self.current_node_id:
            return
        
        url = f"{self.base_url}/api/v1/story/node/{self.current_node_id}"
        resp = self.session.get(url, headers=self._get_headers())
        
        if resp.status_code == 200:
            self.log("获取节点详情成功")
        else:
            self.log(f"获取节点详情失败: {resp.status_code}")

    # ==========================
    # 4. 互动模块 (Interaction)
    # ==========================

    def toggle_like(self):
        """测试点赞"""
        if not self.current_node_id:
            return
            
        url = f"{self.base_url}/api/v1/interaction/node/{self.current_node_id}/like"
        resp = self.session.post(url, headers=self._get_headers())
        
        if resp.status_code == 200:
            self.log("点赞/取消点赞操作成功")
        else:
            self.log(f"点赞操作失败: {resp.status_code}")

    def create_comment(self):
        """测试评论"""
        if not self.current_node_id:
            return
            
        url = f"{self.base_url}/api/v1/interaction/node/{self.current_node_id}/comment"
        payload = {"content": "这是一条非常棒的自动测试评论！"}
        
        resp = self.session.post(url, json=payload, headers=self._get_headers())
        
        if resp.status_code == 200:
            self.log("发布评论成功")
        else:
            self.log(f"发布评论失败: {resp.status_code}")

    def get_comments(self):
        """获取评论列表"""
        if not self.current_node_id:
            return
            
        url = f"{self.base_url}/api/v1/interaction/node/{self.current_node_id}/comments"
        resp = self.session.get(url)
        
        if resp.status_code == 200:
            comments = resp.json()
            self.log(f"获取评论列表成功，当前数量: {len(comments)}")
        else:
            self.log(f"获取评论列表失败: {resp.status_code}")

    def get_notifications(self):
        """获取通知"""
        url = f"{self.base_url}/api/v1/interaction/notifications"
        resp = self.session.get(url, headers=self._get_headers())
        
        if resp.status_code == 200:
            self.log("获取通知列表成功")
        else:
            self.log(f"获取通知列表失败: {resp.status_code}")

    # ==========================
    # 执行流程
    # ==========================
    def run_all(self):
        print("=== 开始综合 API 测试 ===")
        
        # 1. 认证流程
        #self.register()
        #self.send_code()
        #self.verify_email()
        self.login()
        self.get_me()
        
        print("\n--- 认证测试完成，开始业务测试 ---")
        
        # 2. 故事书
        self.setup_book()
        
        # 3. 节点
        self.create_node()
        self.get_node_detail()
        
        # 4. 互动
        if self.current_node_id:
            self.toggle_like()
            self.create_comment()
            self.get_comments()
        
        # 5. 用户其他
        self.get_notifications()
        
        print("\n=== 所有测试执行完毕 ===")

if __name__ == "__main__":
    # 可以通过命令行参数修改 host，例如: python test_api.py http://127.0.0.1:8000
    host = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8057"
    
    tester = TreeStoryAPITester(base_url=host)
    try:
        tester.run_all()
    except Exception as e:
        print(f"\n❌ 发生未捕获异常: {e}")