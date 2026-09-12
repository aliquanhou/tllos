# Vision Evidence Pipeline

## 瀹氫綅

Vision Evidence Pipeline 纭繚鎵€鏈夎瑙夎緭鍑洪兘鏈夊畬鏁寸殑璇佹嵁閾俱€?
---

## Pipeline Flow

```
Image (Frame)
  鈫?Analysis (OCR / Object Detection)
  鈫?Result (Text Regions / Vision Objects)
  鈫?Evidence (Hash + Metadata)
  鈫?Ledger (Audit Event)
```

---

## Evidence Requirements

### Frame Evidence
- frame_id
- timestamp
- width / height
- format
- source
- SHA256 hash
- file_path

### OCR Evidence
- frame_id
- text_regions
- each region: text, confidence, position
- ocr_engine version

### Object Detection Evidence
- frame_id
- objects list
- each object: id, type, position, confidence
- detector version

---

## Safety Rules

1. **No Evidence = No Result**
   - 娌℃湁 hash 鐨勫抚涓嶈兘杩涘叆鍒嗘瀽

2. **Confidence Gate**
   - confidence < 0.5 蹇呴』 REJECT

3. **No Direct Action**
   - Vision Output 涓嶈兘鐩存帴瑙﹀彂 Action
   - 蹇呴』缁忚繃 Decision 鈫?Permission 鈫?Governance

4. **Audit Required**
   - 鎵€鏈夎瑙夎涓哄繀椤昏褰?Audit Ledger

---

## Current Status

```
鉁?Screen Capture Evidence: 宸插疄鐜?鉁?Object Detection Evidence: 宸插疄鐜?鈿狅笍 OCR Evidence: 寰?Tesseract 寮曟搸瀹夎
```

---

*Vision Evidence Pipeline 鈥?P2-08*
