// PM2 进程管理配置
// 启动：pm2 start ecosystem.config.js
// 重载：pm2 reload bifurcation-backend
// 停止：pm2 stop bifurcation-backend
// 查看日志：pm2 logs bifurcation-backend

module.exports = {
  apps: [
    {
      name: 'bifurcation-backend',

      // 使用 venv 内的 Python 直接运行入口文件
      interpreter: './venv/bin/python',
      script: 'main.py',
      cwd: './backend',

      // 进程数：Python 单进程（uvicorn 内建 async，单进程已足够；
      // 如需多核并发，改用 uvicorn --workers N 启动方式，见下方注释）
      instances: 1,
      exec_mode: 'fork',

      // 环境变量（会覆盖 .env 文件中的同名值，用于区分部署环境）
      env: {
        APP_ENV: 'prod',
        BACKEND_HOST: '127.0.0.1',
        BACKEND_PORT: '8057',
      },

      // 崩溃自动重启
      autorestart: true,
      max_restarts: 10,          // 连续崩溃超过 10 次停止重启，避免死循环
      restart_delay: 3000,       // 每次重启等待 3 秒

      // 内存超限自动重启（根据实际负载调整）
      max_memory_restart: '512M',

      // 日志（写入 PM2 默认目录 ~/.pm2/logs/，无需手动建目录）
      // 查看：pm2 logs bifurcation-backend
      // 实时：pm2 logs bifurcation-backend --lines 200
      merge_logs: false,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

      // 优雅退出：收到 SIGINT 后最多等待 10 秒让 uvicorn 处理完在途请求
      kill_timeout: 10000,

      // 监听文件变化自动重启（生产环境建议关闭）
      watch: false,
    },
  ],
}

// ─────────────────────────────────────────────────────────────
// 多核部署备选方案（需要 uvicorn[standard] 或 gunicorn）
//
// 如果服务器核数 ≥ 4，可以改用 gunicorn + uvicorn worker：
//
//   interpreter: './venv/bin/gunicorn',
//   script: 'main:app',
//   cwd: './backend',
//   args: '-k uvicorn.workers.UvicornWorker -w 2 --bind 127.0.0.1:8057',
//   instances: 1,
//   exec_mode: 'fork',
//
// 或者保持 python main.py，在 main.py 里改 uvicorn.run(workers=2)。
// ─────────────────────────────────────────────────────────────
