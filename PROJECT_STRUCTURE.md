# هيكل مشروع المرايا الذكية (Smart Mirrors System)

## نظرة عامة

نظام المرايا الذكية هو نظام متكامل لإدارة الكاميرات الذكية، التعرف على الوجوه، وإدارة بلاغات الأطفال المفقودين.

## هيكل المشروع

```
find-child/
├── api/                          # Backend API (FastAPI)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application + جميع endpoints
│   │   ├── models.py            # Database models (User, Camera, CapturedImage, MissingReport, ReportMatch)
│   │   ├── schemas.py           # Pydantic schemas للـ request/response
│   │   ├── crud.py              # CRUD operations
│   │   ├── db.py                # Database connection
│   │   ├── auth.py              # JWT authentication utilities
│   │   ├── compreface_client.py # CompreFace API client
│   │   ├── external_api.py      # External API notification
│   │   ├── utils.py             # Utility functions
│   │   └── init_db.py           # Database initialization + SystemUser creation
│   ├── Dockerfile
│   └── requirements.txt
│
├── aimirror-vision/              # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── App.tsx              # Main app component + routing
│   │   ├── main.tsx             # Entry point
│   │   ├── pages/
│   │   │   ├── Login.tsx        # صفحة تسجيل الدخول (SystemUser)
│   │   │   ├── Dashboard.tsx    # لوحة التحكم
│   │   │   ├── Cameras.tsx      # قائمة الكاميرات
│   │   │   ├── SavedImages.tsx  # الصور المحفوظة (محمية - SystemUser only)
│   │   │   ├── Search.tsx       # البحث بالصورة
│   │   │   ├── ReportMissing.tsx # صفحة إنشاء بلاغ (عامة)
│   │   │   ├── TrackReport.tsx  # صفحة تتبع البلاغ (عامة)
│   │   │   ├── AdminReports.tsx # صفحة إدارة البلاغات (SystemUser only)
│   │   │   └── NotFound.tsx
│   │   ├── components/
│   │   │   ├── Layout.tsx       # Layout component مع navigation
│   │   │   ├── CameraCapture.tsx
│   │   │   └── ui/              # UI components (shadcn/ui)
│   │   ├── lib/
│   │   │   ├── api.ts           # API functions (جميع endpoints)
│   │   │   └── utils.ts
│   │   └── i18n/
│   │       ├── config.ts
│   │       └── locales/
│   │           ├── ar.json      # الترجمات العربية
│   │           └── en.json      # الترجمات الإنجليزية
│   └── package.json
│
├── docker-compose.yml            # Docker orchestration
├── .env.example                  # Environment variables template
├── ESP32_CAM_API_DOCUMENTATION.md # توثيق API للكاميرات
├── test_api.py                   # Test script شامل
└── README.md
```

## الصفحات والمسارات (Routes)

### صفحات عامة (Public - لا تحتاج authentication)
- `/login` - تسجيل الدخول (SystemUser)
- `/report` - إنشاء بلاغ عن طفل مفقود
- `/track` - تتبع حالة البلاغ

### صفحات محمية (Protected - تحتاج SystemUser authentication)
- `/` - لوحة التحكم (Dashboard)
- `/cameras` - قائمة الكاميرات
- `/saved-images` - الصور المحفوظة (SystemUser only)
- `/search` - البحث بالصورة
- `/admin/reports` - إدارة البلاغات (SystemUser only)

## API Endpoints

### Authentication
- `POST /api/auth/login` - تسجيل الدخول
- `GET /api/auth/me` - معلومات المستخدم الحالي
- `POST /api/auth/refresh` - تحديث token

### Public Endpoints (No Auth)
- `POST /api/reports/create` - إنشاء بلاغ
- `POST /api/reports/track` - تتبع البلاغ
- `POST /api/reports/{report_number}/close` - إغلاق البلاغ

### Protected Endpoints (SystemUser Only)
- `GET /api/saved_images` - الصور المحفوظة
- `GET /api/admin/reports` - قائمة البلاغات
- `GET /api/admin/reports/{report_id}` - تفاصيل بلاغ
- `PUT /api/admin/reports/{report_id}/status` - تحديث حالة البلاغ
- `GET /api/admin/reports/{report_id}/matches` - التطابقات

### Camera Endpoints
- `POST /api/upload_camera_face` - رفع صورة من الكاميرا (يتطلب X-API-KEY)

## Database Models

### User
- `id`, `username`, `email`, `hashed_password`, `is_active`, `is_system_user`, `created_at`

### Camera
- `id`, `code`, `name`, `first_seen_ts`, `last_seen_ts`, `total_images`

### CapturedImage
- `id`, `camera_id`, `camera_name`, `timestamp`, `file_path`, `compreface_face_id`
- `latitude`, `longitude`, `place_name`, `description` (جديدة)

### MissingReport
- `id`, `report_number` (REP-YYYY-XXXX), `reporter_name`, `reporter_email`, `reporter_phone`
- `child_name`, `child_photo_path`, `child_compreface_face_id`
- `status` (open, in_progress, resolved, closed)
- `created_at`, `updated_at`, `closed_at`, `created_by_user_id`

### ReportMatch
- `id`, `report_id`, `captured_image_id`, `similarity_score`
- `camera_id`, `camera_name`, `matched_at`, `notified_at`, `external_api_called`

## Workflow

### 1. إنشاء بلاغ
1. المستخدم يفتح `/report`
2. يملأ البيانات (الاسم، البريد، الهاتف، اسم الطفل)
3. يرفع صورة الطفل
4. النظام يتحقق من وجود وجه في الصورة
5. إذا وُجد وجه: يتم حفظ البلاغ وفهرسته في CompreFace
6. يتم إرجاع رقم البلاغ الفريد

### 2. رفع صورة من الكاميرا
1. ESP32-CAM يرفع صورة مع بيانات الموقع
2. النظام يفحص الصورة في الخلفية:
   - يتحقق من وجود وجه
   - إذا وُجد وجه: يحفظ الصورة ويفهرسها
   - يقارن الصورة مع البلاغات المفتوحة/قيد المعالجة
   - إذا كان التطابق > 88%: ينشئ ReportMatch ويستدعي External API

### 3. تتبع البلاغ
1. المستخدم يفتح `/track`
2. يدخل رقم الهاتف ورقم البلاغ
3. النظام يعرض حالة البلاغ والتطابقات (إن وجدت)
4. يمكن للمستخدم إغلاق البلاغ

### 4. إدارة البلاغات (SystemUser)
1. SystemUser يسجل الدخول في `/login`
2. يفتح `/admin/reports`
3. يستعرض جميع البلاغات مع filters
4. يمكنه تحديث حالة البلاغ وعرض التطابقات

## Environment Variables

راجع `.env.example` للحصول على قائمة كاملة بالمتغيرات المطلوبة.

## ملاحظات مهمة

1. **المصادقة**: SystemUser فقط يمكنه الوصول إلى `/saved-images` و `/admin/reports`
2. **البلاغات**: عامة - أي شخص يمكنه إنشاء بلاغ أو تتبعه
3. **المقارنة التلقائية**: تحدث في الخلفية عند رفع صورة من الكاميرا
4. **External API**: يتم استدعاؤه عند العثور على تطابق > 88%

