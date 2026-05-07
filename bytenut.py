import time
import os
import json
import re
import random
import requests

# ================= 环境配置 =================
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":1"

if "XAUTHORITY" not in os.environ:
    if os.path.exists("/home/headless/.Xauthority"):
        os.environ["XAUTHORITY"] = "/home/headless/.Xauthority"

print(f"[DEBUG] Env DISPLAY: {os.environ.get('DISPLAY')}")
print(f"[DEBUG] Env XAUTHORITY: {os.environ.get('XAUTHORITY')}")

from seleniumbase import SB

# ================= 配置区域 =================
PROXY_URL = os.getenv("PROXY", "")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
ACCOUNTS = os.getenv("ACCOUNTS", "")

URL_LOGIN_PANEL = "https://www.bytenut.com/auth/login"


# ================= 解析多账号 =================
def parse_accounts(accounts_str):
    accounts = []

    if not accounts_str:
        return accounts

    for item in accounts_str.split("|"):
        try:
            u, p, n, a = item.split(",")
            accounts.append((u.strip(), p.strip(), n.strip(), a.strip()))
        except:
            print(f"[WARN] 格式错误: {item}")

    return accounts


# ================= 主类 =================
class BytenutRenewal:

    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.screenshot_dir = os.path.join(self.BASE_DIR, "artifacts")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.results = []

    def log(self, msg):
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] [INFO] {msg}", flush=True)

    # ================= TG =================
    def send_telegram_notify(self, message, photo_path=None):

        if not TG_TOKEN or not TG_CHAT_ID:
            self.log("⚠️ 未配置 TG，跳过")
            return

        try:
            if photo_path and os.path.exists(photo_path):
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                with open(photo_path, "rb") as f:
                    requests.post(
                        url,
                        data={"chat_id": TG_CHAT_ID, "caption": message},
                        files={"photo": f}
                    )
            else:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                requests.post(
                    url,
                    data={"chat_id": TG_CHAT_ID, "text": message}
                )

        except Exception as e:
            self.log(f"TG失败: {e}")

    # ================= 截图 =================
    def step_shot(self, sb, username, step_name):
        try:
            ts = int(time.time())
            shot = os.path.join(
                self.screenshot_dir,
                f"{username}_{step_name}_{ts}.png"
            )

            sb.save_screenshot(shot)
            self.send_telegram_notify(f"📸 {username} | {step_name}", shot)
            self.log(f"📸 已发送截图: {step_name}")

        except Exception as e:
            self.log(f"⚠️ 截图失败: {e}")

    # ================= 剩余时间 =================
    def get_remaining_time(self, sb):
        remaining_text = "未知"

        try:
            sb.wait_for_element_visible("div.countdown-clock", timeout=15)
            time.sleep(2)

            raw_text = sb.get_text("div.countdown-clock")
            match = re.search(r"\d{1,2}:\d{2}", raw_text)

            if match:
                remaining_text = match.group(0)
            else:
                remaining_text = raw_text.strip()

        except Exception as e:
            self.log(f"⚠️ 获取剩余时间失败: {e}")

        return remaining_text

    # ================= 主流程 =================
    def run(self):

        timestamp = time.strftime('%H:%M:%S')
        self.log(f"🚀 开始执行 ByteNut 保活 {timestamp}")

        accounts = parse_accounts(ACCOUNTS)

        if not accounts:
            self.log("❌ 没有账号")
            return

        self.log(f"🚀 共 {len(accounts)} 个账号")

        for idx, (USERNAME, PASSWORD, NUM, AREA) in enumerate(accounts, 1):

            URL_SERVER_PANEL = f"https://www.bytenut.com/free-gamepanel/{NUM}"

            self.log("=" * 60)
            self.log(f"🚀 [{idx}] 开始账号: {USERNAME} | Server {NUM}")
            self.log("=" * 60)

            with SB(
                uc=True,
                test=True,
                headed=True,
                headless=False,
                xvfb=False,
                chromium_arg="--no-sandbox,--disable-dev-shm-usage,--disable-gpu,--window-position=0,0,--start-maximized",
                proxy=PROXY_URL if PROXY_URL else None
            ) as sb:

                try:

                    # ================= IP检测 =================
                    self.log("🌍 检测IP...")

                    try:
                        sb.open("https://api.ipify.org?format=json")
                        ip_val = json.loads(
                            re.search(r'\{.*\}', sb.get_text("body")).group(0)
                        ).get("ip", "Unknown")

                        parts = ip_val.split(".")
                        self.log(f"IP: {parts[0]}.{parts[1]}.***.{parts[-1]}")

                    except:
                        self.log("⚠️ IP跳过")

                    # ================= 登录 =================
                    self.log("📂 打开登录页")
                    sb.uc_open_with_reconnect(URL_LOGIN_PANEL, reconnect_time=5)

                    time.sleep(5)

                    try:
                        sb.uc_gui_click_captcha()
                        sb.uc_gui_handle_captcha()
                    except:
                        pass

                    time.sleep(5)

                    #self.step_shot(sb, USERNAME, "登录页")

                    # ================= Cookie =================
                    cookie_btns = [
                        '//button[contains(., "Continue with Recommended Cookies")]',
                        '//button[contains(., "Recommended Cookies")]',
                        '//button[contains(., "Accept")]',
                        '//button[contains(., "I Agree")]',
                        '//button[contains(., "Consent")]',
                        '//button[contains(., "Got it")]',
                    ]

                    for btn in cookie_btns:
                        if sb.is_element_present(btn):
                            try:
                                sb.click(btn)
                                self.log("🍪 已关闭 Cookie")
                                break
                            except:
                                pass

                    #self.step_shot(sb, USERNAME, "已关闭 Cookie")

                    sb.type('input[placeholder="Username"]', USERNAME)
                    sb.type('input[placeholder="Password"]', PASSWORD)

                    #self.step_shot(sb, USERNAME, "账号密码填写完毕")

                    sb.click('//button[contains(., "Sign In")]')
                    time.sleep(10)

                    # ================= 服务器 =================
                    sb.uc_open_with_reconnect(URL_SERVER_PANEL, reconnect_time=6)
                    time.sleep(10)

                    sb.click('//li[contains(., "RENEW SERVER")]')
                    #self.step_shot(sb, USERNAME, "已点击 RENEW SERVER 按钮进入续费页面")
                    time.sleep(5)

                    try:
                        sb.uc_gui_click_captcha()
                        sb.uc_gui_handle_captcha()
                    except:
                        pass

                    time.sleep(5)
                    
                    # ================= Extend Time =================
                    self.log("🖱️ 检查 Extend Time 状态...")

                    extend_selector = '//button[contains(., "Extend")]'

                    try:
                        if sb.is_element_present(extend_selector):

                            if sb.is_element_enabled(extend_selector):

                                sb.click(extend_selector)
                                self.log("➡️ 已点击 Extend")
                                #self.step_shot(sb, USERNAME, "已点击 Extend 按钮")

                                time.sleep(2)

                                watch_ad_bonus_selector = (
                                    '//button[contains(., "Watch Ad") and contains(., "+180")]'
                                )

                                sb.wait_for_element_visible(watch_ad_bonus_selector, timeout=20)
                                sb.click(watch_ad_bonus_selector)
                                #self.step_shot(sb, USERNAME, "已点击 Watch Ad +180min 按钮")

                                time.sleep(3)

                                # 点击 Watch Ad
                                sb.execute_script("""
                                    var btn = document.querySelector('div.adsterra-rewarded-dialog button.el-button--primary');
                                    if(btn) btn.click();
                                """)
                                time.sleep(3)
                                #self.step_shot(sb, USERNAME, "已点击 Watch Ad 按钮")
            
                                main_window = sb.driver.current_window_handle
                                existing_windows = sb.driver.window_handles

                                new_windows = sb.driver.window_handles

                                if len(new_windows) > len(existing_windows):
                                    for w in new_windows:
                                        if w not in existing_windows:
                                            sb.driver.switch_to.window(w)
                                            time.sleep(3)
                                            sb.driver.close()
                                            break

                                sb.driver.switch_to.window(main_window)
                                #self.step_shot(sb, USERNAME, "已关闭广告页")

                                time.sleep(3)

                                sb.execute_script("""
                                    var btn = document.querySelector('div.adsterra-rewarded-dialog button.el-button--success');
                                    if(btn) btn.click();
                                """)
                                time.sleep(5)
                                
                                #self.step_shot(sb, USERNAME, "已点击 Claim Reward 按钮")

                                remaining_text = self.get_remaining_time(sb)
                                self.log(f"🕒 剩余时间: {remaining_text}")

                        #self.step_shot(sb, USERNAME, "已记录服务器剩余时间")

                        remaining_text = self.get_remaining_time(sb)

                        self.results.append(
                            f"✅ 续期成功 | 账号: {USERNAME} | 服务器区域: {AREA} | 服务器剩余可运行时间: {remaining_text}"
                        )

                    else:
                        self.log("⏳ 冷却中")
                        # ===== 新增：冷却也获取 =====
                        time.sleep(2)
                        remaining_text = self.get_remaining_time(sb)
                        self.log(f"🕒 剩余时间: {remaining_text}")

                        self.results.append(
                        f"⏳ 冷却 | 账号: {USERNAME} | 服务器区域: {AREA} | 服务器剩余可运行时间: {remaining_text}"
                        )
                        continue

                    except Exception as e:
                        self.log(f"❌账号 {USERNAME} Extend失败 : {e}")

                except Exception as e:
                    self.log(f"❌ 账号 {USERNAME} 续期失败 : {e}")

        self.log("📊 生成最终汇总...")
        self.send_telegram_notify("\n".join(self.results))
        self.log("✅ TG汇总已发送")


# ================= 启动 =================
if __name__ == "__main__":
    BytenutRenewal().run()
