import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="밀폐공간 안전 데이터 수집기", page_icon="📊", layout="centered")

st.title("📊 밀폐공간 작업자 센서 데이터 수집기")
st.markdown("현장 작업 시 스마트폰 단독 소지를 통해 **가속도(움직임) 및 기압 데이터**를 수집하고 CSV로 저장합니다.")

# 데이터 수집용 HTML/JavaScript 컴포넌트
collector_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sensor Data Collector</title>
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
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 1.05em;
            margin: 15px 0;
            background-color: #e2e8f0;
            color: #475569;
        }
        .recording { background-color: #d1fae5 !important; color: #065f46 !important; }
        button {
            background-color: #2563eb;
            color: white;
            border: none;
            padding: 12px 20px;
            font-size: 1em;
            border-radius: 6px;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
            font-weight: bold;
        }
        button:active { background-color: #1d4ed8; }
        .stop-btn { background-color: #dc2626; }
        .stop-btn:active { background-color: #b91c1c; }
        .download-btn { background-color: #059669; }
        .download-btn:active { background-color: #047857; }
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
    <h3>📱 스마트폰 센서 로거</h3>
    <p style="font-size: 0.9em; color: #64748b;">측정 시작 버튼을 누르고 작업을 진행하세요.</p>

    <div id="statusBox" class="status-box">
        상태: 대기 중
    </div>

    <button id="permissionBtn" onclick="requestSensors()">1. 센서 권한 허용 및 기록 시작</button>
    <button id="recordBtn" onclick="stopRecording()" style="display:none;" class="stop-btn">2. 기록 중지</button>
    <button id="downloadBtn" onclick="downloadCSV()" style="display:none;" class="download-btn">3. CSV 파일 다운로드</button>

    <div class="data-display" id="dataView">
        [실시간 센서 값 대기 중...]
    </div>
</div>

<script>
    let isRecording = false;
    let logData = [];
    let currentPressure = 1013.25;

    function requestSensors() {
        // iOS 권한 요청 처리
        if (typeof DeviceMotionEvent !== 'undefined' && typeof DeviceMotionEvent.requestPermission === 'function') {
            DeviceMotionEvent.requestPermission()
                .then(response => {
                    if (response === 'granted') {
                        startMonitoring();
                    } else {
                        alert("센서 권한이 거부되었습니다.");
                    }
                }).catch(console.error);
        } else {
            startMonitoring();
        }
    }

    function startMonitoring() {
        isRecording = true;
        logData = [];
        
        document.getElementById('permissionBtn').style.display = 'none';
        document.getElementById('recordBtn').style.display = 'block';
        document.getElementById('downloadBtn').style.display = 'none';
        
        let box = document.getElementById('statusBox');
        box.className = "status-box recording";
        box.innerHTML = "상태: 🔴 데이터 수집 및 기록 중...";

        // 기압 센서 연동 (지원 기기 대상)
        if ('Barometer' in window) {
            try {
                const barometer = new Barometer({ frequency: 1 });
                barometer.addEventListener('reading', () => {
                    currentPressure = barometer.pressure;
                });
                barometer.start();
            } catch (e) {
                console.log("Barometer API not supported.");
            }
        }

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

        // 데이터 로그 적재
        logData.push({ timestamp, x, y, z, pressure });

        // 화면 갱신
        document.getElementById('dataView').innerHTML = 
            `기록 건수: ${logData.length}건<br>` +
            `시간: ${timestamp.split('T')[1].slice(0,8)}<br>` +
            `가속도 X: ${x} | Y: ${y} | Z: ${z}<br>` +
            `기압: ${pressure} hPa`;
    }

    function stopRecording() {
        isRecording = false;
        window.removeEventListener('devicemotion', handleMotion);
        
        document.getElementById('recordBtn').style.display = 'none';
        document.getElementById('downloadBtn').style.display = 'block';
        
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
        link.setAttribute("download", "smartphone_sensor_log.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
</script>

</body>
</html>
"""

components.html(collector_html, height=360)

st.info("💡 **데이터 수집 가이드**\n1. 스마트폰으로 본 대시보드에 접속합니다.\n2. **[센서 권한 허용 및 기록 시작]**을 누르고 작업에 들어갑니다.\n3. 작업 완료 후 **[기록 중지]**를 누르고 **[CSV 파일 다운로드]**를 통해 수집된 센서 파일을 확보합니다.\n4. 확보된 CSV 파일은 복합가스측정기(EDW500) 로그와 타임스탬프를 기준으로 병합하여 머신러닝 학습 데이터로 활용할 수 있습니다.")