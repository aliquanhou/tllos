# Screen Capture Driver

## 定位

Screen Capture Driver 是跨平台屏幕采集驱动抽象层。

---

## 平台 Adapter

### Windows Adapter

**方法：** GDI / DirectX / Windows Graphics Capture

**接口：**
- capture_screen(): 获取全屏
- capture_region(x, y, w, h): 获取指定区域
- capture_window(window_handle): 获取窗口

### Linux Adapter

**方法：** X11 / Wayland

**接口：**
- capture_screen()
- capture_region(x, y, w, h)
- capture_window(window_id)

### macOS Adapter

**方法：** CGWindow / ScreenCaptureKit

**接口：**
- capture_screen()
- capture_region(x, y, w, h)
- capture_window(window_id)

---

## 驱动字段

| 字段 | 说明 |
|------|------|
| driver_id | 驱动 ID (screen_capture.windows / screen_capture.linux / screen_capture.macos) |
| driver_type | 驱动类型 |
| permission | 所需权限 |
| capabilities | 支持的采集能力 |
| status | 驱动状态 |

---

## 安全边界

**禁止：**
- 直接调用系统 API
- 绕过 Permission

**必须：**
- Permission Check → Capture Request → Capture Result → Evidence → Audit

---

## 实现状态

```
INTERFACE ONLY
Real Implementation: NOT IMPLEMENTED
```

---

*Screen Capture Driver — P2-07*
