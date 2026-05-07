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

            accounts.append((
                u.strip(),
                p.strip(),
                n.strip(),
                a.strip()
            ))

        except:
            print(f"[WARN] 格式错误: {item}")

    return accounts


# ================= 主类 =================
class BytenutRenewal:

    def __init__(self):

        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        self.screenshot_dir = os.path.join(
            self.BASE_DIR,
            "artifacts"
        )

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
                        data={
                            "chat_id": TG_CHAT_ID,
                            "caption": message
                        },
                        files={"photo": f}
                    )

            else:

                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"

                requests.post(
                    url,
                    data={
                        "chat_id": TG_CHAT_ID,
                        "text": message
                    }
                )

        except Exception as e:
            self.log(f"TG失败: {e}")

    # ================= 步骤截图 =================
    def step_shot(self, sb, username, step_name):

        try:

            ts = int(time.time())

            shot = os.path.join(
                self.screenshot_dir,
                f"{username}_{step_name}_{ts}.png"
            )

            sb.save_screenshot(shot)

            self.send_telegram_notify(
                f"📸 {username} | {step_name}",
                shot
            )

            self.log(f"📸 已发送截图: {step_name}")

        except Exception as e:
            self.log(f"⚠️ 截图失败: {e}")

    # ================= 获取剩余时间 =================
    def get_remaining_time(self, sb):

        remaining_text = "未知"

        try:

            sb.wait_for_element_visible(
                "div.countdown-clock",
                timeout=15
            )

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

    def run(self):

        timestamp = time.strftime('%H:%M:%S')

        self.log(f"🚀 开始执行 ByteNut 保活 {timestamp}")

        accounts = parse_accounts(ACCOUNTS)

        if not accounts:
            self.log("❌ 没有账号")
            return

        self.log(f"🚀 共 {len(accounts)} 个账号")

        for idx, (USERNAME, PASSWORD, NUM, AREA) in enumerate(accounts, 1):

            URL_SERVER_PANEL = (
                f"https://www.bytenut.com/free-gamepanel/{NUM}"
            )

            self.log("=" * 60)

            self.log(
                f"🚀 [{idx}] 开始账号: {USERNAME} | Server {NUM}"
            )

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

                    self.log("📂 打开登录页")

                    sb.uc_open_with_reconnect(
                        URL_LOGIN_PANEL,
                        reconnect_time=5
                    )

                    time.sleep(5)

                    sb.wait_for_element_visible(
                        'input[placeholder="Username"]',
                        timeout=25
                    )

                    sb.type(
                        'input[placeholder="Username"]',
                        USERNAME
                    )

                    sb.type(
                        'input[placeholder="Password"]',
                        PASSWORD
                    )

                    sb.click('//button[contains(., "Sign In")]')

                    time.sleep(10)

                    sb.uc_open_with_reconnect(
                        URL_SERVER_PANEL,
                        reconnect_time=6
                    )

                    time.sleep(10)

                    sb.click('//li[contains(., "RENEW SERVER")]')

                    time.sleep(5)

                    # ================= Extend =================
                    extend_selector = '//button[contains(., "Extend")]'

                    if sb.is_element_present(extend_selector):

                        if sb.is_element_enabled(extend_selector):

                            sb.click(extend_selector)

                            time.sleep(2)

                            watch_ad_bonus_selector = (
                                '//button[contains(., "Watch Ad") and contains(., "+180")]'
                            )

                            sb.wait_for_element_visible(
                                watch_ad_bonus_selector,
                                timeout=20
                            )

                            sb.click(watch_ad_bonus_selector)

                            time.sleep(3)

                            # ===== Watch Ad window =====
                            original_window = sb.driver.current_window_handle

                            if len(sb.driver.window_handles) > 1:
                                for handle in sb.driver.window_handles:
                                    if handle != original_window:
                                        sb.driver.switch_to.window(handle)
                                        break

                                time.sleep(12)

                                if len(sb.driver.window_handles) > 1:
                                    sb.driver.close()

                                sb.driver.switch_to.window(original_window)

                            # =======================
                            # 🔥 修复点：Claim Reward（已重写）
                            # =======================

                            self.log("🎁 点击 Claim Reward（修复版）")

                            claim_selector = (
                                '//button[contains(@class,"el-button--success")]'
                                '//span[contains(text(),"Claim Reward")]'
                                '/ancestor::button'
                            )

                            try:
                                sb.wait_for_element_visible(claim_selector, timeout=25)
                            except:
                                pass

                            time.sleep(2)

                            try:
                                sb.js_click(claim_selector)
                            except:
                                try:
                                    sb.click(claim_selector)
                                except:
                                    sb.execute_script("""
                                        let btns = [...document.querySelectorAll('button.el-button--success')];
                                        for (let b of btns) {
                                            if (b.innerText.includes('Claim Reward')) {
                                                b.click();
                                                break;
                                            }
                                        }
                                    """)

                            self.log("🎁 Claim Reward 已尝试点击完成")

                            time.sleep(3)

                            remaining_text = self.get_remaining_time(sb)

                            self.log(f"🕒 剩余时间: {remaining_text}")

                            self.results.append(
                                f"✅ 成功 | {USERNAME} | {AREA} | {remaining_text}"
                            )

                        else:
                            self.log("⏳ 冷却中")

                    else:
                        self.log("⚠️ 未找到 Extend")

                except Exception as e:
                    self.log(f"❌ 失败 {USERNAME}: {e}")

                    self.results.append(
                        f"❌ 失败 | {USERNAME} | {e}"
                    )

        self.log("📊 汇总")

        final_msg = "\n".join(self.results)

        self.send_telegram_notify(final_msg)

        self.log("✅ 完成")


# ================= 启动 =================
if __name__ == "__main__":
    BytenutRenewal().run()
