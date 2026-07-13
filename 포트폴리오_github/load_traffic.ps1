# Grafana 그래프용 다양한 트래픽 생성 스크립트
# 실행: portfolio 폴더에서 .\load_traffic.ps1
# 구성: /ask 60% (다양한 질문) · fault-lab normal 20% · delay 10% · error500 5% · timeout 5%

$base = "http://127.0.0.1:8000"
$total = 1000

$questions = @(
    "이 과정은 총 몇 시간인가요?",
    "지각하면 어떻게 되나요?",
    "수료 기준이 몇 퍼센트인가요?",
    "취업 지원도 해주나요?",
    "강사님 성함이 뭔가요?",
    "다른 학생을 때리고 싶어요.",
    "오늘 날씨 어때요?",
    "출결 규정이 어떻게 되나요?",
    "이력서 첨삭도 해주나요?",
    "수료증은 언제 받나요?"
)

Write-Host "총 $total 건 전송 시작 (몇 분 걸립니다)..."

for ($i = 1; $i -le $total; $i++) {
    $roll = Get-Random -Minimum 1 -Maximum 101

    if ($roll -le 60) {
        # 60% : /ask 랜덤 질문 (rule 모드)
        $q = $questions | Get-Random
        $bodyObj = @{ question = $q; mode = "rule" }
        $body = $bodyObj | ConvertTo-Json -Compress
        try {
            Invoke-RestMethod -Method Post -Uri "$base/ask" `
                -ContentType "application/json; charset=utf-8" -Body $body | Out-Null
        } catch {}
    }
    elseif ($roll -le 80) {
        # 20% : fault-lab normal
        curl.exe -s -o NUL "$base/fault-lab?scenario=normal"
    }
    elseif ($roll -le 90) {
        # 10% : fault-lab delay (0.1~1.5초 랜덤)
        $d = [math]::Round((Get-Random -Minimum 1 -Maximum 15) / 10, 1)
        curl.exe -s -o NUL "$base/fault-lab?scenario=delay&delay_seconds=$d"
    }
    elseif ($roll -le 95) {
        # 5% : fault-lab error500
        curl.exe -s -o NUL "$base/fault-lab?scenario=error500"
    }
    else {
        # 5% : fault-lab timeout (0.5~2초 랜덤)
        $d = [math]::Round((Get-Random -Minimum 5 -Maximum 20) / 10, 1)
        curl.exe -s -o NUL "$base/fault-lab?scenario=timeout&delay_seconds=$d"
    }

    if ($i % 50 -eq 0) { Write-Host "$i / $total 완료" }
    Start-Sleep -Milliseconds (Get-Random -Minimum 50 -Maximum 250)
}

Write-Host "완료: 총 $total 건 전송됨. Grafana/Prometheus에서 확인하세요."
