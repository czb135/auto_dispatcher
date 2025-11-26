import json
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        # 1. 启动浏览器（headless=False 让你可以看到界面并进行交互）
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 2. 定义监听函数：只打印 POST 请求，这通常是提交数据的请求
        def handle_request(request):
            # 过滤掉一些无关的静态资源请求，只关注可能的 API 调用
            if request.method == "POST" and request.resource_type in ["fetch", "xhr"]:
                print("-" * 50)
                print(f"【发现 POST 请求】")
                print(f"URL: {request.url}")
                
                # 尝试获取并打印请求体（Payload），即你粘贴的订单号可能出现的地方
                try:
                    post_data = request.post_data
                    if post_data:
                        # 如果太长（比如4万个订单），只打印前500个字符用于确认
                        print(f"Payload (前500字符): {post_data[:500]}")
                    else:
                        print("Payload: (无内容)")
                except Exception as e:
                    print(f"读取 Payload 出错: {e}")
                
                # 打印 Headers，这是后续模拟请求时伪造身份的关键
                print("Headers:")
                for k, v in request.headers.items():
                    print(f"  {k}: {v}")
                print("-" * 50)

        # 3. 绑定监听器
        page.on("request", handle_request)

        # 4. 打开目标网页
        print("正在打开网页，请在打开的浏览器窗口中登录并进行操作...")
        page.goto("https://tools.uniuni.com:8065/")

        # 5. 保持脚本运行，直到你完成操作
        # 你可以在浏览器中：
        #   1. 选择仓库
        #   2. 粘贴少量的测试订单号（建议先用 5-10 个测试，方便观察）
        #   3. 点击“开始日清”
        #   4. 观察控制台输出
        print("等待用户操作... (按 Ctrl+C 结束脚本)")
        try:
            page.wait_for_timeout(300000) # 等待 5 分钟，足够你操作了
        except KeyboardInterrupt:
            print("停止抓包")

        browser.close()

if __name__ == "__main__":
    run()