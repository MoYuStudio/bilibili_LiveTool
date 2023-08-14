
import json
import zlib
import time
import threading

import pyttsx3
import websocket

class DanmuReader:
    def __init__(self, roomid):
        self.roomid = roomid
        self.uri = "wss://broadcastlv.chat.bilibili.com/sub"
        self.data_raw = bytes.fromhex(self.encode(self.roomid))
        
        self.tts_engine_voice = 1
        self.tts_engine_rate = 180
        self.tts_engine_volume = 6
        self.reconnect_interval = 10  # 重新连接间隔时间（秒）
        
        self.ws = None

    def on_message(self, ws, message):
        self.decode(message)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("Connection closed.")
        self.reconnect()

    def on_open(self, ws):
        ws.send(self.data_raw)
        self.ws = ws
        # 在连接打开后设置定时器检查连接状态
        self.check_connection(ws)

    def check_connection(self, ws):
        if not ws.sock or not ws.sock.connected:
            print("Connection lost. Reconnecting...")
            self.reconnect()
        else:
            # 在一段时间后再次检查连接状态
            threading.Timer(self.reconnect_interval, self.check_connection, args=[ws]).start()

    def reconnect(self):
        print("Reconnecting...")
        self.ws.close()  # 关闭现有的连接
        # time.sleep(self.reconnect_interval)  # 等待一段时间，避免频繁重新连接
        self.run()  # 重新运行 WebSocket 连接
        pass
    def decode(self, data):
        packetLen = int(data[:4].hex(), 16)
        ver = int(data[6:8].hex(), 16)
        op = int(data[8:12].hex(), 16)

        if len(data) > packetLen:  # 防止
            self.decode(data[packetLen:])
            data = data[:packetLen]

        if ver == 2:
            data = zlib.decompress(data[16:])
            self.decode(data)
            return

        if op == 5:
            try:
                jd = json.loads(data[16:].decode('utf-8', errors='ignore'))

                if jd['cmd'] == 'SEND_GIFT':  # 礼物
                    print(str(jd["data"]["uname"]) + "赠送了 " + str(jd["data"]["giftName"]) + "X" + str(jd["data"]["num"]))
                    self.say_text(
                        "感谢" + str(jd["data"]["uname"]) + "赠送了" + str(jd["data"]["num"]) + "个" + str(
                            jd["data"]["giftName"]))

                elif jd['cmd'] == 'SUPER_CHAT_MESSAGE_JPN':  # sc醒目提醒
                    print(str(jd["data"]["user_info"]["uname"]) + ": " + str(jd["data"]["message"]))
                    self.say_text(
                        "SC留言" + str(jd["data"]["user_info"]["uname"]) + "说:" + str(jd["data"]["message"]))

                elif jd['cmd'] == 'DANMU_MSG':  # 普通弹幕消息
                    print(str(jd['info'][2][1]) + ": " + str(jd['info'][1]))
                    self.say_text(str(jd['info'][2][1]) + "说" + str(jd['info'][1]))

            except Exception as e:
                pass

    def encode(self, roomid):
        a = '{"roomid":' + str(roomid) + '}'
        data = []
        for s in a:
            data.append(ord(s))
        return "000000{}001000010000000700000001".format(hex(16 + len(data))[2:]) + "".join(
            map(lambda x: x[2:], map(hex, data)))

    def say_text(self, text):
        self.pyttsx3_engine = pyttsx3.init()
        self.pyttsx3_engine.setProperty('voice', self.tts_engine_voice)
        self.pyttsx3_engine.setProperty('rate', self.tts_engine_rate)
        self.pyttsx3_engine.setProperty('volume', self.tts_engine_volume)
        self.pyttsx3_engine.say(text)
        self.pyttsx3_engine.runAndWait()

    def run(self):
        # WebSocket 模块的调试输出
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(self.uri,
                                    on_message=lambda ws, message: self.on_message(ws, message),
                                    on_error=lambda ws, error: self.on_error(ws, error),
                                    on_close=lambda ws: self.on_close(ws))
        ws.on_open = lambda ws: self.on_open(ws)
        ws.run_forever()

if __name__ == '__main__':
    roomid = 545342
    bilibili_danmu = DanmuReader(roomid)
    bilibili_danmu.run()
