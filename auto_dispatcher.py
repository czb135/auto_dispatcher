import streamlit as st
import pandas as pd
import time
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# ================= 配置区域 =================
TARGET_URL = "https://tools.uniuni.com:8065/"
WAREHOUSE_OPTION = "18 - NJ Warehouse"

# ================= 核心自动化函数 (Worker) =================
def process_batch(batch_id, orders_list, headless_mode=True):
    """
    单个机器人的工作逻辑 (V4: 超长待机版)
    """
    log_prefix = f"[批次 #{batch_id}]"
    start_time = time.time()
    
    try:
        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(headless=headless_mode)
            context = browser.new_context()
            # 设置默认超时时间为 0 (无限)，防止脚本内部某些操作默认30s超时
            context.set_default_timeout(0) 
            page = context.new_page()
            
            # --- 1. 打开网页 ---
            try:
                page.goto(TARGET_URL, timeout=120000) # 加载网页给 2 分钟
                page.wait_for_load_state("networkidle")
                time.sleep(random.uniform(2.0, 5.0))
            except Exception as e:
                browser.close()
                return False, f"{log_prefix} ❌ 网页加载失败", 0

            # --- 2. 选择仓库 ---
            try:
                page.wait_for_selector('role=combobox', state="visible", timeout=30000)
                page.get_by_role("combobox").first.click()
                time.sleep(0.5)
                page.keyboard.type(WAREHOUSE_OPTION)
                time.sleep(0.5)
                page.keyboard.press("Enter")
            except Exception as e:
                browser.close()
                return False, f"{log_prefix} ❌ 选仓失败 (可能页面未加载完)", 0

            time.sleep(1)

            # --- 3. 填写订单 ---
            try:
                orders_text = "\n".join([str(o) for o in orders_list])
                
                text_area = page.get_by_role("textbox").last
                if text_area.count() == 0:
                    text_area = page.locator("textarea").first
                
                text_area.click()
                text_area.clear()
                text_area.fill(orders_text)
                
                # 组合拳提交
                time.sleep(0.5)
                text_area.press("Control+Enter")
                time.sleep(0.5)
                text_area.press("Tab")
                
                # 点击标题移开焦点
                try:
                    page.locator("h1").first.click(timeout=1000)
                except:
                    pass
                
                # 动态等待：输入后稍微缓一下
                time.sleep(5) 

            except Exception as e:
                browser.close()
                return False, f"{log_prefix} ❌ 填单失败: {str(e)}", 0

            # --- 4. 点击并长时等待 ---
            start_btn = page.get_by_role("button", name="开始日清")
            
            # 智能重试点击逻辑
            if start_btn.count() > 0 and start_btn.is_disabled():
                time.sleep(1)
                if start_btn.is_disabled():
                    text_area.focus()
                    text_area.press("Control+Enter")
                    time.sleep(2)
            
            try:
                if start_btn.count() > 0 and not start_btn.is_disabled():
                    start_btn.scroll_into_view_if_needed()
                    start_btn.click()
                    
                    # === V4 关键修改 ===
                    # 设置等待时间为 20 分钟 (1,200,000 毫秒)
                    # 只要 20 分钟内出现了结果，就算成功
                    long_timeout = 20 * 60 * 1000 
                    
                    try:
                        # 等待 "外部API已处理" 文字出现
                        page.wait_for_selector("text=外部API已处理", timeout=long_timeout)
                        
                        # 尝试获取具体的成功信息
                        success_msg = "处理完成"
                        try:
                            el = page.locator("text=外部API已处理").first
                            success_msg = el.inner_text()
                        except:
                            pass
                        
                        browser.close()
                        duration = time.time() - start_time
                        # 将秒转换为分钟显示，更直观
                        duration_str = f"{duration/60:.1f}分钟"
                        return True, f"{log_prefix} ✅ {success_msg} (耗时: {duration_str})", len(orders_list)
                        
                    except Exception as e:
                        browser.close()
                        return False, f"{log_prefix} ⏳ 等待超时(超过20分钟)，请检查后台", 0
                    
                else:
                    browser.close()
                    return False, f"{log_prefix} ⚠️ 按钮禁用，输入未生效", 0
            except Exception as e:
                browser.close()
                return False, f"{log_prefix} ❌ 运行出错: {str(e)}", 0

    except Exception as e:
        return False, f"{log_prefix} 💥 浏览器崩溃: {str(e)}", 0


# ================= 前端界面逻辑 =================
def main():
    st.set_page_config(page_title="UniUni EWR936 日清助手", page_icon="🐢", layout="wide")
    
    st.title("UniUni EWR936批量日清助手")
    st.markdown("### 专门针对慢速后端优化：每个批次最长等待 20 分钟")
    
    st.sidebar.header("⚙️ 运行配置")
    
    # 既然处理很慢，建议并发别开太高，稳定为主
    num_workers = st.sidebar.slider("并发窗口数量", 1, 40, 15, 
                                help="M3 Max 建议设置 12-20 个")
    
    batch_size = st.sidebar.number_input("单次处理单量", 
                                         min_value=10, max_value=2000, value=500, step=100)
    
    visible_mode = st.sidebar.checkbox("显示浏览器界面", value=True)
    headless = not visible_mode

    uploaded_file = st.file_uploader("📂 上传 Excel 文件", type=["xlsx"])
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            
            tno_col = None
            for col in df.columns:
                if "TNO" in str(col).strip().upper():
                    tno_col = col
                    break
            
            if tno_col:
                all_orders = df[tno_col].astype(str).tolist()
                all_orders = [x for x in all_orders if x and x.lower() != 'nan' and len(x) > 3]
                total_orders = len(all_orders)
                
                st.success(f"✅ 读取成功！共 **{total_orders}** 个订单。")
                
                if st.button("🔥 开始长效处理"):
                    batches = [all_orders[i:i + batch_size] for i in range(0, total_orders, batch_size)]
                    total_batches = len(batches)
                    
                    st.info(f"💡 提示：由于单次处理需要约 10 分钟，进度条更新会比较慢，请耐心等待。不要关闭此网页。")
                    st.write(f"📊 任务队列: **{total_batches}** 批 | 并发: **{num_workers}** | 单批超时上限: **20分钟**")
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    total_success_orders = 0
                    completed_batches = 0
                    
                    with st.expander("📝 运行日志 (最新的在最上面)", expanded=True):
                        log_placeholder = st.empty()
                        logs = []

                    with ThreadPoolExecutor(max_workers=num_workers) as executor:
                        future_to_batch = {
                            executor.submit(process_batch, i+1, batch_data, headless): i 
                            for i, batch_data in enumerate(batches)
                        }
                        
                        for future in as_completed(future_to_batch):
                            success, msg, count = future.result()
                            completed_batches += 1
                            
                            color = "green" if success else "red"
                            if "超时" in msg: color = "orange"
                            
                            logs.insert(0, f"<span style='color:{color}'>{msg}</span>")
                            log_placeholder.markdown("<br>".join(logs[:50]), unsafe_allow_html=True)
                            
                            if success:
                                total_success_orders += count
                            
                            prog = completed_batches / total_batches
                            progress_bar.progress(prog)
                            status_text.markdown(f"**进度:** {completed_batches}/{total_batches} 批次 | **成功上传:** {total_success_orders} 单")

                    if total_success_orders == total_orders:
                        st.balloons()
                        st.success("🎉 所有批次处理完成！")
                    else:
                        st.warning(f"⚠️ 处理结束。详情请查看日志。")
            
            else:
                st.error("❌ 未找到 TNO 列。")

        except Exception as e:
            st.error(f"文件错误: {e}")

if __name__ == "__main__":
    main()