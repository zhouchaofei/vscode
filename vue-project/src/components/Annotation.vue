<template>
  <div class="annotator-container">
    <canvas ref="videoCanvas" class="background-canvas"></canvas>
    
    <canvas
      ref="annotationCanvas"
      class="annotation-canvas-layer"
      @mousemove="handleCanvasMouseMove"
      :style="{ cursor: canvasCursor }"
    ></canvas>

    <div class="ui-overlay">
      <header class="app-header">
        <h1>智慧监管平台</h1>
        <div class="connection-status">
          <div class="status-indicator" :class="{ connected: isConnected }"></div>
          <span>{{ connectionStatus }}</span>
        </div>
      </header>

      <main class="main-content">
        <div v-if="hoveredAnnotation" class="details-popup" :style="{ top: popupPosition.y + 'px', left: popupPosition.x + 'px' }">
          <h4>{{ hoveredAnnotation.title }}</h4>
          <p>{{ hoveredAnnotation.details }}</p>
        </div>
      </main>

      <div class="view-controls">
        <button @click="switchView('view_1')" class="view-btn">视角1</button>
        <button @click="switchView('view_2')" class="view-btn">视角2</button>
        <button @click="switchView('view_3')" class="view-btn">视角3</button>
        <button @click="switchView('view_4')" class="view-btn">视角4</button>
        <button @click="switchView('view_5')" class="view-btn">视角5</button>
        <button @click="switchView('view_6')" class="view-btn">视角6</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

// --- Canvas 和状态管理 ---
const videoCanvas = ref(null);
const annotationCanvas = ref(null);
let videoCtx = null;
let annotationCtx = null;

const annotations = ref([]); // 保存来自后端的标注数据
const hoveredAnnotation = ref(null); // 保存当前鼠标悬停的标注
const popupPosition = ref({ x: 0, y: 0 }); // 详情弹出框的位置
const canvasCursor = ref('default'); // 用于在悬停时将光标变为'pointer'

// 不同标注类型的颜色映射
const typeColors = {
  '盖梁': '#FFA500', // 橙色
  '桥墩': '#FFD700', // 黄色
  '通道': '#32CD32', // 绿色
  '匝道': '#1E90FF', // 蓝色
  '方向': '#FF4500'  // 红色
};

// --- WebSocket 和连接状态 ---
const socket = ref(null);
const isConnected = ref(false);
const connectionStatus = ref("未连接");

// --- 组件生命周期钩子 ---
onMounted(() => {
  initCanvas();
  connectWebSocket();
  fetchAnnotations(); // 组件加载时获取标注
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  handleDisconnect("组件已卸载");
  window.removeEventListener('resize', handleResize);
});

// --- Canvas 和绘制 ---
const initCanvas = () => {
  const container = document.querySelector('.annotator-container');
  if (!container) return;
  const { clientWidth: width, clientHeight: height } = container;

  // 设置两个canvas的尺寸相同
  [videoCanvas, annotationCanvas].forEach(canvasRef => {
    if(canvasRef.value) {
      canvasRef.value.width = width;
      canvasRef.value.height = height;
    }
  });
  
  videoCtx = videoCanvas.value.getContext('2d');
  annotationCtx = annotationCanvas.value.getContext('2d');
  
  drawAnnotations(); // 窗口大小调整时重绘标注
};

// CHANGE: 优化了handleResize，现在只进行重绘，不再重新获取数据
const handleResize = () => {
    initCanvas(); // initCanvas 会重设画布大小并调用 drawAnnotations
}

/**
 * 将 `annotations` ref 中存储的所有标注绘制到画布上。
 */
const drawAnnotations = () => {
  if (!annotationCtx) return;
  // 获取当前画布的实时尺寸
  const currentCanvasWidth = annotationCtx.canvas.width;
  const currentCanvasHeight = annotationCtx.canvas.height;
  
  annotationCtx.clearRect(0, 0, currentCanvasWidth, currentCanvasHeight);

  annotations.value.forEach(anno => {
    const color = typeColors[anno.type] || '#FFFFFF'; 
    const coordinates = anno.coordinates;
    
    // 检查是否存在必要的尺寸信息
    if (!coordinates || coordinates.length < 2 || !anno.imageWidth || !anno.imageHeight) return;

    // --- NEW: 核心修改：计算缩放比例 ---
    const scaleX = currentCanvasWidth / anno.imageWidth;
    const scaleY = currentCanvasHeight / anno.imageHeight;
    // ------------------------------------

    annotationCtx.lineWidth = 3;
    annotationCtx.strokeStyle = color;
    annotationCtx.fillStyle = `${color}4D`; // 30% 透明度填充

    annotationCtx.beginPath();

    // CHANGE: 对每个坐标点应用缩放比例
    const startX = coordinates[0].x * scaleX;
    const startY = coordinates[0].y * scaleY;
    annotationCtx.moveTo(startX, startY);

    for (let i = 1; i < coordinates.length; i++) {
      const nextX = coordinates[i].x * scaleX;
      const nextY = coordinates[i].y * scaleY;
      annotationCtx.lineTo(nextX, nextY);
    }

    annotationCtx.closePath();
    annotationCtx.stroke();
    annotationCtx.fill();

    // CHANGE: 对文本位置同样应用缩放
    annotationCtx.fillStyle = '#FFFFFF';
    annotationCtx.font = 'bold 16px Arial';
    annotationCtx.textBaseline = 'top';
    const textX = startX + 10; // 在缩放后的坐标基础上偏移
    const textY = startY + 10;
    annotationCtx.fillText(anno.title, textX, textY);
  });
};


// --- 后端数据与交互 ---

/**
 * 建议的后端响应JSON结构：
 * [
 * {
 * "id": "anno_001",
 * "type": "桥墩",
 * "title": "主桥墩 #A1",
 * "details": "承重结构，建于2022年，混凝土强度C50。",
 * "coordinates": [
 * { "x": 150, "y": 400 },
 * { "x": 250, "y": 420 },
 * { "x": 260, "y": 600 },
 * { "x": 160, "y": 580 }
 * ]
 * },
 * {
 * "id": "anno_002",
 * "type": "盖梁",
 * "title": "盖梁 #B2",
 * "details": "钢结构，2023年进行过安全检查。",
 * "coordinates": [
 * { "x": 100, "y": 350 },
 * { "x": 800, "y": 370 },
 * { "x": 790, "y": 410 },
 * { "x": 90, "y": 390 }
 * ]
 * }
 * ]
 */
const fetchAnnotations = async () => {
  console.log("正在从后台获取标注数据...");
  try {
    // 这里是你进行真实API调用的地方。
    // const response = await fetch('/api/get_annotations_for_view', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ viewId: 'current_view' }) // 如果需要，可以发送当前视图的上下文
    // });
    // if (!response.ok) throw new Error('网络响应失败');
    // const data = await response.json();

    // 为演示目的，此处使用模拟数据 (MOCK DATA)
    const mockData = [
      {
        id: "anno_001",
        type: "方向",
        title: "北京方向",
        details: "",
        coordinates: [{
          "x": 803.0602094240838,
          "y": 934.5549738219895
        }, {
          "x": 861.6989528795813,
          "y": 887.434554973822
        }, {
          "x": 848.086387434555,
          "y": 883.7696335078533
        }, {
          "x": 879.5000000000001,
          "y": 874.8691099476439
        }, {
          "x": 876.8821989528797,
          "y": 894.7643979057591
        }, {
          "x": 867.1325088339223,
          "y": 889.7526501766785
        }, {
          "x": 808.1219081272086,
          "y": 938.86925795053
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_002",
        type: "方向",
        title: "香港方向",
        details: "",
        coordinates: [{
          "x": 767.3472222222222,
          "y": 816.6666666666667
        }, {
          "x": 730.5416666666666,
          "y": 829.8611111111111
        }, {
          "x": 726.0277777777778,
          "y": 824.3055555555555
        }, {
          "x": 710.4027777777778,
          "y": 843.4027777777778
        }, {
          "x": 738.875,
          "y": 843.0555555555555
        }, {
          "x": 734.0138888888889,
          "y": 836.8055555555555
        }, {
          "x": 772.5555555555555,
          "y": 822.9166666666667
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_003",
        type: "匝道",
        title: "E匝道",
        details: "",
        coordinates: [{
          "x": 3.5875912408760513,
          "y": 870.8029197080291
        }, {
          "x": 45.92335766423371,
          "y": 868.6131386861313
        }, {
          "x": 97.74817518248189,
          "y": 867.883211678832
        }, {
          "x": 161.98175182481765,
          "y": 868.6131386861313
        }, {
          "x": 202.85766423357677,
          "y": 870.8029197080291
        }, {
          "x": 230.59489051094903,
          "y": 883.941605839416
        }, {
          "x": 248.8430656934308,
          "y": 910.2189781021897
        }, {
          "x": 260.5218978102191,
          "y": 932.8467153284671
        }, {
          "x": 1.9719101123596734,
          "y": 1005.4550561797753
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_004",
        type: "匝道",
        title: "B匝道",
        details: "",
        coordinates: [{
          "x": 1582.3846153846152,
          "y": 1268.5384615384614
        }, {
          "x": 1930.461538461538,
          "y": 1287.7692307692307
        }, {
          "x": 2195.846153846154,
          "y": 1299.3076923076924
        }, {
          "x": 2517.0,
          "y": 1287.7692307692307
        }, {
          "x": 2558.0,
          "y": 1282.1783216783217
        }, {
          "x": 2558.0,
          "y": 1168.5384615384614
        }, {
          "x": 2449.6923076923076,
          "y": 1180.076923076923
        }, {
          "x": 2295.846153846154,
          "y": 1178.1538461538462
        }, {
          "x": 2151.6153846153843,
          "y": 1176.2307692307693
        }, {
          "x": 1917.0,
          "y": 1174.3076923076924
        }, {
          "x": 1638.1538461538462,
          "y": 1168.5384615384614
        }, {
          "x": 1451.6153846153848,
          "y": 1147.3846153846155
        }, {
          "x": 1251.6153846153848,
          "y": 1089.6923076923076
        }],
        imageHeight: 1439,
        imageWidth: 2559
      }, {
        id: "anno_005",
        type: "桥墩",
        title: "1#桥墩",
        details: "",
        coordinates: [{
          "x": 179.6327,
          "y": 786.27796
        }, {
          "x": 180.133555,
          "y": 827.34641
        }, {
          "x": 226.5442404,
          "y": 828.0141903
        }, {
          "x": 228.213689,
          "y": 785.7771285
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_006",
        type: "桥墩",
        title: "2#桥墩",
        details: "",
        coordinates: [{
          "x": 394.2528735632184,
          "y": 800.7807881773399
        }, {
          "x": 392.2824302134647,
          "y": 845.9367816091955
        }, {
          "x": 433.6617405582923,
          "y": 842.324302134647
        }, {
          "x": 433.8259441707718,
          "y": 796.3472906403941
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_007",
        type: "盖梁",
        title: "2#盖梁",
        details: "",
        coordinates: [{
          "x": 375.86206896551727,
          "y": 769.7463054187192
        }, {
          "x": 376.3546798029557,
          "y": 795.0336617405584
        }, {
          "x": 442.6929392446634,
          "y": 791.9137931034484
        }, {
          "x": 442.20032840722496,
          "y": 764.9844006568145
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_008",
        type: "桥墩",
        title: "5#桥墩",
        details: "",
        coordinates: [{
          "x": 1098.361788617886,
          "y": 802.1016260162602
        }, {
          "x": 1096.5731707317073,
          "y": 869.0934959349593
        }, {
          "x": 1116.410569105691,
          "y": 864.3780487804878
        }, {
          "x": 1118.19918699187,
          "y": 798.8495934959349
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_009",
        type: "桥墩",
        title: "6#桥墩",
        details: "",
        coordinates: [{
          "x": 1346.6750663129974,
          "y": 820.4244031830239
        }, {
          "x": 1345.216180371353,
          "y": 869.0934959349593
        }, {
          "x": 1365.110079575597,
          "y": 879.5755968169761
        }, {
          "x": 1366.5689655172414,
          "y": 814.4562334217507
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_010",
        type: "桥墩",
        title: "7#桥墩",
        details: "",
        coordinates: [{
          "x": 1504.159445407279,
          "y": 832.4090121317157
        }, {
          "x": 1502.7729636048525,
          "y": 881.8024263431541
        }, {
          "x": 1544.8873483535526,
          "y": 876.949740034662
        }, {
          "x": 1545.2339688041593,
          "y": 824.2634315424609
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_011",
        type: "盖梁",
        title: "7#盖梁",
        details: "",
        coordinates: [{
          "x": 1499.48006932409,
          "y": 812.8249566724436
        }, {
          "x": 1497.2270363951473,
          "y": 830.6759098786828
        }, {
          "x": 1552.5129982668975,
          "y": 821.4904679376083
        }, {
          "x": 1550.953206239168,
          "y": 805.0259965337955
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_012",
        type: "桥墩",
        title: "8#桥墩",
        details: "",
        coordinates: [{
          "x": 1668.1341719077566,
          "y": 856.6037735849055
        }, {
          "x": 1667.9245283018865,
          "y": 896.4360587002095
        }, {
          "x": 1714.2557651991613,
          "y": 892.4528301886792
        }, {
          "x": 1711.320754716981,
          "y": 848.8469601677148
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_013",
        type: "盖梁",
        title: "8#盖梁",
        details: "",
        coordinates: [{
          "x": 1660.587002096436,
          "y": 836.2683438155135
        }, {
          "x": 1658.7002096436056,
          "y": 854.7169811320754
        }, {
          "x": 1724.5283018867922,
          "y": 845.9119496855345
        }, {
          "x": 1721.174004192872,
          "y": 827.2536687631026
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_014",
        type: "桥墩",
        title: "9#桥墩",
        details: "",
        coordinates: [{
          "x": 1832.9591194968555,
          "y": 856.9182389937107
        }, {
          "x": 1830.4433962264152,
          "y": 903.7735849056603
        }, {
          "x": 1891.4496855345913,
          "y": 904.0880503144654
        }, {
          "x": 1893.6509433962265,
          "y": 850.314465408805
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_015",
        type: "桥墩",
        title: "10#桥墩",
        details: "",
        coordinates: [{
          "x": 1994.0,
          "y": 875.6666666666666
        }, {
          "x": 1993.0,
          "y": 911.0
        }, {
          "x": 2097.3333333333335,
          "y": 913.0
        }, {
          "x": 2097.3333333333335,
          "y": 864.0
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_016",
        type: "桥台",
        title: "11#桥台",
        details: "",
        coordinates: [{
          "x": 2118.6046511627906,
          "y": 895.2751937984495
        }, {
          "x": 2118.217054263566,
          "y": 930.546511627907
        }, {
          "x": 2250.0,
          "y": 930.1589147286821
        }, {
          "x": 2248.062015503876,
          "y": 885.9728682170543
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_017",
        type: "盖梁",
        title: "1#盖梁",
        details: "",
        coordinates: [{
          "x": 171.20731707317077,
          "y": 765.0284552845528
        }, {
          "x": 171.20731707317077,
          "y": 784.3780487804878
        }, {
          "x": 238.68699186991873,
          "y": 781.9390243902438
        }, {
          "x": 238.84959349593498,
          "y": 761.6138211382114
        }],
        imageHeight: 1439,
        imageWidth: 2559,
      }, {
        id: "anno_018",
        type: "涵洞",
        title: "1-2×2m箱型涵洞CK0+310",
        details: "",
        coordinates: [{
          "x": 2257.7894736842104,
          "y": 935.5087719298245
        }, {
          "x": 2254.280701754386,
          "y": 974.9824561403509
        }, {
          "x": 2371.8245614035086,
          "y": 1009.1929824561404
        }, {
          "x": 2374.017543859649,
          "y": 955.6842105263158
        }],
        imageHeight: 1439,
        imageWidth: 2559
      }
    ];

    annotations.value = mockData;
    console.log("标注数据加载成功:", annotations.value);

    drawAnnotations(); // 绘制新获取的标注
  } catch (error) {
    console.error("获取标注数据失败:", error);
    alert("无法加载标注数据，请检查后台连接。");
  }
};

/**
 * 通过向后端发送命令来切换视图。
 * 这通常会触发视频流的更改和一套新的标注。
 * @param {string} viewId - 要切换到的视图ID (例如 'view_1')。
 */
const switchView = async (viewId) => {
  console.log(`准备切换到视角: ${viewId}`);
  try {
    const response = await fetch('/api/switch_view', { // 虚拟的API端点
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ view: viewId, timestamp: new Date().toISOString() })
    });
    if (!response.ok) throw new Error(`HTTP 错误! 状态码: ${response.status}`);
    const result = await response.json();
    console.log('视角切换成功, 响应:', result);
    alert(`已发送指令切换到 "${viewId}"!`);

    // 成功切换视图后，获取新的标注
    await fetchAnnotations();

  } catch (error) {
    console.error(`切换到 ${viewId} 失败:`, error);
    alert(`指令 "${viewId}" 发送失败: ${error.message}`);
  }
};


// --- 用于详情弹出框的鼠标交互 ---

/**
 * 使用射线投射算法检查一个点是否在多边形内部。
 * @param {{x: number, y: number}} point 鼠标位置。
 * @param {Array<{x: number, y: number}>} polygon 标注图形的顶点数组。
 * @returns {boolean} 如果点在多边形内，则返回true。
 */
function isPointInPolygon(point, polygon) {
    let isInside = false;
    const x = point.x, y = point.y;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
        const xi = polygon[i].x, yi = polygon[i].y;
        const xj = polygon[j].x, yj = polygon[j].y;

        const intersect = ((yi > y) !== (yj > y))
            && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
        if (intersect) isInside = !isInside;
    }
    return isInside;
}

const handleCanvasMouseMove = (e) => {
  if (!annotationCanvas.value) return;
  const rect = annotationCanvas.value.getBoundingClientRect();
  const mousePos = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  };

  // --- CHANGE: 悬停检测也需要使用缩放后的坐标 ---
  const currentCanvasWidth = annotationCanvas.value.width;
  const currentCanvasHeight = annotationCanvas.value.height;

  const currentHover = annotations.value.slice().reverse().find(anno => {
      if (!anno.imageWidth || !anno.imageHeight) return false;
      
      const scaleX = currentCanvasWidth / anno.imageWidth;
      const scaleY = currentCanvasHeight / anno.imageHeight;

      // 将原始坐标转换为当前画布坐标以进行比较
      const scaledPolygon = anno.coordinates.map(p => ({
          x: p.x * scaleX,
          y: p.y * scaleY
      }));
      
      return isPointInPolygon(mousePos, scaledPolygon);
  });
  // ----------------------------------------------------

  if (currentHover) {
    hoveredAnnotation.value = currentHover;
    popupPosition.value.x = Math.min(mousePos.x + 15, rect.width - 220); 
    popupPosition.value.y = Math.min(mousePos.y + 15, rect.height - 100); 
    canvasCursor.value = 'pointer';
  } else {
    hoveredAnnotation.value = null;
    canvasCursor.value = 'default';
  }
};

// --- WebSocket 连接逻辑 (基本未变) ---
const connectWebSocket = () => {
  if (isConnected.value) return;
  const serverUrl = 'ws://59.110.65.210:8765';
  connectionStatus.value = "连接中...";
  try {
    const ws = new WebSocket(serverUrl);
    socket.value = ws;
    ws.onopen = () => {
      isConnected.value = true;
      connectionStatus.value = "已连接";
      console.log("已连接视频流");
    };
    ws.onmessage = (event) => {
      // 处理传入视频帧的逻辑
      if (typeof event.data === 'string') {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'frame' && message.data) {
            displayFrame(message.data);
          }
        } catch(e) { /* 不是JSON消息，可能是其他数据类型 */ }
      } else if (event.data instanceof Blob || event.data instanceof ArrayBuffer) {
        processImageData(event.data);
      }
    };
    ws.onclose = () => handleDisconnect('连接已断开');
    ws.onerror = () => handleDisconnect('连接错误');
  } catch (error) {
    handleDisconnect('连接失败');
  }
};

const handleDisconnect = (statusText) => {
  isConnected.value = false;
  connectionStatus.value = statusText;
  if (socket.value) {
    socket.value.close();
    socket.value = null;
  }
};

const displayFrame = (base64Data) => {
  const img = new Image();
  img.onload = () => {
    if (videoCtx) {
      videoCtx.clearRect(0, 0, videoCtx.canvas.width, videoCtx.canvas.height);
      videoCtx.drawImage(img, 0, 0, videoCtx.canvas.width, videoCtx.canvas.height);
    }
  };
  img.src = 'data:image/jpeg;base64,' + base64Data;
};

const processImageData = (data) => {
  const blob = new Blob([data], { type: 'image/jpeg' });
  const url = URL.createObjectURL(blob);
  const img = new Image();
  img.onload = () => {
    if (videoCtx) {
      videoCtx.clearRect(0, 0, videoCtx.canvas.width, videoCtx.canvas.height);
      videoCtx.drawImage(img, 0, 0, videoCtx.canvas.width, videoCtx.canvas.height);
    }
    URL.revokeObjectURL(url);
  };
  img.src = url;
};

</script>

<style scoped>
/* --- 基础布局 --- */
.annotator-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  background-color: #000;
  overflow: hidden;
  font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.background-canvas, .annotation-canvas-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
.background-canvas { z-index: 1; }
.annotation-canvas-layer { z-index: 3; /* 在视频之上，UI之下 */ }

/* --- UI 覆盖层 --- */
.ui-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 4;
  pointer-events: none; /* 允许点击穿透到canvas */
  display: flex;
  flex-direction: column;
}

.main-content {
  flex-grow: 1;
  position: relative;
}

/* --- 头部 --- */
.app-header {
  position: relative;
  height: 50px;
  width: 100%;
  color: #fff;
  background: linear-gradient( to right, rgba(0, 123, 255, 0) 0%, rgba(0, 123, 255, 0.6) 20%, rgba(0, 123, 255, 1) 50%, rgba(0, 123, 255, 0.6) 80%, rgba(0, 123, 255, 0) 100% );
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8), 0 0 10px rgba(0, 191, 255, 0.5);
  flex-shrink: 0;
}
.app-header h1 {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-size: 2.5rem;
  font-weight: 600;
}
.connection-status {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
}
.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #ff5722;
  box-shadow: 0 0 8px #ff5722;
  transition: all 0.3s ease;
}
.status-indicator.connected {
  background-color: #00ff7f;
  box-shadow: 0 0 10px #00ff7f;
}

/* --- 详情弹出框 (新) --- */
.details-popup {
  position: absolute;
  width: 250px;
  padding: 15px;
  background-color: rgba(10, 40, 90, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 191, 255, 0.6);
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  color: #fff;
  font-size: 0.9rem;
  pointer-events: none; /* 弹出框本身不捕获鼠标事件 */
  transition: opacity 0.2s ease;
  z-index: 100;
}
.details-popup h4 {
  margin: 0 0 10px 0;
  color: #00BFFF;
  font-size: 1rem;
  border-bottom: 1px solid rgba(0, 191, 255, 0.3);
  padding-bottom: 5px;
}
.details-popup p {
  margin: 0;
  line-height: 1.5;
}

/* --- 视角控件 (替换PTZ) --- */
.view-controls {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 240px; /* 调整宽度 */
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
  pointer-events: auto; /* 按钮可点击 */
}
.view-btn {
  padding: 12px 10px;
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
  background-color: rgba(20, 40, 80, 0.7);
  border: 1px solid rgba(0, 191, 255, 0.6);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(5px);
  text-align: center;
}
.view-btn:hover {
  background-color: rgba(0, 191, 255, 0.7);
  border-color: #fff;
  transform: scale(1.05);
}
.view-btn:active {
  transform: scale(0.98);
}
</style>