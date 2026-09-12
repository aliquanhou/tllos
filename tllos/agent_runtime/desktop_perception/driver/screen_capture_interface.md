# Screen Capture Interface

## 定位

Screen Capture 是 Perception Layer 的输入接口，负责从操作系统获取屏幕帧。

---

## Interface Definition

### capture(screen_id) → Frame

**输入：**
- screen_id: 屏幕标识

**输出：**
- frame: Screen Frame

---

### capture_region(region) → Frame

**输入：**
- region: 采集区域 (x, y, width, height)

**输出：**
- frame: Screen Frame

---

## 安全边界

**禁止：**
- 直接调用 Windows API / Linux API / macOS API
- 绕过 Permission 直接采集

**必须：**
- Permission Check → Capture Request → Capture Result → Evidence → Audit

---

## 实现状态

```
INTERFACE ONLY
Real Implementation: NOT IMPLEMENTED
```

---

*Screen Capture Interface — P2-07*
