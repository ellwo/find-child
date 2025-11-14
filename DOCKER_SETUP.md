# Docker Setup Guide

## المتطلبات
- Docker
- Docker Compose
- ملف `.env` (انسخ من `.env.example`)

## الخطوات

### 1. إعداد ملف البيئة
```bash
cp .env.example .env
```

ثم عدّل الملف `.env` وأضف:
- `JWT_SECRET_KEY`: مفتاح سري قوي
- `VITE_GOOGLE_MAPS_API_KEY`: مفتاح Google Maps API
- `CAMERA_API_KEY`: مفتاح API للكاميرات
- `GPS_DEVICE_API_KEY`: مفتاح API لأجهزة GPS
- `ADMIN_USERNAME`: اسم مستخدم الإدارة (افتراضي: admin)
- `ADMIN_PASSWORD`: كلمة مرور الإدارة (افتراضي: admin123)
- `ADMIN_EMAIL`: بريد الإدارة

### 2. بناء وتشغيل الحاويات
```bash
docker-compose up -d --build
```

### 3. التحقق من الحالة
```bash
docker-compose ps
```

### 4. عرض السجلات
```bash
# جميع السجلات
docker-compose logs -f

# سجلات API فقط
docker-compose logs -f api

# سجلات Frontend فقط
docker-compose logs -f web
```

### 5. الوصول إلى الخدمات
- **Frontend**: http://localhost:3122 (أو المنفذ المحدد في `WEB_PORT`)
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **CompreFace UI**: http://localhost:8001

### 6. إعداد CompreFace
بعد تشغيل الحاويات:
1. افتح http://localhost:8001
2. أنشئ Subject/Collection جديد
3. احصل على API Key
4. حدّث `COMPREFACE_API_KEY` في `.env`
5. أعد تشغيل API: `docker-compose restart api`

### 7. البيانات الأولية
سيتم إنشاء البيانات الأولية تلقائياً عند بدء تشغيل API:
- مستخدم admin افتراضي (من متغيرات البيئة)
- إعدادات النظام الافتراضية

### 8. إيقاف الخدمات
```bash
docker-compose down
```

### 9. إيقاف وحذف البيانات
```bash
docker-compose down -v
```

## استكشاف الأخطاء

### مشكلة في الاتصال بقاعدة البيانات
```bash
# تحقق من حالة PostgreSQL
docker-compose ps postgres

# عرض سجلات PostgreSQL
docker-compose logs postgres
```

### مشكلة في WebSocket
تأكد من أن nginx.conf يحتوي على إعدادات WebSocket (تم إضافتها تلقائياً)

### مشكلة في CompreFace
```bash
# تحقق من حالة CompreFace
docker-compose ps | grep compreface

# عرض سجلات CompreFace
docker-compose logs compreface-api
```

### إعادة بناء الحاويات
```bash
docker-compose build --no-cache
docker-compose up -d
```

## ملاحظات مهمة

1. **Google Maps API Key**: يجب إضافته في `.env` كـ `VITE_GOOGLE_MAPS_API_KEY`
2. **WebSocket**: يعمل تلقائياً عبر nginx proxy
3. **البيانات**: يتم إنشاء البيانات الأولية تلقائياً عند أول تشغيل
4. **التخزين**: الصور تُحفظ في volume `storage_data`
5. **قاعدة البيانات**: البيانات تُحفظ في volume `postgres_data`

## متغيرات البيئة المهمة

- `JWT_SECRET_KEY`: مفتاح JWT (يجب تغييره في الإنتاج)
- `ADMIN_USERNAME`: اسم مستخدم الإدارة الافتراضي
- `ADMIN_PASSWORD`: كلمة مرور الإدارة الافتراضية
- `VITE_GOOGLE_MAPS_API_KEY`: مفتاح Google Maps
- `CAMERA_API_KEY`: مفتاح API للكاميرات
- `GPS_DEVICE_API_KEY`: مفتاح API لأجهزة GPS

