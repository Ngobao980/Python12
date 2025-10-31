import random, requests, re, threading, time, secrets, os
from hashlib import md5
from time import time as T

# ===============================
# 🔧 Random Device + Build System
# ===============================

def random_device():
    '''Trả về thông tin ngẫu nhiên của một thiết bị Android phổ biến.'''
    devices = [
        ("Pixel 6", "TQ3A.230805.001"),
        ("Pixel 7 Pro", "UPB1.230309.014"),
        ("Samsung Galaxy S21", "SP1A.210812.016"),
        ("Samsung Galaxy S23 Ultra", "TP1A.220624.014"),
        ("Oppo Reno 8", "CPH2359_11.C.21"),
        ("Oppo Find X5", "CPH2307_11.A.19"),
        ("Xiaomi Mi 11", "RKQ1.200710.003"),
        ("Xiaomi 13 Pro", "TKQ1.221114.001"),
        ("Vivo V27", "PD2269F_EX_A_13.0.11.2.W30"),
        ("OnePlus 11", "NE2213_11.C.47"),
        ("Realme GT Neo 5", "RMX3708_11.A.22"),
        ("Asus ROG Phone 7", "WW_33.0820.0810.241"),
        ("Huawei P50 Pro", "HUAWEIP50Pro-C00B125")
    ]
    os_versions = ["12", "13", "14"]
    device, build = random.choice(devices)
    os_version = random.choice(os_versions)
    os_api = random.randint(26, 34)
    return device, os_version, os_api, build


def build_user_agents():
    '''Sinh ra danh sách User-Agent ngẫu nhiên dựa trên danh sách thiết bị.'''
    ua_templates = []
    for _ in range(15):
        device, os_version, _, build = random_device()
        ua = (f"com.ss.android.ugc.trill/400304 (Linux; U; Android {os_version}; vi_VN; "
              f"{device}; Build/{build}; Cronet/TTNetVersion:df66ad56)")
        ua_templates.append(ua)
    return ua_templates


# Danh sách UA động
ua_list = build_user_agents()


# ===============================
# 🔐 Tạo Signature cho request
# ===============================
class Signature:
    def __init__(self, params: str, data: str, cookies: str) -> None:
        self.params = params
        self.data = data
        self.cookies = cookies

    def hash(self, data: str) -> str:
        return str(md5(data.encode()).hexdigest())

    def calc_gorgon(self) -> str:
        g = self.hash(self.params)
        g += self.hash(self.data) if self.data else "0" * 32
        g += self.hash(self.cookies) if self.cookies else "0" * 32
        g += "0" * 32
        return g

    def get_value(self):
        return self.encrypt(self.calc_gorgon())

    def encrypt(self, data: str):
        unix = int(T())
        length = 0x14
        key = [
            0xDF, 0x77, 0xB9, 0x40, 0xB9, 0x9B, 0x84, 0x83, 0xD1, 0xB9,
            0xCB, 0xD1, 0xF7, 0xC2, 0xB9, 0x85, 0xC3, 0xD0, 0xFB, 0xC3
        ]
        pl = []
        for i in range(0, 12, 4):
            t = data[8 * i:8 * (i + 1)]
            for j in range(4):
                pl.append(int(t[j * 2:(j + 1) * 2], 16))
        pl.extend([0x0, 0x6, 0xB, 0x1C])
        H = int(hex(unix), 16)
        pl += [
            (H & 0xFF000000) >> 24,
            (H & 0x00FF0000) >> 16,
            (H & 0x0000FF00) >> 8,
            (H & 0x000000FF) >> 0,
        ]
        e = [a ^ b for a, b in zip(pl, key)]
        for i in range(length):
            C = self.reverse(e[i])
            D = e[(i + 1) % length]
            F = self.rbit(C ^ D)
            H = ((F ^ 0xFFFFFFFF) ^ length) & 0xFF
            e[i] = H
        r = "".join(self.hex_string(x) for x in e)
        return {"X-Gorgon": "840280416000" + r, "X-Khronos": str(unix)}

    def rbit(self, n):
        s = bin(n)[2:].zfill(8)
        return int(s[::-1], 2)

    def hex_string(self, n):
        s = hex(n)[2:]
        return s if len(s) == 2 else "0" + s

    def reverse(self, n):
        s = self.hex_string(n)
        return int(s[1:] + s[:1], 16)


# ===============================
# 🚀 Gửi view
# ===============================
os.system("cls" if os.name == "nt" else "clear")
link = input("Link Video/Ảnh TIKTOK: ")

try:
    m = re.search(r'/(?:video|photo)/(\d+)', link)
    if m:
        video_id = m.group(1)
        print(f"[+] Video/Photo ID: {video_id}")
    else:
        page = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).text
        m = re.search(r'"(video|photo)":\{"id":"(\d+)"', page)
        if m:
            video_id = m.group(2)
            print(f"[+] ID (từ HTML): {video_id}")
        else:
            print("[-] Không tìm thấy ID Video/Ảnh")
            exit(1)
except Exception as e:
    print(f"[-] Lỗi lấy ID: {e}")
    exit(1)


def send_view():
    '''Thread gửi lượt view liên tục.'''
    device_type, os_version, os_api, build = random_device()
    params = (
        f"channel=googleplay&aid=1233&app_name=musical_ly&version_code=400304&device_platform=android"
        f"&device_type={device_type.replace(' ', '+')}&os_version={os_version}"
        f"&build={build}&device_id={random.randint(600000000000000, 699999999999999)}"
        f"&os_api={os_api}&app_language=vi&tz_name=Asia%2FHo_Chi_Minh"
    )
    url = f"https://api16-core-c-alisg.tiktokv.com/aweme/v1/aweme/stats/?{params}"
    cookies = {"sessionid": secrets.token_hex(8)}

    while True:
        data = {"item_id": video_id, "play_delta": 1, "action_time": int(time.time())}
        sig = Signature(params=params, data=str(data), cookies=str(cookies)).get_value()
        headers = {
            "Host": "api16-core-c-alisg.tiktokv.com",
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": random.choice(ua_list),
            "Sdk-Version": "2",
            "Passport-Sdk-Version": "19",
            "X-SS-DP": "1233",
            "X-Khronos": sig["X-Khronos"],
            "X-Gorgon": sig["X-Gorgon"],
        }
        try:
            r = requests.post(url, data=data, headers=headers, cookies=cookies, timeout=10)
            if "application/json" in r.headers.get("Content-Type", ""):
                resp = r.json()
                print(f"✅ View | code={resp.get('status_code')}")
            else:
                print(f"⚠️ Error: {r.text[:80]}...")
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            time.sleep(2)

        time.sleep(random.uniform(0.3, 1.2))


# ===============================
# 🧵 Tạo Threads
# ===============================
threads = []
for i in range(500):
    t = threading.Thread(target=send_view)
    t.daemon = True
    t.start()
    threads.append(t)

for t in threads:
    t.join()
