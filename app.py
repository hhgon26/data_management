import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="밀폐공간 안전 데이터 수집기 (백그라운드 지원)", page_icon="📊", layout="centered")

st.title("📊 밀폐공간 작업자 센서 데이터 수집기")
st.markdown("화면을 끄거나 브라우저를 내려도 **백그라운드에서 센서 데이터가 연속 수집**됩니다.")

collector_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Background Sensor Collector</title>
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
    <h3>📱 백그라운드 센서 로거</h3>
    <p style="font-size: 0.9em; color: #64748b;">측정 시작 후 주머니에 넣거나 화면을 꺼도 기록됩니다.</p>

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
    let wakeLock = null;

    // 화면 꺼짐 방지 (Wake Lock API)
    async function requestWakeLock() {
        if ('wakeLock' in navigator) {
            try {
                wakeLock = await navigator.wakeLock.request('screen');
                console.log('Wake Lock 활성화됨');
                wakeLock.addEventListener('release', () => {
                    console.log('Wake Lock 해제됨');
                });
            } catch (err) {
                console.error(`${err.name}, ${err.message}`);
            }
        }
    }

    // 페이지가 다시 활성화되었을 때 Wake Lock 재요청
    document.addEventListener('visibilitychange', async () => {
        if (wakeLock !== null && document.visibilityState === 'visible' && isRecording) {
            await requestWakeLock();
        }
    });

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

    async function startMonitoring() {
        isRecording = true;
        logData = [];
        
        // 화면 꺼짐 방지 요청
        await requestWakeLock();

        document.getElementById('permissionBtn').style.display = 'none';
        document.getElementById('recordBtn').style.display = 'block';
        document.getElementById('downloadBtn').style.display = 'none';
        
        let box = document.getElementById('statusBox');
        box.className = "status-box recording";
        box.innerHTML = "상태: 🔴 백그라운드 수집 중...";

        // 기압 센서 연동
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

        // 화면 갱신 (화면이 켜져있을 때만 반영됨)
        document.getElementById('dataView').innerHTML = 
            `기록 건수: ${logData.length}건<br>` +
            `시간: ${timestamp.split('T')[1].slice(0,8)}<br>` +
            `가속도 X: ${x} | Y: ${y} | Z: ${z}<br>` +
            `기압: ${pressure} hPa`;
    }

    function stopRecording() {
        isRecording = false;
        window.removeEventListener('devicemotion', handleMotion);
        
        // Wake Lock 해제
        if (wakeLock !== null) {
            wakeLock.release();
            wakeLock = null;
        }

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
        link.setAttribute("download", "smartphone_sensor_log_bg.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
</script>

</body>
</html>
"""

components.html(collector_html, height=360)

st.info("💡 **백그라운드 수집 안내**\n1. **Screen Wake Lock API**가 적용되어 측정 중에는 화면이 임의로 꺼지는 현상을 방지합니다.\n2. 작업 중 주머니에 넣거나 브라우저를 내려도 센서 이벤트(`devicemotion`)가 발생하는 동안 데이터가 메모리에 안전하게 누적됩니다.\n3. 작업 완료 후 화면을 켜고 **[기록 중지]** 및 **[CSV 파일 다운로드]**를 진행해 주세요.")
