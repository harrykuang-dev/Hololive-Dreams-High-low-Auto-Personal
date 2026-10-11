# Hololive Dreams — 하이&로 자동 플레이

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Windows용 하이&로 자동 플레이 프로그램입니다. 신중(기본) 전략과 공격적(3단계) 전략을 제공합니다. 인터페이스는 영어, 번체 중국어, 일본어, 한국어, 인도네시아어, 간체 중국어를 지원합니다.

Fluent 스타일 인터페이스는 흰색 단축키 입력란과 명확한 시작·중지 버튼을 제공하며 전략 설명은 프로그램 창 중앙에 표시됩니다. 언어 라벨은 현재 언어의 ‘언어’ 번역과 ‘Language’를 함께 표시합니다.

## 다운로드 및 실행

[최신 릴리스](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal/releases/latest)에서 **HololiveDreamsHighLowAuto.exe**를 다운로드하여 실행합니다. 템플릿, OCR 모델 및 필수 리소스가 단일 실행 파일에 포함되며 시작할 때 임시로 압축이 해제됩니다.

1. 게임의 하이&로 화면을 엽니다.
2. 신중 또는 공격적 전략을 선택합니다. 기본값은 신중입니다. 전략 오른쪽의 물음표를 클릭하면 설명을 볼 수 있습니다.
3. **F8**로 시작하고 **INSERT**로 중지합니다. 화면의 버튼으로도 조작할 수 있습니다.

단축키 칸을 클릭하고 키 또는 Ctrl / Alt / Shift 조합을 눌러 변경합니다. **Esc**로 등록을 취소합니다. 시작과 중지 단축키는 서로 달라야 합니다. Num Lock 때문에 Alt 보조 키가 추가되지 않습니다.

## 기록 및 순이익

오늘의 코인은 확인된 보상 합계입니다. 순이익은 **확인된 보상 − 50 × (승리 라운드 수 + 패배 라운드 수)**입니다. 정산된 승리 라운드에도 참가 비용 50 코인이 적용됩니다. 이 차감은 순이익 표시에만 적용되며 보상 금액과 전략 판단은 기존 규칙을 유지합니다.

`daily_coins.json`은 당일 보상, 라운드 수 및 3단계 진행 상황을 저장하고, `settings.json`은 언어, 전략 및 단축키를 저장합니다. 업데이트 전에 프로그램을 중지하고 두 파일을 새 EXE와 같은 폴더에 보존합니다.

당일 기록과 3단계 진행 상황은 **컴퓨터의 현지 시각 오전 4시**에 초기화됩니다. **당일 기록 초기화** 버튼은 확인 후 보상, 순이익, 라운드 수 및 3단계 진행 상황을 초기화합니다. 서버와 컴퓨터의 시간대가 다르면 수동 초기화를 사용할 수 있습니다.

이전 당일 기록에 승리 횟수가 없으면 기존 보상을 유지하고 순이익을 계산할 수 없다고 표시합니다. 과거 참가 비용은 추정하지 않으며 다음 당일 기록 초기화 후 완전한 집계를 재개합니다. 로그나 스크린샷은 저장하지 않습니다.

## 소스 실행 및 빌드

```powershell
python -m pip install -r requirements.txt pyinstaller
python main_ui.py
python -m PyInstaller --noconfirm "Hololive Dreams-Auto.spec"
```

출력: `dist/HololiveDreamsHighLowAuto.exe`.

## 문서 및 라이선스

[3단계 전략](THREE_STAGE.md#ko) · [게임 용어](docs/GAME_TERMS.md) · [보상 OCR](docs/OCR.md) · [v1.1.1 릴리스 노트](docs/RELEASE-1.1.1.md) · [버전 이력](HISTORY.md)

카드 인식 및 보유 카드 선택 전략은 [hololive-dreams-helper](https://github.com/Oreki0504/hololive-dreams-helper)를 기반으로 합니다. [MIT 고지](licenses/poker-core-MIT.txt)와 기타 필수 라이선스 고지는 [licenses](licenses/)에 포함됩니다.
