import streamlit as st
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(
    page_title="밀폐공간 안전 데이터 수집기", 
    page_icon="🛡️", 
    layout="centered"
)

# 🛠️ [안전한 숨김 스타일] 화면 전체를 날리지 않고 상단 헤더와 불필요한 클라우드 뱃지만 깔끔하게 숨김
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none;}
    [data-testid="stHeader"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("🛡️ 밀폐공간 현장 센서 데이터 수집기")
st.markdown("측정 중에는 모든 버튼이 비활성화되며, **[측정 중지] 버튼을 빠르게 3번** 눌러야 안전하게 종료됩니다.")

# 데이터 수집용 HTML/JavaScript 컴포넌트
collector_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Sensor Collector</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f4f6f9;
            color: #333;
            margin: 0;
            padding: 10px;
            text-align: center;
        }
        .container {
            background: #fff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        h3 { color: #1e293b; margin-top: 0; }
        .status-box {
            padding: 15px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 1.1em;
            margin: 15px 0;
            background-color: #e2e8f0;
            color: #475569;
        }
        .recording { background-color: #d1fae5 !important; color: #065f46 !important; }
        button {
            background-color: #2563eb;
            color: white;
            border: none;
            padding: 14px 20px;
            font-size: 1.05em;
            border-radius: 6px;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
            font-weight: bold;
            transition: background 0.2s;
        }
        button:disabled {
            background-color: #cbd5e1 !important;
            color: #94a3b8 !important;
            cursor: not-allowed;
        }
        button:active:not(:disabled) { background-color: #1d4ed8; }
        .stop-btn { background-color: #dc2626; }
        .download-btn { background-color: #059669; }
        .data-display {
            text-align: left;
            background: #f8fafc;
            padding: 12px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.85em;
            margin-top: 15px;
            max-height: 160px;
            overflow-y: auto;
            border: 1px solid #e2e8f0;
        }
    </style>
</head>
<body>

<div class="container">
    <h3>🔒 잠금 모드 센서 로거</h3>
    <p id="guideText" style="font-size: 0.9em; color: #64748b;">시작 후 다른 버튼은 모두 잠깁니다.</p>

    <div id="statusBox" class="status-box">
        상태: 대기 중
    </div>

    <!-- 제어 버튼 -->
    <button id="startBtn" onclick="requestSensors()">1. 권한 허용 및 측정 시작</button>
    <button id="stopBtn" onclick="handleTripleTap()" class="stop-btn" style="display:none;" disabled>⚠️ 측정 중지 (빠르게 3번 누르세요)</button>
    <button id="downloadBtn" onclick="downloadCSV()" class="download-btn" style="display:none;">3. CSV 파일 다운로드</button>

    <div class="data-display" id="dataView">
        [실시간 센서 값 대기 중...]
    </div>
</div>

<script>
    let isRecording = false;
    let logData = [];
    let currentPressure = 1013.25;
    let wakeLock = null;

    // 트리플 탭(빠른 3번 클릭) 감지 변수
    let tapCount = 0;
    let tapTimer = null;

    // 화면 꺼짐 방지 (Wake Lock)
    async function requestWakeLock() {
        if ('wakeLock' in navigator) {
            try {
                wakeLock = await navigator.wakeLock.request('screen');
            } catch (err) {
                console.error(err);
            }
        }
    }

    function requestSensors() {
        if (typeof DeviceMotionEvent !== 'undefined' && typeof DeviceMotionEvent.requestPermission === 'function') {
            DeviceMotionEvent.requestPermission()
                .then(response => {
                    if (response === 'granted') { startMonitoring(); }
                    else { alert("센서 권한이 거부되었습니다."); }
                }).catch(console.error);
        } else {
            startMonitoring();
        }
    }

    async function startMonitoring() {
        isRecording = true;
        logData = [];
        
        await requestWakeLock();

        document.getElementById('startBtn').style.display = 'none';
        let stopBtn = document.getElementById('stopBtn');
        stopBtn.style.display = 'block';
        stopBtn.disabled = false;
        
        document.getElementById('downloadBtn').style.display = 'none';
        document.getElementById('guideText').innerText = "🔒 측정 중: 주머니 속 오작동 방지 잠금 활성화됨";
        
        let box = document.getElementById('statusBox');
        box.className = "status-box recording";
        box.innerHTML = "상태: 🔴 데이터 수집 중 (안전 잠금)";

        window.addEventListener('devicemotion', handleMotion);
    }

    function handleMotion(event) {
        if (!isRecording) return;

        let acc = event.accelerationIncludingGravity || event.acceleration;
        let x = acc && acc.x !== null ? acc.x.toFixed(3) : 0;
        let y = acc && acc.y !== null ? acc.y.toFixed(3) : 0;
        let z = acc && acc.z !== null ? acc.z.toFixed(3) : 0;
        let pressure = currentPressure.toFixed(2);

        let timestamp = new Date().toISOString();

        logData.push({ timestamp, x, y, z, pressure });

        document.getElementById('dataView').innerHTML = 
            `기록 건수: ${logData.length}건<br>` +
            `시간: ${timestamp.split('T')[1].slice(0,8)}<br>` +
            `가속도 X: ${x} | Y: ${y} | Z: ${z}`;
    }

    // 트리플 탭(0.6초 이내에 3번 연속 터치)으로만 중지 작동
    function handleTripleTap() {
        tapCount++;
        
        if (tapCount === 1) {
            tapTimer = setTimeout(() => {
                tapCount = 0;
            }, 600);
        } else if (tapCount === 3) {
            clearTimeout(tapTimer);
            tapCount = 0;
            stopRecording();
        }
    }

    function stopRecording() {
        isRecording = false;
        window.removeEventListener('devicemotion', handleMotion);
        
        if (wakeLock !== null) {
            wakeLock.release();
            wakeLock = null;
        }

        document.getElementById('stopBtn').style.display = 'none';
        document.getElementById('downloadBtn').style.display = 'block';
        document.getElementById('guideText').innerText = "측정이 완료되었습니다. 파일을 다운로드하세요.";
        
        let box = document.getElementById('statusBox');
        box.className = "status-box";
        box.innerHTML = `상태: ✅ 수집 완료 (총 ${logData.length}건)`;
    }

    function downloadCSV() {
        if (logData.length === 0) {
            alert("다운로드할 데이터가 없습니다.");
            return;
        }

        let csvContent = "data:text/csv;charset=utf-8,timestamp,acc_x,acc_y,acc_z,pressure\\n";
        logData.forEach(row => {
            csvContent += `${row.timestamp},${row.x},${row.y},${row.z},${row.pressure}\\n`;
        });
        
        let encodedUri = encodeURI(csvContent);
        let link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "smartphone_sensor_log_secure.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
</script>

</body>
</html>
"""

components.html(collector_html, height=380)

st.info("💡 **안전 수집 가이드**\n1. **화면 정상 출력**: 레이아웃을 깨트리던 과도한 CSS를 제거하여 대시보드 화면이 정상적으로 나타납니다.\n2. **트리플 탭 방어**: 실수로 한 번 터치되거나 주머니 속에서 눌려 조기에 종료되는 것을 막기 위해, **[측정 중지] 버튼을 0.6초 안에 빠르게 3번** 연타해야만 데이터 수집이 안전하게 종료됩니다.")
