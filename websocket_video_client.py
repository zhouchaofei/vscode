import asyncio
import websockets
import json
import cv2
import base64
import numpy as np
import threading
import time
from queue import Queue

class WebSocketVideoClient:
    def __init__(self, server_url='ws://localhost:8765'):
        self.server_url = server_url
        self.display_queue = Queue(maxsize=5)
        self.running = False
        self.connected = False
        self.frame_count = 0
        
    def start_display_thread(self):
        """启动视频显示线程"""
        display_thread = threading.Thread(target=self.display_video)
        display_thread.daemon = True
        display_thread.start()
        
    def display_video(self):
        """显示视频帧"""
        cv2.namedWindow('RTSP Video Stream', cv2.WINDOW_AUTOSIZE)
        print("视频显示窗口已启动，按 'q' 键退出")
        
        fps_counter = 0
        fps_start_time = time.time()
        
        while self.running:
            try:
                if not self.display_queue.empty():
                    frame = self.display_queue.get(timeout=0.1)
                    
                    # 计算FPS
                    fps_counter += 1
                    current_time = time.time()
                    if current_time - fps_start_time >= 1.0:
                        fps = fps_counter / (current_time - fps_start_time)
                        fps_counter = 0
                        fps_start_time = current_time
                        
                        # 在图像上显示FPS
                        cv2.putText(frame, f'FPS: {fps:.1f}', (10, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # 显示连接状态
                    status_text = "Connected" if self.connected else "Disconnected"
                    status_color = (0, 255, 0) if self.connected else (0, 0, 255)
                    cv2.putText(frame, status_text, (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
                    
                    # 显示帧计数
                    cv2.putText(frame, f'Frame: {self.frame_count}', (10, 90), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                    
                    cv2.imshow('RTSP Video Stream', frame)
                    
                # 检查按键
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("用户按下 'q' 键，退出程序")
                    self.running = False
                    break
                    
            except Exception as e:
                print(f"显示视频时出错: {e}")
                
        cv2.destroyAllWindows()
        
    def decode_frame(self, frame_data):
        """解码视频帧"""
        try:
            # 解码base64
            img_data = base64.b64decode(frame_data)
            nparr = np.frombuffer(img_data, np.uint8)
            
            # 解码为OpenCV图像
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is not None:
                # 添加时间戳
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                cv2.putText(frame, timestamp, (10, frame.shape[0] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # 添加到显示队列
                if not self.display_queue.full():
                    self.display_queue.put(frame)
                else:
                    try:
                        self.display_queue.get_nowait()
                        self.display_queue.put(frame)
                    except:
                        pass
                        
                self.frame_count += 1
            else:
                print("无法解码视频帧")
                
        except Exception as e:
            print(f"解码帧时出错: {e}")
            
    async def connect_to_server(self):
        """连接到WebSocket服务器"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries and self.running:
            try:
                print(f"尝试连接到服务器: {self.server_url}")
                async with websockets.connect(self.server_url) as websocket:
                    self.connected = True
                    print("成功连接到视频流服务器")
                    
                    # 发送ping保持连接
                    ping_task = asyncio.create_task(self.send_ping(websocket))
                    
                    try:
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                message_type = data.get('type', 'unknown')
                                
                                if message_type == 'welcome':
                                    print(f"服务器欢迎消息: {data.get('message', '')}")
                                    
                                elif message_type == 'frame':
                                    frame_data = data.get('data', '')
                                    if frame_data:
                                        self.decode_frame(frame_data)
                                        
                                elif message_type == 'pong':
                                    # 收到pong响应
                                    pass
                                    
                            except json.JSONDecodeError:
                                print("收到无效的JSON消息")
                            except Exception as e:
                                print(f"处理消息时出错: {e}")
                                
                    except websockets.exceptions.ConnectionClosed:
                        print("服务器连接已断开")
                    finally:
                        ping_task.cancel()
                        self.connected = False
                        
            except websockets.exceptions.ConnectionRefused:
                retry_count += 1
                print(f"连接被拒绝，3秒后重试 ({retry_count}/{max_retries})")
                await asyncio.sleep(3)
            except Exception as e:
                retry_count += 1
                print(f"连接出错: {e}，3秒后重试 ({retry_count}/{max_retries})")
                await asyncio.sleep(3)
                
        if retry_count >= max_retries:
            print("达到最大重试次数，停止连接尝试")
            self.running = False
            
    async def send_ping(self, websocket):
        """定期发送ping保持连接"""
        try:
            while self.connected:
                ping_message = {
                    'type': 'ping',
                    'timestamp': time.time()
                }
                await websocket.send(json.dumps(ping_message))
                await asyncio.sleep(30)  # 每30秒发送一次ping
        except Exception as e:
            print(f"发送ping时出错: {e}")
            
    async def start_client(self):
        """启动客户端"""
        self.running = True
        
        # 启动显示线程
        self.start_display_thread()
        
        # 连接到服务器
        while self.running:
            await self.connect_to_server()
            if self.running:
                print("5秒后尝试重新连接...")
                await asyncio.sleep(5)
                
    def stop_client(self):
        """停止客户端"""
        self.running = False
        self.connected = False
        cv2.destroyAllWindows()
        
if __name__ == "__main__":
    # 配置服务器地址
    SERVER_URL = "ws://10.1.34.169:8765"
    
    client = WebSocketVideoClient(SERVER_URL)
    
    try:
        asyncio.run(client.start_client())
    except KeyboardInterrupt:
        print("\n客户端停止")
        client.stop_client()