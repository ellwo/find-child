# Quick Start Guide - نظام تتبع الأطفال الأبوي

## التشغيل السريع مع Docker

### 1. إعداد ملف البيئة
```bash
cp .env.example .env
```

### 2. تعديل ملف `.env`
أضف القيم التالية (مهمة):
- `JWT_SECRET_KEY`: مفتاح سري قوي (مثال: `my-super-secret-key-12345`)
- `VITE_GOOGLE_MAPS_API_KEY`: مفتاح Google Maps API
- `CAMERA_API_KEY`: مفتاح للكاميرات (مثال: `camera_key_123`)
- `GPS_DEVICE_API_KEY`: مفتاح لأجهزة GPS (مثال: `gps_key_123`)
- `ADMIN_USERNAME`: اسم مستخدم الإدارة (افتراضي: `admin`)
- `ADMIN_PASSWORD`: كلمة مرور الإدارة (افتراضي: `admin123`)

### 3. تشغيل المشروع
```bash
docker-compose up -d --build
```

### 4. انتظار التهيئة
انتظر دقيقة أو دقيقتين حتى:
- يتم إنشاء جداول قاعدة البيانات
- يتم إنشاء مستخدم admin الافتراضي
- يتم إنشاء إعدادات النظام

### 5. الوصول إلى النظام
- **الواجهة الرئيسية**: http://localhost:3122
- **تسجيل دخول الإدارة**: http://localhost:3122/admin/login
  - Username: `admin` (أو ما حددته في `.env`)
  - Password: `admin123` (أو ما حددته في `.env`)
- **تسجيل دخول ولي الأمر**: http://localhost:3122/parent/login
- **API Documentation**: http://localhost:8000/docs
- **CompreFace UI**: http://localhost:8001

### 6. إعداد CompreFace (مهم)
1. افتح http://localhost:8001
2. سجل دخول (أو أنشئ حساب)
3. أنشئ Subject/Collection جديد
4. احصل على API Key
5. حدّث `COMPREFACE_API_KEY` في `.env`
6. أعد تشغيل API:
   ```bash
   docker-compose restart api
   ```

## استخدام النظام

### للإدارة:
1. سجل دخول من `/admin/login`
2. من لوحة التحكم يمكنك:
   - إضافة حافلات وربطها بأجهزة GPS والكاميرات
   - إضافة أولياء أمور
   - إضافة طلاب مع رفع صور وجوههم
   - تحديد موقع المدرسة في الإعدادات
   - متابعة الحافلات لحظياً

### لأولياء الأمور:
1. سجل دخول من `/parent/login`
2. شاهد قائمة أطفالك
3. اختر طفلاً لمتابعة:
   - آخر حضور
   - موقع الحافلة الحالي
   - سجل الحضور
   - مسار الحافلة

## إرسال البيانات من الأجهزة

### من جهاز GPS:
```bash
curl -X POST "http://localhost:8000/api/device/gps/update" \
  -H "X-API-KEY: changeme_gps_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "gps_001",
    "latitude": 24.7136,
    "longitude": 46.6753
  }'
```

### من الكاميرا:
```bash
curl -X POST "http://localhost:8000/api/upload_camera_face" \
  -H "X-API-KEY: changeme_camera_api_key" \
  -F "camera_id=cam_001" \
  -F "image=@face.jpg"
```

## الأوامر المفيدة

```bash
# عرض السجلات
docker-compose logs -f api

# إعادة بناء
docker-compose build --no-cache

# إيقاف
docker-compose down

# إيقاف مع حذف البيانات
docker-compose down -v
```

## ملاحظات مهمة

1. **Google Maps**: يجب إضافة API Key في `.env` كـ `VITE_GOOGLE_MAPS_API_KEY`
2. **CompreFace**: يجب إعداد API Key بعد أول تشغيل
3. **WebSocket**: يعمل تلقائياً عبر nginx
4. **البيانات**: يتم إنشاء admin user تلقائياً من متغيرات `.env`

