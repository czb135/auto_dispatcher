import time
from playwright.sync_api import sync_playwright

# === 配置区域 ===
TEST_ORDERS = """
GFUS01020112309504
GFUS01020429434496
GFUS01020443773312
GFUS01020443776832
GFUS01020443777728
GFUS01020443777600
GFUS01020443781313
GFUS01020443788032
GFUS01020443785601
"""
TARGET_URL = "https://tools.uniuni.com:8065/"
# ================

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("1. 打开网页...")
        page.goto(TARGET_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        # --- 步骤 A: 选择仓库 ---
        print("2. 选择仓库 '18 - NJ Warehouse'...")
        try:
            page.get_by_role("combobox").first.click()
            time.sleep(0.5)
            page.keyboard.type("18 - NJ Warehouse")
            time.sleep(0.5)
            page.keyboard.press("Enter")
            print("   -> 仓库已选择")
        except Exception as e:
            print(f"   [!] 仓库选择报错: {e}")

        time.sleep(1)

        # --- 步骤 B: 填写订单号 (强力提交版) ---
        print("3. 填写订单号并强制 Apply...")
        try:
            # 这里的 .last 通常是准确的，因为 Streamlit 的文本域一般在页面较下方
            text_area = page.get_by_role("textbox").last
            if text_area.count() == 0:
                text_area = page.locator("textarea").first
            
            # 1. 清空并填入
            text_area.click()
            text_area.clear()
            text_area.fill(TEST_ORDERS.strip())
            print("   -> 文本已填入")
            time.sleep(0.5)

            # 2. 【关键】模拟 Streamlit 标准提交快捷键 Ctrl+Enter
            print("   -> 执行组合拳：按下 Control+Enter 提交...")
            text_area.press("Control+Enter")
            time.sleep(1)

            # 3. 【保险】按下 Tab 键切出焦点
            print("   -> 执行组合拳：按下 Tab 键移开焦点...")
            text_area.press("Tab")
            time.sleep(1)

            # 4. 【三重保险】点击页面顶部的标题区域
            print("   -> 执行组合拳：点击页面顶部...")
            page.locator("h1").first.click(timeout=2000) 
            # 如果找不到h1，这里也不会报错中断，只会跳过
            
            # 等待 Streamlit 右上角的 "Running" 状态结束
            print("   -> 等待 2 秒让后台同步状态...")
            time.sleep(2)

        except Exception as e:
            print(f"   [!] 填写订单号失败: {e}")

        # --- 步骤 C: 检查并点击按钮 ---
        print("4. 尝试点击 '开始日清'...")
        try:
            button = page.get_by_role("button", name="开始日清")
            
            if button.count() > 0:
                # 检查按钮是否被激活
                if button.is_disabled():
                    print("   [❌] 失败：按钮仍然是‘禁用’(Greyed out)状态。输入未生效。")
                else:
                    button.scroll_into_view_if_needed()
                    button.click()
                    print("   [✅] 成功！按钮已点击，流程跑通。")
            else:
                print("   [!] 未找到按钮，请确认页面是否还在加载。")

        except Exception as e:
            print(f"   [!] 点击按钮操作失败: {e}")

        print("\n------------------------------------------------")
        print("请观察：")
        print("按下 Ctrl+Enter 时，网页右上角那个小的 'Running' 动画动了吗？")
        print("------------------------------------------------")
        
        page.wait_for_timeout(30000)
        browser.close()

if __name__ == "__main__":
    run_test()